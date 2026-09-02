# curl_cffi imita o fingerprint TLS/JA3 de um browser real. O WAF da GoCache
# do site da Unifique bloqueia (403 "Acesso Bloqueado") o handshake TLS padrao
# do requests/urllib3; com impersonate="chrome" a requisicao passa normalmente.
from curl_cffi import requests
import sys
import csv
import json  # <--- NEW: JSON export support
from bs4 import BeautifulSoup
import urllib3
import re
import unidecode
import pandas as pd
import hashlib # <--- NEW: Imported library for hashing logic
from pathlib import Path  # <--- FIX: paths ancorados no arquivo, nao no CWD
from datetime import datetime  # <--- NEW: data de extracao para o nome do output

# --- Desativar Avisos de SSL ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- FIX DE PATH ---
# Todos os caminhos passam a ser resolvidos a partir da pasta deste arquivo,
# nao da pasta de onde o script foi chamado. Assim funciona tanto rodando
# 'python unifique.py' dentro de /unifique quanto via run_all.py na raiz.
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / 'output'
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)  # cria output/ se nao existir
EXTRACTION_DATE = datetime.now().strftime("%Y-%m-%d")

# --- Configuração da Requisição ---
cookies = {
    '_gcl_au': '1.1.457361293.1762527157',
    '_fbp': 'fb.2.1762527156986.411001257407178764',
    '_ga': 'GA1.1.187858891.1762527157',
    'FPAU': '1.1.457361293.1762527157',
    'cookie-consent': '%7B%22necessarios%22%3Atrue%2C%22estatistica%22%3Atrue%2C%22personalizacao%22%3Atrue%2C%22publicidade%22%3Atrue%7D',
    '__trf.src': 'encoded_eyJmaXJzdF9zZXNzaW9uIjp7InZhbHVlIjoiKG5vbmUpIiwiZXh0cmFfcGFyYW1zIjp7fX0sImN1cnJlbnRfc2Vzc2lvbiI6eyJ2YWx1ZSI6Iihub25lKSIsImV4dHJhX3BhcmFtcyI6e319LCJjcmVhdGVkX2F0IjoxNzYyNTQwMTczODQ2fQ==',
    '_ga_DZB3E9W1TJ': 'GS2.1.s1762540076$o2$g1$t1762540173$j60$l0$h1477898148',
    'FPGSID': '1.1762540080.1762540175.G-DZB3E9W1TJ.rVXpAsztrBgdnXu0z2M2vQ',
    'PHPSESSID': '3cfc4c64fdb5844243f10d47099b68c9',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
}

url = 'https://unifique.com.br/atendimento/lojas'
output_csv_file = OUTPUT_DIR / f"unifique_Capilaridade_{EXTRACTION_DATE}.csv"
output_json_file = OUTPUT_DIR / f"unifique_Capilaridade_{EXTRACTION_DATE}.json"  # <--- NEW: JSON output path
excel_ibge_file = DATA_DIR / 'Base_BR_IBGE.xlsx'

re_pattern = re.compile(r'^(.*)\s*-\s*([a-zA-Z]{2})$')

print(f"Enviando requisição para: {url}")

