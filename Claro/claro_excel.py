import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = __import__('datetime').datetime.now().strftime("%Y-%m-%d")

def json_to_excel(input_json_path, output_excel_path):
    """
    Lê um arquivo JSON contendo uma lista de objetos (lojas) e o converte
    para um arquivo Excel (.xlsx).
    
    Args:
        input_json_path (str): Caminho para o arquivo JSON de entrada.
        output_excel_path (str): Caminho para o arquivo Excel de saída.
    """
    try:
        # 1. Leitura do arquivo JSON
        # O pandas pode ler JSON diretamente para um DataFrame
        df = pd.read_json(input_json_path)
        
        # 2. Exportação para Excel
        # Corrigido: Removido o argumento 'encoding', que causa o erro.
        df.to_excel(output_excel_path, index=False)
        
        print(f"Sucesso: O arquivo Excel foi gerado em: {output_excel_path}")
        print(f"Total de {len(df)} registros exportados.")

    except FileNotFoundError:
        print(f"Erro: O arquivo de entrada '{input_json_path}' não foi encontrado.")
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{input_json_path}' não é um JSON válido.")
    except Exception as e:
        print(f"Um erro inesperado ocorreu durante a conversão: {e}")

if __name__ == "__main__":
    input_file = OUTPUT_DIR / f"claro_Capilaridade_{EXTRACTION_DATE}.json"
    output_file = OUTPUT_DIR / f"claro_Capilaridade_{EXTRACTION_DATE}.xlsx"

    # Executa a função de conversão
    json_to_excel(input_file, output_file)