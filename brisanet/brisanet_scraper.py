import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests


MAP_ID = "1rmfAe5YTRjsPeN9tnkZJzsj3fNGC7QI"
MAP_URL = f"https://www.google.com/maps/d/u/0/viewer?mid={MAP_ID}&femb=1"
BASELINE_RECORDS = 337
MINIMUM_EXPECTED_RECORDS = BASELINE_RECORDS // 2
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"}
ROOT_DIR = Path(__file__).resolve().parent
EXTRACTION_DATE = datetime.now().strftime("%Y-%m-%d")
OUTPUT_CSV_FILE = ROOT_DIR / "output" / f"brisanet_Capilaridade_{EXTRACTION_DATE}.csv"
OUTPUT_JSON_FILE = ROOT_DIR / "output" / f"brisanet_Capilaridade_{EXTRACTION_DATE}.json"
CSV_HEADERS = [
    "ID",
    "Nome da Loja",
    "Cidade",
    "UF",
    "Endereço",
    "CEP",
    "Telefone",
    "Tipo de Cadastro",
    "Latitude",
    "Longitude",
]


def find_attr(node, key):
    result = ""

    def dig(value):
        nonlocal result
        if isinstance(value, list):
            if len(value) > 1 and value[0] == key and isinstance(value[1], list):
                result = value[1][0] if value[1] else ""
                return
            for child in value:
                dig(child)

    dig(node)
    return result


def search(obj, results):
    if isinstance(obj, list):
        if (
            len(obj) >= 6
            and isinstance(obj[0], str)
            and re.search(r"^[0-9A-F]{10,}$", obj[0], re.IGNORECASE)
            and isinstance(obj[1], list)
            and isinstance(obj[5], list)
        ):
            item_id = obj[0]
            lat = ""
            lng = ""

            try:
                lat = obj[1][0][0][0]
                lng = obj[1][0][0][1]
            except (IndexError, KeyError, TypeError):
                pass

            nome = find_attr(obj[5], "nome") or ""
            endereco = find_attr(obj[5], "Endereço") or ""
            telefone = find_attr(obj[5], "Telefone") or ""
            tipo_cadastro = find_attr(obj[5], "Tipo do Cadastro") or ""

            cep_match = re.search(r"\d{5}-\d{3}", endereco)
            cep = cep_match.group(0) if cep_match else ""

            uf_match = re.search(r"[-/]\s*([A-Z]{2})\b", endereco)
            uf = uf_match.group(1) if uf_match else ""

            cidade = ""
            if uf_match and uf_match.start() > 0:
                text_before_uf = endereco[: uf_match.start()]
                parts = re.split(r"[,\-]", text_before_uf)
                cidade = parts[-1].strip()

            endereco_limpo = endereco.replace('"', "'").replace("\n", " ")

            if lat and lng:
                results.append(
                    {
                        "id": item_id,
                        "nome": nome,
                        "cidade": cidade,
                        "uf": uf,
                        "endereco": endereco_limpo,
                        "cep": cep,
                        "telefone": telefone,
                        "tipoCadastro": tipo_cadastro,
                        "lat": lat,
                        "lng": lng,
                    }
                )

        for child in obj:
            search(child, results)


def acquire_page_data():
    # verify=True: o alvo e um dominio do Google com cert valido; desabilitar
    # TLS aqui so gerava InsecureRequestWarning repetido e sem motivo.
    response = requests.get(
        MAP_URL, headers=REQUEST_HEADERS, timeout=60
    )
    response.raise_for_status()
    match = re.search(
        r"var\s+_pageData\s*=\s*(\"(?:\\.|[^\"\\])*\")\s*;",
        response.text,
    )
    if not match:
        raise RuntimeError("A variável _pageData não foi encontrada no HTML do viewer.")

    encoded_page_data = json.loads(match.group(1))
    return json.loads(encoded_page_data)


def csv_value(value):
    return str(value).replace(".", ",")


def write_outputs(results):
    OUTPUT_CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV_FILE.open("w", encoding="utf-8-sig", newline="") as output_file:
        output_file.write(";".join(CSV_HEADERS) + "\n")
        for item in results:
            values = [
                item["id"],
                item["nome"],
                item["cidade"],
                item["uf"],
                item["endereco"],
                item["cep"],
                item["telefone"],
                item["tipoCadastro"],
                csv_value(item["lat"]),
                csv_value(item["lng"]),
            ]
            output_file.write(";".join(f'"{value}"' for value in values) + "\n")

    payload = {
        "fonte": MAP_URL,
        "total_lojas": len(results),
        "campos": CSV_HEADERS,
        "lojas": results,
    }
    with OUTPUT_JSON_FILE.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, ensure_ascii=False, indent=2)


def main():
    page_data = acquire_page_data()
    results = []
    search(page_data, results)

    if not results:
        raise RuntimeError(
            "Nenhum registro encontrado: a estrutura de _pageData pode ter mudado."
        )
    if len(results) < MINIMUM_EXPECTED_RECORDS:
        print(
            f"AVISO: foram encontrados {len(results)} registros; "
            f"baseline={BASELINE_RECORDS}.",
            file=sys.stderr,
        )

    write_outputs(results)
    print(f"Sucesso: {len(results)} registros salvos em CSV e JSON.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERRO: {error}", file=sys.stderr)
        sys.exit(1)