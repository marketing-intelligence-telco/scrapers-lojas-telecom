import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = __import__('datetime').datetime.now().strftime("%Y-%m-%d")

def generate_excel_from_json(json_file, excel_file):
    """
    Lê um arquivo JSON e o converte para um arquivo Excel.

    Args:
        json_file (str): O caminho para o arquivo JSON de entrada.
        excel_file (str): O nome do arquivo Excel de saída.
    """
    try:
        # Verifica se o arquivo JSON existe
        if not Path(json_file).exists():
            print(f"Erro: O arquivo JSON '{json_file}' não foi encontrado.")
            return

        # 1. Carregar os dados do arquivo JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 2. Criar um DataFrame do pandas a partir dos dados JSON
        # O pandas lida automaticamente com a estrutura da lista de dicionários
        df = pd.DataFrame(data)

        # 3. Salvar o DataFrame em um arquivo Excel
        df.to_excel(excel_file, index=False)  # index=False evita salvar o índice do DataFrame como uma coluna

        print(f"Arquivo Excel '{excel_file}' gerado com sucesso!")

    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{json_file}' tem um formato JSON inválido.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    json_input = OUTPUT_DIR / f"vivo_Capilaridade_{EXTRACTION_DATE}.json"
    excel_output = OUTPUT_DIR / f"vivo_Capilaridade_{EXTRACTION_DATE}.xlsx"

    generate_excel_from_json(json_input, excel_output)
    print(f"Arquivo Excel salvo em {excel_output}")