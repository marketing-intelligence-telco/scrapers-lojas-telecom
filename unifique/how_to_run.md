# Como executar o scraper Unifique

## O que o scraper faz

O scraper acessa a página de lojas da Unifique em `https://unifique.com.br/atendimento/lojas`.
Ele extrai cidade, UF, identificador, loja responsável, endereço e horário de atendimento.
Em seguida, cruza cidade/UF com a base de códigos IBGE.
Ao final, gera os mesmos registros em CSV e JSON.

## Pré-requisitos

- Python 3.13.14 ou versão compatível mais recente.
- O arquivo `Base_BR_IBGE.xlsx` deve existir em `data/Base_BR_IBGE.xlsx` antes da execução.
- Acesso à internet para consultar o site da Unifique.

## Setup do ambiente virtual

### Windows PowerShell

Execute a partir de `scrapers/lojas_fisicas/unifique/`:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS

Execute a partir de `scrapers/lojas_fisicas/unifique/`:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Como executar

A partir de `scrapers/lojas_fisicas/unifique/`, com o ambiente virtual ativado:

```bash
python unifique.py
```

O script não recebe argumentos de linha de comando.

## Saídas esperadas

- `output/lojas_unifique.csv`: CSV separado por `;`, codificado em `utf-8-sig`, com as colunas:
  `ID`, `Cidade`, `UF`, `cidade_uf`, `COD IBGE`, `Atendida_Por`, `Endereco_Completo`, `Horario`.
- `output/lojas_unifique.json`: objeto JSON com a estrutura:

```json
{
  "fonte": "https://unifique.com.br/atendimento/lojas",
  "total_lojas": 132,
  "campos": ["ID", "Cidade", "UF", "cidade_uf", "COD IBGE", "Atendida_Por", "Endereco_Completo", "Horario"],
  "lojas": [{"ID": "94F2F55E", "Cidade": "Abdon Batista"}]
}
```

O total e os valores dos registros podem mudar conforme o conteúdo publicado no site.

## Troubleshooting

- **Arquivo de input ausente:** confirme que `data/Base_BR_IBGE.xlsx` existe e que contém as colunas `uf_cidade` e `COD IBGE`.
- **Cookies ou sessão expirados:** o site pode retornar erro, bloquear a requisição ou entregar HTML vazio; renove manualmente os cookies e headers no topo de `unifique.py`.
- **Seletores HTML alterados:** se a página mudar sua estrutura, os seletores usados pelo parser podem deixar de encontrar as lojas; revise o HTML e os seletores do script.
- **`openpyxl` faltando:** instale as dependências com `pip install -r requirements.txt` ou, especificamente, `pip install openpyxl`.
- **CSV não gerado:** verifique se a extração retornou lojas e se o processo possui permissão para escrever em `output/`.

## Nota sobre cookies

Os cookies e headers no topo do script são estáticos. Se o site começar a retornar erro ou HTML vazio, pode ser necessário renová-los manualmente.
