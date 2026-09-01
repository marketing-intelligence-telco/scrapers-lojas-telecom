import json
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = datetime.now().strftime("%Y-%m-%d")

def parse_address_claro(address_string):
    """
    Parsa uma string de endereço da Claro (formato típico: RUA, NÚMERO, COMPLEMENTO, BAIRRO)
    e a divide em rua (com número) e complemento.
    
    Args:
        address_string (str): A string do ENDERECO (Rua e Complemento).
        
    Returns:
        dict: Um dicionário com as partes do endereço (endereco, complemento).
    """
    parsed_address = {
        "endereco": "", 
        "complemento": ""
    }

    if not address_string:
        return parsed_address

    # Divide a string por vírgulas e remove espaços.
    parts = [p.strip() for p in address_string.split(',')]
    
    rua_e_numero = []
    restante = []

    # O padrão Claro é frequentemente: Rua (0), Número (1), Complemento (2), Bairro (3)
    # Tenta identificar Rua e Número, assumindo que o número é a segunda parte (índice 1).
    if len(parts) >= 2 and re.search(r'\d+', parts[1]):
        # Se a primeira parte é a rua e a segunda é o número, unimos.
        rua_e_numero.append(parts[0].title()) # Rua (title case)
        rua_e_numero.append(parts[1])         # Número
        
        # O restante (a partir do índice 2) é o complemento, filtrando partes vazias ou '0's.
        restante = [p.title() for p in parts[2:] if p.strip() and p.strip() != '0']
    else:
        # Caso o formato não siga o padrão esperado (sem número claro na segunda parte),
        # simplifica usando a primeira parte como rua e o resto como complemento.
        rua_e_numero.append(parts[0].title())
        restante = [p.title() for p in parts[1:] if p.strip() and p.strip() != '0']

    parsed_address["endereco"] = ", ".join(rua_e_numero).strip()
    parsed_address["complemento"] = ", ".join(restante).strip().replace(" , ", ", ")
    
    # Limpeza final do complemento
    parsed_address["complemento"] = parsed_address["complemento"].strip().rstrip(',').replace(" - , ", " - ")
    
    return parsed_address

def process_claro_data(file_path, output_path):
    """
    Lê o arquivo JSON da Claro, processa cada loja, adiciona a lógica de lojasProprias
    e remove duplicatas pela idLoja, **incluindo apenas as chaves existentes ou mapeadas**.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            claro_data = json.load(f)

        processed_data_map = {} # Dicionário para armazenar lojas únicas pela idLoja
        data_atual = datetime.now().strftime("%d/%m/%Y")

        # ATUALIZAÇÃO 1: Removendo chaves que não existem no JSON da Claro
        # (lojaConceito, lojasParticipantesSmartofertas)
        final_keys = [
            "idLoja", "operadora", "nomeSite", "latitude", "longitude",
            "lojasProprias", "endereco", "complemento", "cidade", "estado",
            "horario", "dataReferencia"
        ]
        
        # Mapeamento de chaves Claro para o formato final
        key_mapping = {
            "COD_LOJA": "idLoja",
            "NOME": "nomeSite",
            "MUNICIPIO": "cidade",
            "UF": "estado",
            "LATITUDE": "latitude",
            "LONGITUDE": "longitude"
        }

        for store in claro_data:
            new_store = {}
            
            # 1. Mapeamento de chaves simples e obtenção do idLoja
            for claro_key, final_key in key_mapping.items():
                new_store[final_key] = store.get(claro_key)
            
            id_loja = new_store.get("idLoja")
            if not id_loja:
                continue

            # 2. Lógica de lojasProprias e eliminação de duplicatas
            if id_loja in processed_data_map:
                continue
            
            # Define lojasProprias com base no TIPO
            tipo = store.get("TIPO")
            if tipo == 1:
                new_store["lojasProprias"] = "sim"
            else:
                new_store["lojasProprias"] = "não"

            # 3. Processamento do endereço
            address_string = store.get("ENDERECO", "")
            if address_string:
                parsed_address = parse_address_claro(address_string)
                new_store.update(parsed_address)
            
            # 4. Processamento dos horários (mantendo apenas SEG_SEX)
            new_store["horario"] = store.get("SEG_SEX", "Não Informado")

            # 5. Adiciona a operadora e a data de referência
            new_store["operadora"] = "Claro"
            new_store["dataReferencia"] = data_atual

            # 6. Formatação de latitude e longitude: converter para string e usar vírgula.
            for coord in ["latitude", "longitude"]:
                value = new_store.get(coord)
                if isinstance(value, (float, int)):
                    # Formata para string com até 8 casas decimais, usando vírgula como separador.
                    new_store[coord] = f"{value:.8f}".replace('.', ',').rstrip('0').rstrip(',')
                elif isinstance(value, str):
                    new_store[coord] = value.replace('.', ',')
            
            # ATUALIZAÇÃO 2: Removido o preenchimento fixo para 'lojaConceito' e 'lojasParticipantesSmartofertas'
            # Agora, se essas chaves não vierem do mapeamento ou processamento, elas não existirão em new_store.
            
            # 7. Reordena e filtra as chaves para o formato final
            # A filtragem (if k in new_store) garante que apenas as chaves existentes em 'new_store'
            # e listadas em 'final_keys' (já atualizada) sejam mantidas.
            ordered_store = {k: new_store.get(k) for k in final_keys if k in new_store}
            
            # Adiciona a loja processada ao mapa de lojas únicas
            processed_data_map[id_loja] = ordered_store

        processed_data = list(processed_data_map.values())
        
        # Salva o resultado
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=4, ensure_ascii=False)

        print(f"Total de {len(claro_data)} registros lidos.")
        print(f"Total de {len(processed_data)} registros únicos processados e salvos em {output_path}")

    except FileNotFoundError:
        # ... (restante do tratamento de erros)
        print(f"Erro: Arquivo '{file_path}' não encontrado.")
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{file_path}' não é um JSON válido.")
    except Exception as e:
        print(f"Um erro inesperado ocorreu: {e}")

if __name__ == "__main__":
    input_file = OUTPUT_DIR / f"claro_Capilaridade_{EXTRACTION_DATE}.json"
    output_file = OUTPUT_DIR / f"claro_Capilaridade_{EXTRACTION_DATE}.json"
    process_claro_data(input_file, output_file)