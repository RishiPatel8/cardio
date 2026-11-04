import os
import pandas as pd
import requests
import concurrent.futures
import time

def download_file(url, local_path):
    if os.path.exists(local_path):
        return True # Already exists
    
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        # Delete partial file if it exists
        if os.path.exists(local_path):
            os.remove(local_path)
        return False

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'ptbxl'))
    csv_path = os.path.join(base_dir, 'ptbxl_database.csv')
    
    if not os.path.exists(csv_path):
        print(f"CSV not found at {csv_path}. Cannot download files.")
        return

    df = pd.read_csv(csv_path)
    base_url = "https://physionet.org/files/ptb-xl/1.0.3/"
    
    download_tasks = []
    
    for _, row in df.iterrows():
        # filename_lr is like 'records100/00000/00001_lr'
        file_base = row['filename_lr']
        dat_url = base_url + file_base + ".dat"
        hea_url = base_url + file_base + ".hea"
        
        dat_local = os.path.join(base_dir, file_base + ".dat")
        hea_local = os.path.join(base_dir, file_base + ".hea")
        
        if not os.path.exists(dat_local):
            download_tasks.append((dat_url, dat_local))
        if not os.path.exists(hea_local):
            download_tasks.append((hea_url, hea_local))
            
    print(f"Found {len(download_tasks)} files missing. Starting resumable download...")
    
    # We use a relatively small number of workers to not get rate-limited by PhysioNet
    success_count = 0
    fail_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(download_file, task[0], task[1]): task[0] for task in download_tasks}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as exc:
                print(f'{url} generated an exception: {exc}')
                fail_count += 1
                
            if (i + 1) % 500 == 0:
                print(f"Progress: {i+1}/{len(download_tasks)}. Success: {success_count}, Fail: {fail_count}")

    print(f"Download complete. Successful: {success_count}. Failed: {fail_count}.")

if __name__ == "__main__":
    main()
