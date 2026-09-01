import json
import time
from datetime import datetime
from pathlib import Path

import requests
import urllib3

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = datetime.now().strftime("%Y-%m-%d")

# Desativa os warnings de SSL para evitar mensagens de erro desnecessárias
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_all_tim_stores():
    base_url = "https://tim.img.com.br/server/rest/services/Lojas/MapServer/0/query"
    
    # Parâmetros para a query
    params = {
        'f': 'json',
        'where': '1=1',
        'returnGeometry': 'true',
        'outFields': 'IDPARCEIRO,NOME_LOJA,ENDERECO,BAIRRO,CIDADE,ESTADO,UF,CEP,HORARIO_AT,TIPO_LOJA,SEGMENTO,ACESSIBILIDADE',
        'resultRecordCount': 2000,  # Máximo permitido por requisição
        'resultOffset': 0
    }
    
    all_stores = []
    total_count = 0
    offset = 0
    
    print("Buscando dados das lojas TIM...")
    
    while True:
        try:
            # Atualiza o offset para paginação
            params['resultOffset'] = offset
            
            # Faz a requisição
            response = requests.get(base_url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            # Verifica se há "features" na resposta
            if 'features' not in data:
                print("Nenhuma 'feature' encontrada na resposta.")
                break
                
            stores = data['features']
            
            if not stores:
                print("Nenhuma loja adicional encontrada.")
                break
                
            # Extrai e combina as informações das lojas
            for store in stores:
                attributes = store.get('attributes', {})
                geometry = store.get('geometry', {})
                
                # Combina os atributos e a geometria em um único objeto
                flattened_store_data = {**attributes, **geometry}
                all_stores.append(flattened_store_data)
            
            current_batch_count = len(stores)
            total_count += current_batch_count
            offset += current_batch_count
            
            print(f"Lojas buscadas nesta rodada: {current_batch_count}. Total até agora: {total_count}")
            
            # Se a quantidade de lojas for menor que o máximo solicitado,
            # chegamos ao final da lista
            if current_batch_count < params['resultRecordCount']:
                break
                
            # Adiciona um pequeno atraso para ser respeitoso com o servidor
            time.sleep(0.5)
                
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar dados: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"Erro ao analisar a resposta JSON: {e}")
            break
        except Exception as e:
            print(f"Erro inesperado: {e}")
            break
    
    return all_stores, total_count

def save_to_json(data, filename):
    """Salva os dados em um arquivo JSON"""
    try:
        path = Path(filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Dados salvos com sucesso em {path}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")

def main():
    # Busca todas as lojas
    all_stores, total_count = fetch_all_tim_stores()
    
    if all_stores:
        filename = OUTPUT_DIR / f'tim_Capilaridade_{EXTRACTION_DATE}.json'
        save_to_json(all_stores, filename)

        print(f"\nTotal de {total_count} lojas TIM buscadas com sucesso.")
        print(f"Dados salvos em: {filename}")
        
        # Mostra uma amostra dos dados
        if total_count > 0:
            print("\nAmostra dos dados da primeira loja:")
            sample_store = all_stores[0]
            for key, value in sample_store.items():
                if value:  # Exibe apenas campos não vazios
                    print(f"  {key}: {value}")
                    
    else:
        print("Nenhuma loja foi encontrada.")

if __name__ == "__main__":
    main()
