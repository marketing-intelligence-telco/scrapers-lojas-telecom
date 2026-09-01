# -*- coding: utf-8 -*-
"""
VIVO STORE SCRAPER — V4 "Varredura Nacional Autocalibrada por Raio"
===================================================================
Baseado no comportamento REAL da API (confirmado via diagnóstico):

  • /stores/by-radius aceita o parâmetro `radius` (em km).
  • Devolve as lojas dentro desse raio, ORDENADAS da mais perto p/ mais longe,
    com um TETO RÍGIDO de 200 resultados por consulta.
  • Cada loja vem com `haversineDistance` (distância ao ponto consultado).

ESTRATÉGIA (completude demonstrável):
  Cobrimos o Brasil com uma grade de quadrados. Cada quadrado é consultado
  UMA vez, com um raio grande o suficiente para cobrir o quadrado inteiro.
    - Se a consulta volta com MENOS de 200 lojas  -> vimos TUDO dentro do
      quadrado (inclusive uma loja nova). Quadrado COMPLETO.
    - Se volta com 200 (teto) -> está truncado. Dividimos o quadrado em 4 e
      repetimos, recursivamente, até cada pedaço voltar com < 200.
  Como os quadrados ladrilham o país inteiro e todo quadrado acaba enumerado
  por completo, NENHUMA loja pode escapar. Áreas vazias (oceano/sertão) se
  resolvem numa única consulta barata; só as regiões densas (SP, RJ...) são
  drilladas a fundo. Sem lista fixa de cidades e sem depender de arquivo do IBGE.

Requisitos: Python 3.9+  e  `pip install httpx`
"""

import asyncio
import json
import math
import time
from collections import deque
from pathlib import Path

import httpx
import urllib3

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = __import__('datetime').datetime.now().strftime("%Y-%m-%d")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
# CONFIGURAÇÃO
# ============================================================
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://plataforma.portal.vivo.com.br',
    'Referer': 'https://plataforma.portal.vivo.com.br/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'x-api-key': '70c463d9-3b1b-4850-9f7c-a978bf41ce34',
}
STORE_URL = 'https://orion.vivoportal.com.br/stores/by-radius'
OUTPUT_FILENAME = OUTPUT_DIR / f'vivo_Capilaridade_{EXTRACTION_DATE}.json'

# Caixa que envolve o Brasil continental (lat_min, lat_max, lon_min, lon_max)
BRASIL_BBOX = (-34.0, 5.5, -74.2, -34.0)

CAP            = 200     # teto de resultados por consulta (confirmado no diagnóstico)
PASSO_INICIAL  = 1.0     # grau; célula de 1° => raio ~77 km (< 100, dentro do testado)
PASSO_MINIMO   = 0.02    # grau (~2,2 km); piso de segurança contra recursão infinita
RAIO_SEGURANCA = 1.03    # margem no raio para garantir cobertura do canto da célula

BATCH_SIZE        = 150
PAUSA_ENTRE_LOTES = 0.3
TIMEOUT           = 20.0
MAX_RETRIES       = 3
MAX_CONSULTAS     = 60000   # disjuntor global (não deve ser alcançado na prática)


# ============================================================
# GEOMETRIA
# ============================================================
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def centro(cel):
    la0, la1, lo0, lo1 = cel
    return (la0 + la1) / 2.0, (lo0 + lo1) / 2.0


def raio_da_celula_km(cel):
    """Raio que cobre o canto mais distante do quadrado (centro -> canto)."""
    la0, la1, lo0, lo1 = cel
    clat, clon = centro(cel)
    return haversine_km(clat, clon, la1, lo1) * RAIO_SEGURANCA


def dividir(cel):
    la0, la1, lo0, lo1 = cel
    mla, mlo = (la0 + la1) / 2.0, (lo0 + lo1) / 2.0
    return [
        (la0, mla, lo0, mlo), (la0, mla, mlo, lo1),
        (mla, la1, lo0, mlo), (mla, la1, mlo, lo1),
    ]


def grade_inicial(bbox, passo):
    la0, la1, lo0, lo1 = bbox
    cels = []
    n_la = math.ceil((la1 - la0) / passo)
    n_lo = math.ceil((lo1 - lo0) / passo)
    for i in range(n_la):
        for j in range(n_lo):
            cels.append((
                la0 + i * passo, min(la0 + (i + 1) * passo, la1),
                lo0 + j * passo, min(lo0 + (j + 1) * passo, lo1),
            ))
    return cels


