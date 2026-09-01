import subprocess
import sys
import os

def run_script(script_name):
    # Check if the file actually exists in the current folder before trying to run it
    if not os.path.exists(script_name):
        print(f"\n[ERROR] ❌ Could not find '{script_name}' in the current directory.")
        return False

    print(f"\n{'='*60}")
    print(f"🚀 STARTING: {script_name}")
    print(f"{'='*60}\n")
    
    try:
        # sys.executable ensures we use the current Python interpreter (great for venvs)
        # check=True ensures an exception is raised if the script crashes
        subprocess.run([sys.executable, script_name], check=True)
        
        print(f"\n✅ [SUCCESS] '{script_name}' finished execution.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n[CRITICAL ERROR] ❌ '{script_name}' crashed with exit code {e.returncode}.")
        return False
    except KeyboardInterrupt:
        print(f"\n[WARNING] 🛑 Execution of '{script_name}' was manually interrupted.")
        return False

def main():
    # Define the order of execution
    pipeline = [
        "generate_cities.py",
        "algar_scrapper.py",
        "generate_excel.py"
    ]
    
    print("🤖 Starting the Algar Web Scraping Pipeline...")
    
    for script in pipeline:
        success = run_script(script)
        
        # If generate_cities.py fails, there is no point in running the scraper.
        # This breaks the loop to prevent cascading errors.
        if not success:
            print("\n🚨 Pipeline aborted due to an error in the previous step.")
            break
            
    else:
        # This 'else' belongs to the 'for' loop (it triggers only if the loop doesn't 'break')
        print(f"\n{'='*60}")
        print("🎉 PIPELINE COMPLETE! All scripts executed successfully.")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()