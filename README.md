# Scrapers de lojas físicas

Esta pasta reúne scrapers de presença física organizados por operadora. Cada operadora possui seu próprio diretório, dados de entrada, documentação, dependências e saídas.

## Operadoras

| Operadora | Pasta | Status | O que extrai |
|---|---|---|---|
| Unifique | `unifique/` | Ativo | Lojas físicas, cidade, UF, endereço, horário e código IBGE |
| Algar | `algar/` | A definir | A preencher |
| Brisanet | `brisanet/` | A definir | A preencher |

## Convenção para novas operadoras

Toda nova operadora deve seguir esta estrutura:

```text
<operadora>/
├── <operadora>.py
├── requirements.txt
├── how_to_run.md
├── data/
└── output/
    └── .gitkeep
```

`data/` contém somente inputs do scraper. `output/` contém os arquivos gerados durante a execução.
