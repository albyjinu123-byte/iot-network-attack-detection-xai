"""
legacy_v1: download_data.py
Prototype script for downloading CICIoT2023 raw CSV slices.
"""
import os
import urllib.request

DATA_URLS = [
    "http://205.174.165.178/IOTDataset/CIC_IOT_2023/Dataset/DATASET-CSV/part-00000-363d8616-edd3-4b3c-9f18-2d007821dd93-c000.csv",
]

def download_dataset(target_dir="legacy_v1/data"):
    os.makedirs(target_dir, exist_ok=True)
    print(f"[*] Target directory: {target_dir}")
    for idx, url in enumerate(DATA_URLS):
        filename = os.path.join(target_dir, f"raw_ciciot2023_slice_{idx}.csv")
        print(f"[*] Downloading slice {idx+1}/{len(DATA_URLS)} from {url}...")
        try:
            urllib.request.urlretrieve(url, filename)
            print(f"[OK] Downloaded to {filename}")
        except Exception as e:
            print(f"[!] Download failed (network/mirror offline): {e}")

if __name__ == "__main__":
    download_dataset()
