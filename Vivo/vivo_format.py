import json
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = datetime.now().strftime("%Y-%m-%d")

def parse_address_simplified(address_string):
    """
    Parsa uma string de endereço e a divide em componentes essenciais.
    
    Args:
        address_string (str): A string do endereço.
        
    Returns:
        dict: Um dicionário com as partes do endereço (rua, complemento, cidade, estado).
    """
    parsed_address = {
        "rua": "", # Será usado para o novo 'endereco' (Rua e Número)
        "complemento": "",
        "cidade": "",
        "estado": ""
    }
    
    # 1. Padrão para separar Bairro/Cidade/Estado
    # Exemplo: "... - Centro, Diadema - SP"
    match_state_city = re.search(r'([\w\sçãéíúó]+) - ([A-Z]{2})$', address_string, re.IGNORECASE)
    if match_state_city:
        parsed_address["cidade"] = match_state_city.group(1).strip().title()
        parsed_address["estado"] = match_state_city.group(2).strip().upper()
        address_string = address_string[:match_state_city.start()].strip()
    
    # 2. Extrair o bairro e o resto da string para o complemento
    # Exemplo: "... - Shopping SP Market - Térreo - Vila Almeida"
    match_bairro_and_rest = re.search(r'- ([\w\sçãéíúó\-]+)$', address_string, re.IGNORECASE)
    if match_bairro_and_rest:
        # Pega a parte restante antes do bairro para o complemento
        complement_part = address_string[:match_bairro_and_rest.start()].strip()
        
        # O bairro é a última parte, que queremos manter no complemento neste novo formato
        bairro_part = match_bairro_and_rest.group(0).strip()
        
        # Junta a parte de complemento extraída antes do bairro + o bairro
        parsed_address["complemento"] = complement_part.strip().rstrip(',') + " " + bairro_part.strip()
        
        # A string restante é apenas a Rua e Número
        address_string = address_string[:match_bairro_and_rest.start()].strip().rstrip('-').rstrip(',')
        
    # 3. O restante da string é a Rua + Número.
    parts = [p.strip() for p in address_string.split(',')]
    
    if len(parts) >= 2 and re.search(r'\d+', parts[1]):
        # Se a primeira parte for a rua e a segunda for o número, unimos.
        # Ex: ["Avenida Interlagos", "2225", "LOJA 128 / 128A PARTE"]
        parsed_address["rua"] = f"{parts[0].title()}, {parts[1]}"
        
        # O resto vai para o complemento
        rest_complement = [p.strip() for p in parts[2:] if p.strip()]
        if rest_complement:
             # Adiciona as partes de complemento que sobraram (Ex: "LOJA 128 / 128A PARTE")
            current_complement = ", ".join(rest_complement)
            if parsed_address["complemento"]:
                parsed_address["complemento"] = current_complement + " - " + parsed_address["complemento"]
            else:
                parsed_address["complemento"] = current_complement
                
    else:
        # Caso não haja número claro (ou outro formato), mantém a lógica anterior simplificada.
        parsed_address["rua"] = parts[0].title()
        if len(parts) > 1:
            rest_complement = [p.strip() for p in parts[1:] if p.strip()]
            if rest_complement:
                current_complement = ", ".join(rest_complement)
                if parsed_address["complemento"]:
                    parsed_address["complemento"] = current_complement + " - " + parsed_address["complemento"]
                else:
                    parsed_address["complemento"] = current_complement

    # Limpeza final do complemento
    parsed_address["complemento"] = parsed_address["complemento"].strip().rstrip(',').replace(" - , ", " - ")
    # Padroniza "LOJ" e "LOJ A" para "Loja"
    parsed_address["complemento"] = re.sub(r'\bLOJ\s*A?\b', 'Loja', parsed_address["complemento"], flags=re.IGNORECASE)
    
    # CORREÇÃO ANTERIOR: Remove hífen inicial se ele for o primeiro caractere após limpeza e espaços.
    if parsed_address["complemento"].startswith('-'):
        parsed_address["complemento"] = parsed_address["complemento"].lstrip('-').strip()
    
    return parsed_address

def process_vivo_data_final(file_path, output_path):
    """
    Lê o arquivo JSON da Vivo, processa cada loja, adiciona a operadora, 
    renomeia a data e salva o resultado.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            vivo_data = json.load(f)
            
        processed_data = []
        data_atual = datetime.now().strftime("%d/%m/%Y")
        
        # Chaves que serão mantidas no formato final, em ordem
        final_keys = [
            "idLoja", "operadora", "nomeSite", "latitude", "longitude", "lojaConceito", 
            "lojasParticipantesSmartofertas", "lojasProprias", "endereco", 
            "complemento", "cidade", "estado", "horario", "dataReferencia"
        ]

        for store in vivo_data:
            # 1. Processamento do endereço
            address_string = store.get("endereco", "")
            if address_string:
                parsed_address = parse_address_simplified(address_string)
                store.update(parsed_address)
                # Remove a chave 'endereco' original (que contém a string completa)
                store.pop('endereco', None)

            # 2. Processamento dos horários
            horario_base = store.get("abreSegundaFeira")
            horario_keys = [
                "abreFeriado", "abreDomingo", "abreSegundaFeira", "abreTercaFeira",
                "abreQuartaFeira", "abreQuintaFeira", "abreSextaFeira", "abreSabado"
            ]
            for key in horario_keys:
                store.pop(key, None)
            if horario_base:
                store["horario"] = horario_base

            # 3. Adiciona a operadora e Renomeia a data de extração
            store["operadora"] = "Vivo"
            store["dataReferencia"] = data_atual # Renomeia dataExtracao para dataReferencia
            
            # 4. Formatação de latitude e longitude (NOVA IMPLEMENTAÇÃO)
            for coord in ["latitude", "longitude"]:
                if coord in store and isinstance(store[coord], str):
                    # Substitui o ponto decimal por vírgula
                    store[coord] = store[coord].replace('.', ',')

            # 5. Remove chaves não desejadas
            keys_to_remove = [
                'placeid', 'servicostelecomatend', 'whatsapp', 'sim', 'haversineDistance'
            ]
            for key in keys_to_remove:
                store.pop(key, None)

            # 6. Renomeia 'rua' para 'endereco'
            if 'rua' in store:
                store['endereco'] = store.pop('rua')

            # 7. Reordena e filtra as chaves para o formato final
            ordered_store = {k: store.get(k) for k in final_keys if k in store or k == "operadora"}
            
            processed_data.append(ordered_store)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=4, ensure_ascii=False)
            
        print(f"Dados processados salvos em {output_path}")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{file_path}' não encontrado.")
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{file_path}' não é um JSON válido.")
    except Exception as e:
        print(f"Um erro inesperado ocorreu: {e}")

if __name__ == "__main__":
    input_file = OUTPUT_DIR / f"vivo_Capilaridade_{EXTRACTION_DATE}.json"
    output_file = OUTPUT_DIR / f"vivo_Capilaridade_{EXTRACTION_DATE}.json"
    process_vivo_data_final(input_file, output_file)