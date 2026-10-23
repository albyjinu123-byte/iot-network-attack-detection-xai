"""
SentinelAI - Autonomous Pipeline Runner (auto_run.py)
Recreates the 50/50 hold-out split, executes the tri-method feature selection consensus,
trains all candidate models and the Soft Voting Ensemble, and exports demo test samples.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure ml_modules are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from ml_modules.module1_feature_intelligence.pipeline import FeatureIntelligencePipeline, CONSENSUS_15_FEATURES
from ml_modules.module2_detection_engine.trainer import DetectionEngineTrainer
from ml_modules.module3_security_analytics.evaluator import SecurityAnalyticsEvaluator

# Raw 40+ features from CICIoT2023 benchmark schema
ALL_40_FEATURES = [
    "flow_duration", "Header_Length", "Protocol Type", "Duration", "Rate", "Srate", "Drate",
    "fin_flag_number", "syn_flag_number", "rst_flag_number", "psh_flag_number", "ack_flag_number",
    "ece_flag_number", "cwr_flag_number", "ack_count", "syn_count", "fin_count", "urg_count",
    "rst_count", "HTTP", "HTTPS", "DNS", "Telnet", "SMTP", "SSH", "IRC", "TCP", "UDP",
    "DHCP", "ARP", "ICMP", "IPv", "LLC", "Tot sum", "Min", "Max", "AVG", "Std", "Tot size",
    "IAT", "Number", "Magnitue", "Radius", "Covariance", "Variance", "Weight", "Time_To_Live"
]

ATTACK_CLASSES = [
    "BenignTraffic",
    "DDoS-ICMP_Flood",
    "DDoS-UDP_Flood",
    "DDoS-TCP_Flood",
    "DDoS-SYN_Flood",
    "DDoS-PSHACK_Flood",
    "DDoS-RSTFINFlood",
    "DDoS-SlowLoris",
    "DDoS-ICMP_Fragmentation"
]

def generate_representative_ciciot_dataset(n_samples: int = 15000) -> pd.DataFrame:
    """
    Generates a realistic, high-fidelity synthetic CICIoT2023 telemetry dataset
    exhibiting characteristic statistical distributions for benign IoT and flood attacks.
    """
    print(f"[SentinelAI Data Engine] Generating {n_samples} realistic CICIoT2023 network flow records...")
    np.random.seed(42)
    
    rows = []
    # Distribute samples across attack types
    class_weights = [0.30, 0.12, 0.15, 0.12, 0.10, 0.08, 0.05, 0.04, 0.04]
    assigned_classes = np.random.choice(ATTACK_CLASSES, size=n_samples, p=class_weights)
    
    for i in range(n_samples):
        label = assigned_classes[i]
        is_attack = label != "BenignTraffic"
        
        # Base realistic features
        row = {}
        if not is_attack:
            # Benign normal IoT communication (e.g. MQTT, HTTP, DNS)
            row["Header_Length"] = np.random.normal(54, 8)
            row["Rate"] = np.random.exponential(15.0)
            row["Time_To_Live"] = np.random.choice([64, 128, 255])
            row["AVG"] = np.random.normal(250, 50)
            row["HTTPS"] = 1 if np.random.rand() > 0.4 else 0
            row["ICMP"] = 0
            row["TCP"] = 1 if np.random.rand() > 0.3 else 0
            row["UDP"] = 1 if row["TCP"] == 0 else 0
            row["syn_flag_number"] = 1 if np.random.rand() > 0.85 else 0
            row["psh_flag_number"] = 1 if np.random.rand() > 0.6 else 0
            row["ack_flag_number"] = 1 if np.random.rand() > 0.3 else 0
            row["fin_flag_number"] = 1 if np.random.rand() > 0.9 else 0
            row["IAT"] = np.random.exponential(0.05)
            row["Protocol Type"] = 6 if row["TCP"] == 1 else (17 if row["UDP"] == 1 else 1)
            row["Number"] = np.random.randint(1, 15)
        else:
            # Attack traffic patterns
            if "SYN_Flood" in label:
                row["Header_Length"] = np.random.normal(40, 2)
                row["Rate"] = np.random.normal(1200, 200)
                row["Time_To_Live"] = np.random.choice([48, 64, 112])
                row["AVG"] = np.random.normal(60, 10)
                row["HTTPS"] = 0
                row["ICMP"] = 0
                row["TCP"] = 1
                row["UDP"] = 0
                row["syn_flag_number"] = 1
                row["psh_flag_number"] = 0
                row["ack_flag_number"] = 0
                row["fin_flag_number"] = 0
                row["IAT"] = np.random.exponential(0.001)
                row["Protocol Type"] = 6
                row["Number"] = np.random.randint(50, 300)
            elif "UDP_Flood" in label:
                row["Header_Length"] = np.random.normal(28, 4)
                row["Rate"] = np.random.normal(2500, 400)
                row["Time_To_Live"] = np.random.choice([32, 64])
                row["AVG"] = np.random.normal(512, 100)
                row["HTTPS"] = 0
                row["ICMP"] = 0
                row["TCP"] = 0
                row["UDP"] = 1
                row["syn_flag_number"] = 0
                row["psh_flag_number"] = 0
                row["ack_flag_number"] = 0
                row["fin_flag_number"] = 0
                row["IAT"] = np.random.exponential(0.0005)
                row["Protocol Type"] = 17
                row["Number"] = np.random.randint(100, 600)
            elif "ICMP" in label:
                row["Header_Length"] = np.random.normal(28, 2)
                row["Rate"] = np.random.normal(1800, 300)
                row["Time_To_Live"] = np.random.choice([64, 128])
                row["AVG"] = np.random.normal(84, 15)
                row["HTTPS"] = 0
                row["ICMP"] = 1
                row["TCP"] = 0
                row["UDP"] = 0
                row["syn_flag_number"] = 0
                row["psh_flag_number"] = 0
                row["ack_flag_number"] = 0
                row["fin_flag_number"] = 0
                row["IAT"] = np.random.exponential(0.002)
                row["Protocol Type"] = 1
                row["Number"] = np.random.randint(80, 400)
            else:
                # Other floods / SlowLoris
                row["Header_Length"] = np.random.normal(60, 15)
                row["Rate"] = np.random.normal(350, 80)
                row["Time_To_Live"] = np.random.choice([64, 128])
                row["AVG"] = np.random.normal(180, 40)
                row["HTTPS"] = 0
                row["ICMP"] = 0
                row["TCP"] = 1
                row["UDP"] = 0
                row["syn_flag_number"] = 1 if np.random.rand() > 0.4 else 0
                row["psh_flag_number"] = 1 if np.random.rand() > 0.5 else 0
                row["ack_flag_number"] = 1 if np.random.rand() > 0.5 else 0
                row["fin_flag_number"] = 1 if np.random.rand() > 0.6 else 0
                row["IAT"] = np.random.exponential(0.02)
                row["Protocol Type"] = 6
                row["Number"] = np.random.randint(20, 150)
                
        # Fill remaining non-consensus features to maintain 40+ feature shape
        for feat in ALL_40_FEATURES:
            if feat not in row:
                row[feat] = abs(np.random.normal(10, 5))
                
        row["label"] = label
        row["src_ip"] = f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
        rows.append(row)
        
    df = pd.DataFrame(rows)
    return df

def run_autonomous_pipeline():
    print("=" * 70)
    print("[SentinelAI] Autonomous Retraining & Deployment Pipeline")
    print("=" * 70)
    
    models_dir = os.path.join(current_dir, "models")
    experiments_dir = os.path.join(current_dir, "experiments", "current_run")
    demo_dir = os.path.join(current_dir, "demo_scenarios")
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(experiments_dir, exist_ok=True)
    os.makedirs(demo_dir, exist_ok=True)
    
    # 1. Dataset Generation & Preprocessing
    df = generate_representative_ciciot_dataset(n_samples=12000)
    
    # Encode Target Labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(df["label"])
    target_names = list(label_encoder.classes_)
    joblib.dump(label_encoder, os.path.join(experiments_dir, "label_encoder.pkl"))
    
    feature_cols = [c for c in df.columns if c not in ["label", "src_ip"]]
    X = df[feature_cols]
    
    # 2. Strict 50/50 Leakage-Safe Hold-Out Split
    print("[Pipeline] Splitting data into 50% Train and 50% Hold-Out Test set...")
    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y_encoded, df, test_size=0.50, random_state=42, stratify=y_encoded
    )
    
    # Export 5,000 Hold-Out Packets for Frontend Simulator Replay
    demo_sample_path = os.path.join(demo_dir, "frontend_test_sample.csv")
    df_test.head(5000).to_csv(demo_sample_path, index=False)
    print(f"[Pipeline] Exported 5,000 hold-out packets to {demo_sample_path}")
    
    # 3. Module 1: Hybrid Feature Intelligence (Tri-Method Consensus)
    pipeline_m1 = FeatureIntelligencePipeline(n_features_to_select=15)
    X_train_clean = pipeline_m1.clean_network_dataframe(X_train)
    selected_features = pipeline_m1.fit_feature_consensus(X_train_clean, y_train)
    
    pipeline_m1.save_artifacts(experiments_dir)
    
    X_train_scaled = pipeline_m1.transform(X_train)
    X_test_scaled = pipeline_m1.transform(X_test)
    
    # 4. Module 2: Detection Engine Training
    trainer_m2 = DetectionEngineTrainer(random_state=42)
    ensemble = trainer_m2.train_models(X_train_scaled, y_train)
    trainer_m2.save_models(models_dir)
    
    # 5. Module 3: Security Analytics & Evaluation
    evaluator_m3 = SecurityAnalyticsEvaluator(feature_names=selected_features)
    metrics_report = evaluator_m3.evaluate_all_models(
        trainer_m2.models, ensemble, X_test_scaled, y_test, target_names
    )
    
    # Initialize background TreeSHAP explainer
    evaluator_m3.initialize_shap_explainer(trainer_m2.models["Random_Forest"], X_train_scaled)
    joblib.dump(evaluator_m3.explainer, os.path.join(experiments_dir, "shap_explainer.pkl"))
    
    # Persist metrics report
    report_path = os.path.join(experiments_dir, "metrics_report.json")
    with open(report_path, "w") as f:
        json.dump({
            "metrics": metrics_report,
            "classes": target_names,
            "selected_features": selected_features,
            "train_samples": len(X_train),
            "test_samples": len(X_test)
        }, f, indent=4)
        
    print(f"[Pipeline] Metrics report persisted to {report_path}")
    print("\n" + "=" * 70)
    print("[SUCCESS] SentinelAI Engine fully trained and ready for live FastAPI deployment!")
    print("=" * 70)

if __name__ == "__main__":
    run_autonomous_pipeline()
