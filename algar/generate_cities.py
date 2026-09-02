import json
import requests
import urllib3
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = datetime.now().strftime("%Y-%m-%d")

def extrair_mapeamento_e_lojas():
    # Headers to mimic a real browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Sessão reutilizada para todas as requisições (mantém conexão e cookies)
    session = requests.Session()
    session.headers.update(headers)
    session.verify = False

    # --- PASSO 1: Pegar o mapeamento de cidades diretamente do HTML ---
    url_lojas = "https://loja.algar.com.br/lojas"
    print(f"\n[INFO] 🌐 Acessando {url_lojas} silenciosamente via requests...")

    try:
        response_html = session.get(url_lojas)
        response_html.raise_for_status()
    except Exception as e:
        print(f"[ERRO FATAL] ❌ Não foi possível acessar o site: {e}")
        return []

    print("[AÇÃO] 🔍 Buscando JSON de mapeamento no HTML usando BeautifulSoup...")
    soup = BeautifulSoup(response_html.text, 'html.parser')
    estado_select = soup.find(id="estado")
    
    if not estado_select or not estado_select.get("data-states-and-cities"):
        print("[ERRO FATAL] ❌ JSON de estados e cidades não encontrado no DOM. Abortando.")
        return []
        
    dados_raw = estado_select.get("data-states-and-cities")
    mapeamento = json.loads(dados_raw)
    
    total_estados = len(mapeamento.keys())
    total_cidades = sum(len(cidades) for cidades in mapeamento.values())
    print(f"[SUCESSO] ✅ Mapeamento carregado: {total_estados} estados e {total_cidades} cidades prontas.\n")
    print("-" * 60)

    # --- PASSO 2: Consultar a API para cada cidade mapeada ---
    url_api = "https://loja.algar.com.br/on/demandware.store/Sites-algartelecom-BR-Site/pt_BR/Stores-FindStores"
    resultados = []
    contador_atual = 1
    map_index = 0

    for estado, cidades in mapeamento.items():
        for cidade in cidades:
            print(f"[{contador_atual}/{total_cidades}] 📍 Consultando API para: {cidade} - {estado}")
            
            params = {
                "showMap": "false",
                "state": estado,
                "city": cidade
            }
            
            try:
                # Fazendo a requisição na API oculta em vez de clicar na UI
                api_response = session.get(url_api, params=params, headers=headers)
                
                if api_response.status_code == 200:
                    dados_api = api_response.json()
                    stores = dados_api.get("stores", [])
                    
                    if not stores:
                        print("  └─ ⚠️ Aviso: Retorno vazio para esta cidade pela API.")
                    else:
                        for store in stores:
                            # Formatação exata para bater com o que você precisa
                            postal_code = store.get("postalCode")
                            postal_code_str = str(postal_code) if postal_code else "null"
                            
                            address1 = store.get("address1", "")
                            city_str = store.get("city", "")
                            state_code = store.get("stateCode", "")
                            endereco_completo = f"{address1} {city_str}, {state_code} {postal_code_str}"

                            resultados.append({
                                "estado": state_code,
                                "cidade": city_str,
                                "endereco": endereco_completo,
                                "horario": store.get("storeHours", "N/A"),
                                "telefone": store.get("phone", "N/A"),
                                "link_maps": f"http://googleusercontent.com/maps.google.com/{map_index}"
                            })
                            map_index += 1
                        print(f"  └─ [SUCESSO] ✅ {len(stores)} loja(s) encontrada(s) e salva(s).")
                else:
                    print(f"  └─ [ERRO] ❌ Falha na API. Código HTTP: {api_response.status_code}")
                    
            except Exception as e:
                print(f"  └─ [ERRO CRÍTICO] ❌ Detalhes da falha: {e}")

            contador_atual += 1

    return resultados

if __name__ == "__main__":
    dados = extrair_mapeamento_e_lojas()
    print(f"\n[FINALIZADO] 🎉 Extração hiper-rápida concluída! Total de registros: {len(dados)}")
    
    if dados:
        nome_arquivo = OUTPUT_DIR / f"algar_Capilaridade_{EXTRACTION_DATE}.json"
        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as arquivo_json:
                json.dump(dados, arquivo_json, ensure_ascii=False, indent=4)
                
            print(f"[SUCESSO] 💾 Dados salvos no arquivo: {nome_arquivo}")
            
        except Exception as e:
            print(f"[ERRO] ❌ Falha ao tentar salvar o arquivo JSON: {e}")