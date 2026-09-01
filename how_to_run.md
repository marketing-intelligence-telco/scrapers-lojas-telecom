# Projeto Lojas Espaço Scraper - Como rodar

## Rodar todas as operadoras em sequência

Na raiz do projeto:

```bash
python run_all.py
```

Esse runner executa na ordem:

1. Claro
2. Vivo
3. TIM
4. Unifique

## Rodar cada operadora isoladamente

### Claro

```bash
cd Claro
python claro_run_all.py
```

### Vivo

```bash
cd Vivo
python vivo_run_all.py
```

### TIM

```bash
cd TIM
python tim_lojas_scrapper.py
```

### Unifique

```bash
cd unifique
python unifique.py
```

## Instalar dependências

Para cada pasta, use:

```bash
python -m pip install -r requirements.txt
```

## Observações

- O projeto foi organizado por operadora em pastas separadas.
- A pasta venv não é movida nem copiada para as pastas das operadoras.
- Os outputs ficam dentro de cada pasta correspondente.
- **Unifique:** Requer que `unifique/data/Base_BR_IBGE.xlsx` exista antes da execução (arquivo de referência do IBGE). Este arquivo é necessário para enriquecer os dados das lojas com os códigos IBGE por município.
