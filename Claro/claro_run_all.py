import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def executar_script(script_name):
    script_path = BASE_DIR / script_name
    print(f"\n{'='*50}")
    print(f"Iniciando: {script_path.name}")
    print(f"{'='*50}")

    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
        print(f"✔ {script_path.name} finalizado com sucesso!")
    except subprocess.CalledProcessError:
        print(f"✖ Erro ao executar {script_path.name}. Interrompendo o processo.")
        sys.exit(1)

def main():
    scripts = [
        "claro_lojas_scrapper.py",
        "claro_format.py",
        "claro_excel.py"
    ]

    for script in scripts:
        executar_script(script)

    print(f"\n{'='*50}")
    print("PROCESSO CONCLUÍDO: Planilha gerada com sucesso!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()