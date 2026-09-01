import json
import time
import urllib3
from datetime import datetime
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = datetime.now().strftime("%Y-%m-%d")

# Desativa os warnings de SSL para evitar mensagens de erro desnecessárias
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL da API
URL = "https://lojas.claro.com.br/arcgis/mapserver/ServiceArea_prd/MapServer/1/query"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/137.0.0.0 Mobile Safari/537.36"
}

def fetch_all_stores():
    """
    Coleta todos os registros de lojas da API usando paginação com 'SourceOID'.
    """
    # Usamos um conjunto (set) para evitar duplicatas automaticamente
    all_records_set = set()
    total_records_fetched = 0
    
    # Usamos o 'SourceOID' para a paginação. Ele garante que cada requisição
    # comece a partir do último registro da requisição anterior.
    last_oid = 0

    while True:
        # Parâmetros da requisição para a API
        params = {
            "f": "json",
            # A nova cláusula "where" garante que só busquemos registros com
            # 'SourceOID' maior que o último que coletamos.
            "where": f"SourceOID > {last_oid}",
            "returnGeometry": "false",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "COD_LOJA,NOME,ENDERECO,MUNICIPIO,UF,LATITUDE,LONGITUDE,TIPO,HORARIO,SERVICOS,"
                         "SourceOID,SEG_SEX,SABADO,DOMINGO,"
                         "com_LOJAS_CLARO_PRODUTOS,com_LOJAS_CLARO_AGENDAMENTO,com_LOJAS_CLARO_WHATSAPP,"
                         "com_LOJAS_CLARO_DELIVERY,com_LOJAS_CLARO_DRIVE_THRU,"
                         "com_LOJAS_CLARO_WHATSAPP_BUSINESS,com_LOJAS_CLARO_COMANDO,FromBreak",
            # Ordenamos por 'SourceOID' para que a paginação funcione corretamente
            "orderByFields": "SourceOID",
            "outSR": "102100",
        }

        try:
            # Faz a requisição HTTP GET
            resp = requests.get(URL, headers=HEADERS, params=params, verify=False)
            resp.raise_for_status()  # Lança um erro se a resposta não for 200
            data = resp.json()

            # Extrai a lista de features (lojas)
            features = data.get("features", [])
            
            # Se não houver mais features, a paginação terminou
            if not features:
                print("✅ Paginação completa. Não há mais registros.")
                break
            
            # Adiciona as lojas encontradas ao conjunto para remover duplicatas
            for f in features:
                # Dicionários não podem ser adicionados diretamente a um conjunto.
                # Convertemos para uma tupla de itens para que possa ser adicionado.
                all_records_set.add(tuple(f["attributes"].items()))
                total_records_fetched += 1
            
            # Atualiza o 'last_oid' para a próxima iteração. Pegamos o valor do
            # último registro na lista.
            last_oid = features[-1]["attributes"]["SourceOID"]
            
            print(f"🔎 Coletados {len(features)} registros. Próximo 'SourceOID' será > {last_oid}")

            # Pausa para evitar sobrecarga no servidor.
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            break
    
    # Converte o conjunto de volta para uma lista de dicionários
    final_records = [dict(record) for record in all_records_set]
    return final_records, total_records_fetched

if __name__ == "__main__":
    print("Iniciando a coleta de lojas...")
    
    start_time = datetime.now()
    
    records, total_fetched = fetch_all_stores()
    
    end_time = datetime.now()
    
    # Calcula o tempo total de execução
    total_time = end_time - start_time
    hours, remainder = divmod(total_time.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Calcula o número de duplicatas removidas
    duplicates_removed = total_fetched - len(records)
    
    print(f"✅ Coleta finalizada! Total de {len(records)} registros únicos.")
    print(f"🗑️ Foram removidos {duplicates_removed} registros duplicados.")
    print(f"⏱️ Tempo total: {int(hours)}h {int(minutes)}m {int(seconds)}s")
    
    # Salva todos os registros em um arquivo JSON dentro da pasta output
    file_path = OUTPUT_DIR / f"claro_Capilaridade_{EXTRACTION_DATE}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Arquivo salvo em: {file_path}")