try:
    response = requests.get(
        url, headers=headers, impersonate="chrome", verify=False, timeout=30
    )

    # ------------------------------------------------------------------
    # DIAGNÓSTICO DA RESPOSTA (antes do raise_for_status)
    # Objetivo: quando der 403, ver EXATAMENTE o que o servidor devolveu
    # em vez de só um traceback seco.
    # ------------------------------------------------------------------
    print("\n" + "-" * 60)
    print(f"[DIAG] Status HTTP        : {response.status_code} {response.reason}")
    print(f"[DIAG] URL final          : {response.url}")
    print(f"[DIAG] Redirecionamentos  : {[r.status_code for r in response.history]}")
    print(f"[DIAG] Tamanho do corpo   : {len(response.text)} bytes")
    for h in ("Server", "CF-RAY", "X-Cache", "X-GoCache-Status", "Set-Cookie",
              "Content-Type", "Retry-After", "X-Powered-By"):
        if h in response.headers:
            print(f"[DIAG] {h:<18}: {response.headers[h]}")

    corpo = response.text
    # So faz sentido procurar pagina de bloqueio quando a resposta NAO foi 200
    # (a pagina legitima de lojas tem 2 MB e cita "cloudflare" num script).
    if response.status_code != 200 or len(corpo) < 50_000:
        marcadores_waf = ("Acesso Bloqueado", "gocache", "captcha", "cloudflare",
                          "Attention Required", "Just a moment", "Access denied")
        hit = [m for m in marcadores_waf if m.lower() in corpo.lower()]
        if hit:
            print(f"[DIAG] ⚠️  PÁGINA DE WAF/BLOQUEIO detectada (marcadores: {hit})")
    print(f"[DIAG] Trecho do corpo    : {corpo[:400]!r}")
    print(f"[DIAG] Cookies recebidos  : {response.cookies.get_dict()}")
    print("-" * 60 + "\n", flush=True)

    response.raise_for_status()

    print(f"Requisição bem-sucedida (Status: {response.status_code})")

    # --- INÍCIO DO PARSING ---
    print("Analisando o conteúdo HTML...")
    soup = BeautifulSoup(response.text, 'html.parser')

    store_blocks = soup.find_all('div', class_='space-y-1.5')

    lojas_data = []
    enderecos_vistos = set()
    lojas_duplicadas = 0

    print(f"Encontrados {len(store_blocks)} blocos de loja. Iniciando extração...")

    for block in store_blocks:
        # 1. Cidade e Estado
        cidade_tag = block.find('h4')
        if not cidade_tag: continue
        cidade_estado = cidade_tag.get_text(strip=True)

        # 2. Atendida Por
        atendida_p = block.find('p', class_='text-accent-700')
        atendida_span = atendida_p.find('span') if atendida_p else None
        atendida_por = atendida_span.get_text(strip=True) if atendida_span else 'N/A'

        # 3. Endereço Completo
        endereco_tag = block.find('p', class_='text-accent-950')
        endereco_completo = endereco_tag.get_text(strip=True) if endereco_tag else 'N/A'

        # 4. Horário
        horario_tag = block.find('p', class_='text-accent-600')
        horario = horario_tag.get_text(strip=True) if horario_tag else 'N/A'

        # --- LÓGICA DE DUPLICADAS ---
        if endereco_completo == 'N/A': continue
        if endereco_completo in enderecos_vistos:
            lojas_duplicadas += 1
            continue

        enderecos_vistos.add(endereco_completo)

        # --- REGEX CIDADE/UF ---
        match = re_pattern.match(cidade_estado)
        if match:
            cidade = match.group(1).strip()
            uf = match.group(2).strip()
            cidade_norm = unidecode.unidecode(cidade).lower().strip()
            uf_norm = unidecode.unidecode(uf).lower().strip()
            chave_cidade_uf = f"{cidade_norm}_{uf_norm}"
        else:
            cidade = cidade_estado
            uf = 'N/A'
            chave_cidade_uf = 'N/A'

        # ---------------------------------------------------------
        # ### NEW: HASH ID GENERATION STRATEGY
        # ---------------------------------------------------------

        # 1. Create the Unique String (Fingerprint)
        # using City + UF + Address to guarantee uniqueness per location
        raw_id_string = f"{cidade}-{uf}-{endereco_completo}"

        # 2. Apply MD5 Hash
        hash_object = hashlib.md5(raw_id_string.encode('utf-8'))

        # 3. Format: Get Hex, Slice first 8 chars, Upper Case
        unique_id = hash_object.hexdigest()[:8].upper()

        # ---------------------------------------------------------

        # Adiciona os dados (incluindo o ID novo)
        lojas_data.append({
            'ID': unique_id,  # <--- Added here
            'Cidade': cidade,
            'UF': uf,
            'cidade_uf': chave_cidade_uf,
            'Atendida_Por': atendida_por,
            'Endereco_Completo': endereco_completo,
            'Horario': horario
        })

    print(f"Extração concluída. {len(lojas_data)} lojas únicas adicionadas.")

    # --- MERGE COM IBGE (Mantido igual) ---
    print("\nIniciando etapa de enriquecimento com dados do IBGE...")

    try:
        df_ibge = pd.read_excel(excel_ibge_file, usecols=['uf_cidade', 'COD IBGE'], dtype=str)
        df_ibge = df_ibge.rename(columns={'uf_cidade': 'cidade_uf'})
        df_ibge = df_ibge.drop_duplicates(subset=['cidade_uf'])

        df_lojas = pd.DataFrame(lojas_data)

        print("Executando merge...")
        df_final = pd.merge(df_lojas, df_ibge, on='cidade_uf', how='left')

        # Tratamento de N/A
        df_final.loc[(df_final['COD IBGE'].isna()) & (df_final['cidade_uf'] != 'N/A'), 'COD IBGE'] = 'N/A'
        df_final['COD IBGE'] = df_final['COD IBGE'].fillna('')

    except Exception as e:
        print(f"Aviso: Não foi possível ler IBGE ({e}). Gerando CSV sem ele.")
        df_final = pd.DataFrame(lojas_data)
        if 'COD IBGE' not in df_final.columns:
            df_final['COD IBGE'] = 'N/A'

    # --- EXPORTAÇÃO FINAL ---
    if not df_final.empty:
        # ### NEW: Updated Headers to include 'ID' at the start
        headers = ['ID', 'Cidade', 'UF', 'cidade_uf', 'COD IBGE', 'Atendida_Por', 'Endereco_Completo', 'Horario']

        # Reorder columns safely
        # (Only select columns that actually exist in the dataframe to avoid errors)
        existing_headers = [col for col in headers if col in df_final.columns]
        df_final = df_final[existing_headers]

        print(f"Salvando dados em '{output_csv_file}'...")
        df_final.to_csv(output_csv_file, sep=';', index=False, encoding='utf-8-sig')
        print("Sucesso.")

        # ---------------------------------------------------------
        # ### NEW: JSON EXPORT (mesma fonte de dados do CSV)
        # Não altera a lógica existente: apenas serializa uma cópia
        # defensiva do df_final já ordenado/enriquecido.
        # ---------------------------------------------------------
        try:
            print(f"Salvando dados em '{output_json_file}'...")

            # 1. Cópia defensiva + normalização de tipos
            #    (evita NaN/np.nan virarem literais inválidos no JSON)
            df_json = df_final.copy()
            df_json = df_json.fillna('')
            df_json = df_json.astype(str)

            # 2. Lista de dicts preservando a ORDEM das colunas do CSV
            registros = df_json.to_dict(orient='records')

            # 3. Envelope com metadados (útil para pipelines/ETL downstream)
            payload = {
                'fonte': url,
                'total_lojas': len(registros),
                'campos': existing_headers,
                'lojas': registros
            }

            with open(output_json_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            print("Sucesso (JSON).")

        except Exception as e:
            # Falha no JSON NUNCA derruba o CSV já gerado
            print(f"Aviso: Falha ao gerar o JSON ({e}). O CSV foi gerado normalmente.")

except Exception as e:
    print(f"Erro Crítico: {e}")
    import traceback
    traceback.print_exc()
    # FIX: sair com codigo != 0 para o run_all.py detectar a falha
    # (antes o script morria com exit code 0 e o orquestrador dizia "sucesso")
    sys.exit(1)
