# Claro - Como rodar

## Requisitos

```bash
python -m pip install -r requirements.txt
```

## Execução principal

Na pasta Claro:

```bash
python claro_run_all.py
```

Esse runner executa, em sequência:

1. claro_lojas_scrapper.py
2. claro_format.py
3. claro_excel.py

## Saídas geradas

- claro_lojas_revendas_pdvs.json
- claro_lojas_revendas_pdvs_processed.json
- claro_lojas_revendas_pdvs.xlsx

## Observações

- O script usa a API da Claro diretamente.
- A pasta venv do projeto não deve ser copiada para esta pasta.
- Os arquivos de saída ficam no mesmo diretório do runner.
