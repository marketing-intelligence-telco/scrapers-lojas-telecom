import json
import requests
import csv
import urllib3
from pathlib import Path
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
EXTRACTION_DATE = datetime.now().strftime("%Y-%m-%d")

def main():
    # 1. Load the initial JSON data
    input_file = OUTPUT_DIR / f'algar_Capilaridade_{EXTRACTION_DATE}.json'
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            dados_algar = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
        return

    # 2. Extract unique (city, state) pairs to avoid duplicate API requests
    unique_locations = set()
    for item in dados_algar:
        cidade = item.get("cidade")
        estado = item.get("estado")
        if cidade and estado:
            unique_locations.add((cidade, estado))

    print(f"Found {len(unique_locations)} unique locations to query.")

    # API Base URL and Headers
    url = "https://loja.algar.com.br/on/demandware.store/Sites-algartelecom-BR-Site/pt_BR/Stores-FindStores"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 3. Define the CSV headers based on the API 'stores' structure
    csv_headers = [
        "ID", "name", "address1", "address2", "city", 
        "postalCode", "latitude", "longitude", "phone", 
        "stateCode", "countryCode", "storeHours"
    ]
    
    output_file = OUTPUT_DIR / f'algar_Capilaridade_{EXTRACTION_DATE}.csv'

    # Array to track requests that fail during the run
    failed_locations = []

    # 4 & 5. Setup CSV, iterate through locations, request, and write
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()

        for cidade, estado in unique_locations:
            print(f"Fetching data for {cidade} - {estado}...")
            
            # Setup dynamic query parameters
            params = {
                "showMap": "false",
                "state": estado,
                "city": cidade
            }

            try:
                response = requests.get(url, params=params, headers=headers, verify=False)
                
                # Check if the request was successful
                if response.status_code == 200:
                    data = response.json()
                    stores = data.get("stores", [])
                    
                    if not stores:
                        print(f"  -> No stores found in the API response for {cidade}.")
                        continue

                    for store in stores:
                        # Extract only the fields we care about, respecting nulls
                        row_data = {key: store.get(key) for key in csv_headers}
                        writer.writerow(row_data)
                        
                    print(f"  -> Saved {len(stores)} store(s).")
                else:
                    print(f"  -> Failed to fetch {cidade}. Status code: {response.status_code}")
                    failed_locations.append((cidade, estado))
                    
            except requests.exceptions.RequestException as e:
                print(f"  -> Request error for {cidade}: {e}")
                failed_locations.append((cidade, estado))
            except json.JSONDecodeError:
                print(f"  -> Error: API did not return valid JSON for {cidade}.")
                failed_locations.append((cidade, estado))

        # --- RETRY LOGIC QUEUE ---
        max_retries = 3
        current_retry = 0

        # Loop will run if there are items in the array AND we haven't hit the 3-retry limit
        while failed_locations and current_retry < max_retries:
            current_retry += 1
            print(f"\n--- Starting Retry Attempt {current_retry}/{max_retries} for {len(failed_locations)} failed locations ---")
            
            # Copy the failed list to iterate over, and clear the main one to catch new failures during this retry
            locations_to_retry = failed_locations.copy()
            failed_locations.clear()

            for cidade, estado in locations_to_retry:
                print(f"Retrying data for {cidade} - {estado}...")
                
                params = {
                    "showMap": "false",
                    "state": estado,
                    "city": cidade
                }

                try:
                    response = requests.get(url, params=params, headers=headers, verify=False)
                    
                    if response.status_code == 200:
                        data = response.json()
                        stores = data.get("stores", [])
                        
                        if not stores:
                            print(f"  -> No stores found in the API response for {cidade}.")
                            continue

                        for store in stores:
                            row_data = {key: store.get(key) for key in csv_headers}
                            writer.writerow(row_data)
                            
                        print(f"  -> Saved {len(stores)} store(s).")
                    else:
                        print(f"  -> Failed to fetch {cidade}. Status code: {response.status_code}")
                        failed_locations.append((cidade, estado))
                        
                except requests.exceptions.RequestException as e:
                    print(f"  -> Request error for {cidade}: {e}")
                    failed_locations.append((cidade, estado))
                except json.JSONDecodeError:
                    print(f"  -> Error: API did not return valid JSON for {cidade}.")
                    failed_locations.append((cidade, estado))

        # Final sanity check to log if any locations permanently failed
        if failed_locations:
            print(f"\n[WARNING] Finished all {max_retries} retries, but {len(failed_locations)} locations still failed.")
        elif current_retry > 0:
            print("\n[SUCCESS] All retry attempts successfully recovered the failed requests.")

    print(f"\nProcess complete! All data has been saved to {output_file}.")

if __name__ == "__main__":
    main()