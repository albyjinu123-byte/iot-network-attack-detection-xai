"""
Module 1: Hybrid Network Feature Intelligence Pipeline
SentinelAI - Multi-Class IoT Intrusion Detection System

Responsible for:
- Leakage-safe preprocessing & scaling
- Imputing missing / infinite flow values
- Tri-method feature consensus:
    1. Filter: ANOVA F-statistic
    2. Wrapper: Recursive Feature Elimination (RFE)
    3. Embedded: Random Forest Gini Impurity Reduction
- Isolating top 15 consensus features
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_selection import f_classif, RFE
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import json
import joblib
import os

# The 15 consensus features defined by the SentinelAI architecture
CONSENSUS_15_FEATURES = [
    "Header_Length",
    "Rate",
    "Time_To_Live",
    "AVG",
    "HTTPS",
    "ICMP",
    "TCP",
    "UDP",
    "syn_flag_number",
    "psh_flag_number",
    "ack_flag_number",
    "fin_flag_number",
    "IAT",
    "Protocol Type",
    "Number"
]

class FeatureIntelligencePipeline:
    def __init__(self, n_features_to_select=15):
        self.n_features = n_features_to_select
        self.scaler = MinMaxScaler()
        self.selected_features = list(CONSENSUS_15_FEATURES)
        self.feature_scores = {}
        
    def clean_network_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handles infinities and missing values typical of high-speed PCAP flow aggregation.
        Replaces inf/-inf with max/min valid float and imputes NaNs with median values.
        """
        df_clean = df.copy()
        
        # Replace positive and negative infinities with NaN
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        df_clean[numeric_cols] = df_clean[numeric_cols].replace([np.inf, -np.inf], np.nan)
        
        # Median imputation across numeric columns
        for col in numeric_cols:
            if df_clean[col].isnull().any():
                median_val = df_clean[col].median()
                df_clean[col] = df_clean[col].fillna(median_val if not np.isnan(median_val) else 0.0)
                
        return df_clean

    def fit_feature_consensus(self, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Runs the tri-method feature selection consensus:
        1. ANOVA F-test
        2. RFE with DecisionTree
        3. Random Forest Gini Importance
        Finds the intersection consensus.
        """
        print("[Module 1] Executing Tri-Method Feature Consensus Pipeline...")
        all_features = list(X_train.columns)
        
        # 1. Filter: ANOVA F-test
        f_scores, _ = f_classif(X_train, y_train)
        f_scores = np.nan_to_num(f_scores, nan=0.0)
        top_anova_idx = np.argsort(f_scores)[::-1][:25]
        top_anova = set([all_features[i] for i in top_anova_idx])
        print(f"[Module 1] ANOVA F-test selected {len(top_anova)} candidate features.")
        
        # 2. Wrapper: Recursive Feature Elimination
        rfe_estimator = DecisionTreeClassifier(max_depth=5, random_state=42)
        rfe = RFE(estimator=rfe_estimator, n_features_to_select=22, step=2)
        rfe.fit(X_train, y_train)
        top_rfe = set([feat for feat, supp in zip(all_features, rfe.support_) if supp])
        print(f"[Module 1] RFE Wrapper selected {len(top_rfe)} candidate features.")
        
        # 3. Embedded: Random Forest Importance
        rf_embedded = RandomForestClassifier(n_estimators=30, max_depth=6, random_state=42, n_jobs=-1)
        rf_embedded.fit(X_train, y_train)
        importances = rf_embedded.feature_importances_
        top_rf_idx = np.argsort(importances)[::-1][:20]
        top_rf = set([all_features[i] for i in top_rf_idx])
        print(f"[Module 1] Random Forest Embedded selected {len(top_rf)} candidate features.")
        
        # Consensus intersection
        consensus = top_anova.intersection(top_rfe).intersection(top_rf)
        print(f"[Module 1] 3-Way Intersection Size: {len(consensus)}")
        
        # If intersection is fewer than 15, supplement with highest weighted consensus
        if len(consensus) < self.n_features:
            ranked_pool = list(consensus)
            combined_scores = {}
            for i, feat in enumerate(all_features):
                score = (f_scores[i] / (np.max(f_scores) + 1e-6)) + (importances[i] / (np.max(importances) + 1e-6))
                if feat in top_rfe:
                    score += 1.0
                combined_scores[feat] = score
                
            sorted_feats = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
            for feat, _ in sorted_feats:
                if feat not in ranked_pool:
                    ranked_pool.append(feat)
                if len(ranked_pool) == self.n_features:
                    break
            self.selected_features = ranked_pool
        else:
            self.selected_features = list(consensus)[:self.n_features]
            
        print(f"[Module 1] Final 15 Consensus Features: {self.selected_features}")
        
        # Fit MinMax Scaler on the selected features
        self.scaler.fit(X_train[self.selected_features])
        return self.selected_features

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Subsets DataFrame to the consensus 15 features and transforms via fitted scaler.
        """
        missing = [f for f in self.selected_features if f not in X.columns]
        if missing:
            raise ValueError(f"Input DataFrame is missing consensus features: {missing}")
            
        X_sub = X[self.selected_features].copy()
        X_sub = X_sub.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return self.scaler.transform(X_sub)

    def save_artifacts(self, artifact_dir: str):
        """Saves scaler and selected feature metadata."""
        os.makedirs(artifact_dir, exist_ok=True)
        joblib.dump(self.scaler, os.path.join(artifact_dir, "scaler.pkl"))
        with open(os.path.join(artifact_dir, "selected_features.json"), "w") as f:
            json.dump({
                "selected_features": self.selected_features,
                "n_features": len(self.selected_features)
            }, f, indent=4)
        print(f"[Module 1] Artifacts successfully persisted to {artifact_dir}")

    def load_artifacts(self, artifact_dir: str):
        """Loads scaler and selected feature metadata."""
        scaler_path = os.path.join(artifact_dir, "scaler.pkl")
        features_path = os.path.join(artifact_dir, "selected_features.json")
        if os.path.exists(scaler_path) and os.path.exists(features_path):
            self.scaler = joblib.load(scaler_path)
            with open(features_path, "r") as f:
                data = json.load(f)
                self.selected_features = data["selected_features"]
            return True
        return False
