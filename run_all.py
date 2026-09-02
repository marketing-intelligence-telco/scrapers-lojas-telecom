import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def executar_script(descricao, script_path):
    print(f"\n{'=' * 70}")
    print(f"Iniciando: {descricao}")
    print(f"Caminho: {script_path}")
    print(f"Working dir: {script_path.parent}")
    print(f"{'=' * 70}")

    if not script_path.exists():
        print(f"✖ Arquivo não encontrado: {script_path}")
        return False

    try:
        # cwd = pasta do proprio script.
        # Isso faz o processo filho rodar como se voce tivesse feito 'cd' na pasta dele,
        # entao caminhos relativos como 'output/...' e 'data/...' resolvem corretamente.
        subprocess.run(
            [sys.executable, script_path.name],
            check=True,
            cwd=str(script_path.parent),
        )
        print(f"✔ {descricao} finalizado com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✖ Falha em {descricao} (código {e.returncode}).")
        return False


def main():
    scripts = [
        ("Claro", BASE_DIR / "Claro" / "claro_run_all.py"),
        ("Vivo", BASE_DIR / "Vivo" / "vivo_run_all.py"),
        ("TIM", BASE_DIR / "TIM" / "tim_lojas_scrapper.py"),
        ("Algar", BASE_DIR / "algar" / "run_all.py"),
        ("Brisanet", BASE_DIR / "brisanet" / "brisanet_scraper.py"),
        ("Unifique", BASE_DIR / "unifique" / "unifique.py"),
    ]

    # Cada scraper e independente: a falha de um NAO interrompe os demais.
    # As falhas sao acumuladas e reportadas no fim; o processo sai com codigo
    # != 0 se qualquer scraper falhou (util para CI / agendador).
    resultados = {
        descricao: executar_script(descricao, script_path)
        for descricao, script_path in scripts
    }

    ok = [d for d, sucesso in resultados.items() if sucesso]
    falhas = [d for d, sucesso in resultados.items() if not sucesso]

    print(f"\n{'=' * 70}")
    print("RESUMO DO PROCESSO GLOBAL")
    print(f"{'=' * 70}")
    print(f"✔ Sucesso ({len(ok)}): {', '.join(ok) if ok else '-'}")
    print(f"✖ Falha   ({len(falhas)}): {', '.join(falhas) if falhas else '-'}")
    print(f"{'=' * 70}")

    if falhas:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