def formatar_tempo(seg):
    h, r = divmod(int(seg), 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def merge_stores(stores, db):
    novas = 0
    for s in stores:
        sid = s.get('storeId')
        if sid and sid not in db:
            db[sid] = s
            novas += 1
    return novas


# ============================================================
# REQUISIÇÃO RESILIENTE (com raio explícito)
# ============================================================
async def fetch_radius(client, lat, lon, raio_km):
    params = {
        'fromLatitude': f"{lat:.6f}",
        'fromLongitude': f"{lon:.6f}",
        'radius': str(int(math.ceil(raio_km))),
    }
    for tentativa in range(MAX_RETRIES):
        try:
            r = await client.get(STORE_URL, params=params)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                await asyncio.sleep(1.5 * (tentativa + 1))
            else:
                await asyncio.sleep(0.4 * (tentativa + 1))
        except Exception:
            await asyncio.sleep(0.5 * (tentativa + 1))
    return None


# ============================================================
# MOTOR PRINCIPAL — quadtree por saturação
# ============================================================
async def main():
    t_ini = time.time()
    print("=" * 66)
    print("🚀 VIVO SCRAPER V4 — Varredura Nacional Autocalibrada por Raio")
    print(f"   Teto/consulta: {CAP} | célula inicial: {PASSO_INICIAL}° | "
          f"piso: {PASSO_MINIMO}°")
    print("=" * 66)

    fila = deque(grade_inicial(BRASIL_BBOX, PASSO_INICIAL))
    print(f"Grade inicial: {len(fila)} células de {PASSO_INICIAL}° cobrindo o Brasil.\n")

    lojas, falhas = {}, []
    n_consultas, max_visto, lote = 0, 0, 0
    estourou = False

    limits = httpx.Limits(max_keepalive_connections=30, max_connections=60)
    async with httpx.AsyncClient(headers=HEADERS, limits=limits,
                                 timeout=TIMEOUT, verify=False) as client:
        while fila:
            lote += 1
            batch = [fila.popleft() for _ in range(min(BATCH_SIZE, len(fila)))]
            centros = [centro(c) for c in batch]
            raios = [raio_da_celula_km(c) for c in batch]

            t0 = time.time()
            res = await asyncio.gather(
                *[fetch_radius(client, ct[0], ct[1], rd)
                  for ct, rd in zip(centros, raios)]
            )

            novas, saturados, vazios = 0, 0, 0
            for cel, ct, rd, stores in zip(batch, centros, raios, res):
                n_consultas += 1
                if stores is None:
                    falhas.append((ct[0], ct[1], rd))
                    continue
                if not stores:
                    vazios += 1
                if len(stores) > max_visto:
                    max_visto = len(stores)
                novas += merge_stores(stores, lojas)

                lado = cel[1] - cel[0]
                if len(stores) >= CAP and lado > PASSO_MINIMO and not estourou:
                    for sub in dividir(cel):
                        fila.append(sub)
                    saturados += 1

            if n_consultas >= MAX_CONSULTAS and not estourou:
                estourou = True
                print(f"  [!] Disjuntor de {MAX_CONSULTAS} consultas atingido; "
                      f"drenando a fila sem subdividir mais.")

            print(f"[LOTE {lote:04d}] {time.time()-t0:4.1f}s | cels {len(batch):3d} | "
                  f"+{novas:3d} novas | {saturados:2d} saturados↘ | {vazios:3d} vazias | "
                  f"fila {len(fila):5d} | DB {len(lojas)}")
            await asyncio.sleep(PAUSA_ENTRE_LOTES)

        # ---------- REPESCAGEM ----------
        if falhas:
            unicas = list({(round(la, 5), round(lo, 5), round(rd, 1)) for la, lo, rd in falhas})
            print(f"\n--- REPESCAGEM: re-tentando {len(unicas)} consultas que falharam ---")
            for i in range(0, len(unicas), BATCH_SIZE):
                bloco = unicas[i:i + BATCH_SIZE]
                t0 = time.time()
                res = await asyncio.gather(
                    *[fetch_radius(client, la, lo, rd) for la, lo, rd in bloco]
                )
                novas = 0
                for stores in res:
                    if stores:
                        novas += merge_stores(stores, lojas)
                print(f"[REPESCAGEM {(i//BATCH_SIZE)+1:03d}] {time.time()-t0:4.1f}s | "
                      f"+{novas} | DB {len(lojas)}")
                await asyncio.sleep(PAUSA_ENTRE_LOTES)

    # ---------- SALVAR (schema idêntico ao original) ----------
    print("\n" + "=" * 66)
    print("💾 SALVANDO E FORMATANDO DADOS...")
    dados = []
    for store in lojas.values():
        dados.append({
            "idLoja": store.get("storeId", ""),
            "nomeSite": store.get("siteName", ""),
            "endereco": store.get("address", ""),
            "latitude": str(store.get("latitude")).replace(".", ",") if store.get("latitude") else "",
            "longitude": str(store.get("longitude")).replace(".", ",") if store.get("longitude") else "",
            "placeid": store.get("placeId", ""),
            "servicostelecomatend": store.get("telecomAttendanceServices", ""),
            "lojaConceito": "sim" if store.get("conceptStore") else "não",
            "whatsapp": store.get("whatsApp", ""),
            "lojaPadrao": "sim" if store.get("defaultStore") else "não",
            "lojasParticipantesSmartofertas": "sim" if store.get("smartOffersParticipant") else "não",
            "lojasProprias": "sim" if store.get("ownStore") else "não",
        })

    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    print("=" * 66)
    print("✅ EXTRAÇÃO FINALIZADA!")
    print(f"📊 Lojas únicas:            {len(lojas)}")
    print(f"🔎 Consultas feitas:        {n_consultas}")
    print(f"📈 Máx. lojas numa consulta:{max_visto:>4d}   (se ficou em {CAP}, "
          f"o teto é {CAP} mesmo; se passou de {CAP}, ajuste o CAP!)")
    print(f"📁 Arquivo:                 {OUTPUT_FILENAME}")
    print(f"⏱️ Tempo total:             {formatar_tempo(time.time() - t_ini)}")
    print("=" * 66)


if __name__ == "__main__":
    asyncio.run(main())
