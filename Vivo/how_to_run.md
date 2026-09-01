# Vivo - Como rodar

## Requisitos

```bash
python -m pip install -r requirements.txt
```

## Execução principal

Na pasta Vivo:

```bash
python vivo_run_all.py
```

Esse runner executa, em sequência:

1. vivo_scrapper_v4.py
2. vivo_format.py
3. vivo_excel.py

## Saídas geradas

- vivo_lojas_nacional.json
- vivo_processed_address.json
- vivo_lojas_revendas.xlsx

## Observações

- O scraper usa a API da Vivo e faz varredura autocalibrada por raio.
- O runner foi validado em execução real.
- Os arquivos gerados ficam na pasta Vivo.
