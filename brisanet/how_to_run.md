# Como executar o scraper Brisanet

## O que faz

O scraper acessa o Google My Maps customizado da Brisanet por HTTP puro.
Ele extrai os pontos das camadas de escritórios e novas lojas a partir de `_pageData`.
O resultado contém identificação, nome, endereço, CEP, telefone, tipo de cadastro e coordenadas.
São gerados um CSV compatível com Excel e um JSON estruturado.

## Pré-requisitos

- Python 3.13.14 ou versão compatível.
- Acesso à internet.
- O mapa precisa continuar publicado e acessível pelo `mid` configurado no script.
- Não é necessário arquivo de input local nem navegador.

## Setup do ambiente virtual

### Windows PowerShell

A partir de `scrapers/lojas_fisicas/brisanet/`:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS

A partir de `scrapers/lojas_fisicas/brisanet/`:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Execução

A partir de `scrapers/lojas_fisicas/brisanet/`:

```bash
python brisanet_scraper.py
```

## Saídas esperadas

- `output/brisanet_lojas.csv`: CSV UTF-8 com BOM, separador `;`, header nesta ordem:
  `ID`, `Nome da Loja`, `Cidade`, `UF`, `Endereço`, `CEP`, `Telefone`, `Tipo de Cadastro`, `Latitude`, `Longitude`.
  Os valores são delimitados por aspas e as coordenadas usam vírgula decimal para o Excel.
- `output/brisanet_lojas.json`: envelope com `fonte`, `total_lojas`, `campos` e `lojas`. Latitude e longitude permanecem números JSON com ponto decimal.

Exemplo resumido:

```json
{
  "fonte": "https://www.google.com/maps/d/u/0/viewer?mid=...&femb=1",
  "total_lojas": 337,
  "campos": ["ID", "Nome da Loja", "Cidade", "UF", "Endereço", "CEP", "Telefone", "Tipo de Cadastro", "Latitude", "Longitude"],
  "lojas": [{"id": "517C8816FE000001", "lat": -3.499577, "lng": -39.57999}]
}
```

## Guarda de regressão

O baseline conhecido é de 337 registros. Zero registros interrompe a execução com código de saída diferente de zero. Quantidades abaixo de 168 geram um aviso destacado no stderr; a saída ainda é gravada para investigação.

## Seção de fragilidade

- **Estrutura interna de `_pageData`:** o parser depende da assinatura de arrays (`obj[0]` como ID hexadecimal, `obj[1]` como coordenadas e `obj[5]` como atributos), além das chaves e regex atuais. Se o resultado for zero ou cair muito, compare o HTML baixado e a forma da variável `_pageData` com o viewer.
- **Mapa despublicado ou restrito:** a requisição pode retornar erro HTTP, uma página de login ou HTML sem `_pageData`. Verifique o status HTTP e abra a URL do mapa no navegador.
- **`mid` alterado:** se o mapa for substituído, atualize `MAP_ID` no topo do script e valide novamente a contagem contra o mapa manual.
- **Mudança de conteúdo/camadas:** o parser percorre recursivamente os dados das camadas presentes no `_pageData`; ele não adiciona uma coluna de camada, pois o contrato CSV é imutável.

Para diagnóstico, execute o comando observando a mensagem de erro e confira se a URL configurada ainda retorna HTML público com `var _pageData`.

## Agendamento

Como o mapa muda pouco, uma execução diária ou semanal é suficiente. Para acompanhamento operacional, recomenda-se diária; para uma rotina de atualização menos frequente, semanal reduz requisições sem perder alterações relevantes.
