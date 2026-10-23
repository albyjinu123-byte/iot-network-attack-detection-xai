"""
legacy_v1: create_dataset.py
Initial prototype script to preprocess raw CICIoT2023 flows into sample CSV subsets.
"""
import os
import pandas as pd
import numpy as np

def create_sample_dataset(raw_path="legacy_v1/data/raw_ciciot2023_slice_0.csv", output_path="legacy_v1/data/sampled_dataset.csv", n_samples=10000):
    if not os.path.exists(raw_path):
        print(f"[!] Raw file {raw_path} not found. Creating synthetic preview data for prototyping...")
        labels = ["BenignTraffic", "DDoS-ICMP_Flood", "DDoS-TCP_Flood", "DDoS-UDP_Flood", "DDoS-SYN_Flood"]
        data = {
            "Header_Length": np.random.randint(20, 100, size=n_samples),
            "Protocol Type": np.random.choice([6, 17, 1], size=n_samples),
            "Rate": np.random.exponential(scale=200.0, size=n_samples),
            "label": np.random.choice(labels, size=n_samples)
        }
        df = pd.DataFrame(data)
    else:
        df = pd.read_csv(raw_path, nrows=n_samples)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] Sample dataset created with shape {df.shape} at {output_path}")

if __name__ == "__main__":
    create_sample_dataset()
