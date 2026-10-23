"""
Module 2: Multi-Algorithm Ensemble Detection Engine
SentinelAI - Multi-Class IoT Intrusion Detection System

Responsible for:
- Training individual base classifiers:
    1. Random Forest (100 estimators, balanced class weights)
    2. CatBoostClassifier (Symmetric oblivious trees)
    3. HistGradientBoostingClassifier (LightGBM equivalent, binned histograms)
    4. Calibrated Linear SVC (Regularized hyperplane baseline)
- Assembling models via Soft Voting (probability aggregation)
- Serializing models to disk for low-latency serving
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, VotingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from catboost import CatBoostClassifier

class DetectionEngineTrainer:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models = {}
        self.ensemble = None
        
    def initialize_base_models(self):
        """Initializes all base models specified in the SentinelAI specification."""
        print("[Module 2] Initializing base classifiers with balanced class weighting...")
        
        # 1. Random Forest
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            class_weight='balanced',
            n_jobs=-1,
            random_state=self.random_state
        )
        
        # 2. CatBoost
        cat = CatBoostClassifier(
            iterations=120,
            depth=6,
            learning_rate=0.1,
            verbose=False,
            random_seed=self.random_state
        )
        
        # 3. HistGradientBoosting (LightGBM equivalent)
        hgb = HistGradientBoostingClassifier(
            max_iter=100,
            max_depth=8,
            class_weight='balanced',
            random_state=self.random_state
        )
        
        # 4. Calibrated Linear SVC (to enable predict_proba for soft voting)
        base_svc = LinearSVC(
            C=1.0,
            class_weight='balanced',
            max_iter=2000,
            random_state=self.random_state
        )
        calibrated_svc = CalibratedClassifierCV(estimator=base_svc, cv=3)
        
        self.models = {
            "Random_Forest": rf,
            "CatBoost": cat,
            "HistGradientBoosting": hgb,
            "Linear_SVC": calibrated_svc
        }
        return self.models

    def train_models(self, X_train: np.ndarray, y_train: np.ndarray):
        """Trains base classifiers and constructs the soft-voting ensemble."""
        if not self.models:
            self.initialize_base_models()
            
        trained_estimators = []
        for name, model in self.models.items():
            print(f"[Module 2] Training {name} on {X_train.shape[0]} flow samples...")
            model.fit(X_train, y_train)
            trained_estimators.append((name, model))
            
        print("[Module 2] Constructing Soft Voting Ensemble aggregator...")
        # Soft voting combines class probabilities from each estimator
        self.ensemble = VotingClassifier(
            estimators=trained_estimators,
            voting='soft',
            n_jobs=1  # Sequential or parallel inference
        )
        self.ensemble.fit(X_train, y_train)
        print("[Module 2] Ensemble training completed successfully.")
        return self.ensemble

    def save_models(self, models_dir: str):
        """
        Saves models matching the exact naming convention from the README:
        - EXP_FINAL_Ensemble.pkl
        - EXP_FINAL_Random_Forest.pkl
        - EXP_FINAL_CatBoost.pkl
        - EXP_FINAL_LightGBM_equiv.pkl
        """
        os.makedirs(models_dir, exist_ok=True)
        
        joblib.dump(self.ensemble, os.path.join(models_dir, "EXP_FINAL_Ensemble.pkl"))
        joblib.dump(self.models["Random_Forest"], os.path.join(models_dir, "EXP_FINAL_Random_Forest.pkl"))
        joblib.dump(self.models["CatBoost"], os.path.join(models_dir, "EXP_FINAL_CatBoost.pkl"))
        joblib.dump(self.models["HistGradientBoosting"], os.path.join(models_dir, "EXP_FINAL_LightGBM_equiv.pkl"))
        
        print(f"[Module 2] Serialized all models into {models_dir}")
        print("  ✓ EXP_FINAL_Ensemble.pkl")
        print("  ✓ EXP_FINAL_Random_Forest.pkl")
        print("  ✓ EXP_FINAL_CatBoost.pkl")
        print("  ✓ EXP_FINAL_LightGBM_equiv.pkl")

    def load_ensemble(self, models_dir: str):
        """Loads pre-trained ensemble model from disk."""
        path = os.path.join(models_dir, "EXP_FINAL_Ensemble.pkl")
        if os.path.exists(path):
            self.ensemble = joblib.load(path)
            return self.ensemble
        return None
