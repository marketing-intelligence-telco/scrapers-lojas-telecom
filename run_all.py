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
    except subprocess.CalledProcessError as e:
        print(f"✖ Falha em {descricao} (código {e.returncode}).")
        raise SystemExit(1)
    except FileNotFoundError:
        print(f"✖ Arquivo não encontrado: {script_path}")
        raise SystemExit(1)


def main():
    scripts = [
        ("Claro", BASE_DIR / "Claro" / "claro_run_all.py"),
        ("Vivo", BASE_DIR / "Vivo" / "vivo_run_all.py"),
        ("TIM", BASE_DIR / "TIM" / "tim_lojas_scrapper.py"),
        ("Algar", BASE_DIR / "algar" / "run_all.py"),
        ("Brisanet", BASE_DIR / "brisanet" / "brisanet_scraper.py"),
        ("Unifique", BASE_DIR / "unifique" / "unifique.py"),
    ]

    for descricao, script_path in scripts:
        if not script_path.exists():
            print(f"✖ Script não encontrado para {descricao}: {script_path}")
            raise SystemExit(1)

        executar_script(descricao, script_path)

    print(f"\n{'=' * 70}")
    print("PROCESSO GLOBAL CONCLUÍDO: Claro → Vivo → TIM → Algar → Brisanet → Unifique")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
