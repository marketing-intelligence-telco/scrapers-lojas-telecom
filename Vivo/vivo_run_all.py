import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def executar_esteira():
    scripts = [
        # Esses dois primeiros scripts caducaram e não são mais necessários, então estão comentados.
        # "vivo_lojas_scrapper.py",
        # "vivo_lojas_scrapper_api.py",
        "vivo_scrapper_v4.py",
        "vivo_format.py",
        "vivo_excel.py"
    ]

    print("Iniciando a esteira de extração de dados...\n")

    for script in scripts:
        script_path = BASE_DIR / script
        print(f"⏳ Iniciando: {script_path.name} ...")

        try:
            subprocess.run([sys.executable, str(script_path)], check=True)
            print(f"✅ Sucesso: {script_path.name} concluído.\n")

        except subprocess.CalledProcessError as e:
            print(f"❌ Erro Crítico: O script '{script_path.name}' falhou (código {e.returncode}).")
            print("A execução foi interrompida para evitar dados inconsistentes nas próximas etapas.")
            sys.exit(1)

        except FileNotFoundError:
            print(f"🔍 Erro: O arquivo '{script_path.name}' não foi encontrado.")
            print("Certifique-se de que ele está no mesmo diretório deste script principal.")
            sys.exit(1)

    print("🎉 Todos os scripts foram executados com sucesso! O Excel deve estar pronto.")

if __name__ == "__main__":
    executar_esteira()