"""
Module 3: Security Analytics & Explainable AI (XAI)
SentinelAI - Multi-Class IoT Intrusion Detection System

Responsible for:
- Full evaluation matrix: Accuracy, Precision, Recall, Macro F1, Confusion Matrix
- Latency profiling per sample
- Dynamic SHAP feature attribution calculation for streaming packet inspection
"""

import time
import json
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import shap

class SecurityAnalyticsEvaluator:
    def __init__(self, feature_names=None):
        self.feature_names = feature_names or []
        self.explainer = None
        
    def profile_latency(self, model, X_sample: np.ndarray, n_runs: int = 50) -> float:
        """Profiles average inference latency in milliseconds."""
        single_row = X_sample[:1]
        # Warmup
        for _ in range(5):
            _ = model.predict_proba(single_row)
            
        start = time.perf_counter()
        for _ in range(n_runs):
            _ = model.predict_proba(single_row)
        end = time.perf_counter()
        
        avg_ms = ((end - start) / n_runs) * 1000.0
        return round(avg_ms, 3)

    def evaluate_all_models(self, models_dict: dict, ensemble, X_test: np.ndarray, y_test: np.ndarray, target_names: list) -> dict:
        """Evaluates all candidate models and the ensemble."""
        print("[Module 3] Running full evaluation matrix on hold-out test set...")
        results = {}
        
        all_eval_targets = list(models_dict.items()) + [("Voting_Ensemble", ensemble)]
        for name, model in all_eval_targets:
            y_pred = model.predict(X_test)
            latency_ms = self.profile_latency(model, X_test)
            
            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, average='macro', zero_division=0))
            rec = float(recall_score(y_test, y_pred, average='macro', zero_division=0))
            f1 = float(f1_score(y_test, y_pred, average='macro', zero_division=0))
            
            cm = confusion_matrix(y_test, y_pred).tolist()
            
            results[name] = {
                "accuracy": round(acc * 100, 2),
                "precision": round(prec * 100, 2),
                "recall": round(rec * 100, 2),
                "f1_score": round(f1 * 100, 2),
                "latency_ms": latency_ms,
                "confusion_matrix": cm
            }
            print(f"  [{name}] Accuracy: {results[name]['accuracy']}% | F1: {results[name]['f1_score']}% | Latency: {latency_ms} ms")
            
        return results

    def initialize_shap_explainer(self, background_model, X_background: np.ndarray):
        """Initializes TreeSHAP explainer for dynamic local attribution."""
        try:
            print("[Module 3] Initializing TreeSHAP explainer on background samples...")
            self.explainer = shap.TreeExplainer(background_model)
        except Exception as e:
            print(f"[Module 3] Standard TreeExplainer fallback: {e}")
            sample_bg = shap.sample(X_background, 50)
            self.explainer = shap.Explainer(background_model.predict_proba, sample_bg)

    def explain_sample(self, model, x_scaled: np.ndarray, predicted_class_idx: int = 1, top_k: int = 5) -> list:
        """
        Calculates dynamic local feature attributions for a single network flow sample.
        Returns list of {'feature': name, 'importance': val}.
        """
        if self.explainer is not None:
            try:
                shap_vals = self.explainer.shap_values(x_scaled.reshape(1, -1))
                if isinstance(shap_vals, list):
                    # Multi-class list
                    vals = np.abs(shap_vals[predicted_class_idx][0])
                elif len(shap_vals.shape) == 3:
                    vals = np.abs(shap_vals[0, :, predicted_class_idx])
                else:
                    vals = np.abs(shap_vals[0])
            except Exception:
                vals = self._heuristic_feature_attribution(model, x_scaled)
        else:
            vals = self._heuristic_feature_attribution(model, x_scaled)
            
        # Normalize to 0.0 - 1.0 range
        max_val = np.max(vals) if np.max(vals) > 0 else 1.0
        normalized_vals = vals / max_val
        
        # Rank features
        ranked_indices = np.argsort(normalized_vals)[::-1][:top_k]
        top_features = []
        for idx in ranked_indices:
            feat_name = self.feature_names[idx] if idx < len(self.feature_names) else f"Feature_{idx}"
            top_features.append({
                "feature": feat_name,
                "importance": round(float(normalized_vals[idx]), 3)
            })
            
        return top_features

    def _heuristic_feature_attribution(self, model, x_scaled: np.ndarray) -> np.ndarray:
        """
        Fast mathematical perturbation-based attribution for sub-millisecond line-rate serving.
        """
        base_probs = model.predict_proba(x_scaled.reshape(1, -1))[0]
        top_class = np.argmax(base_probs)
        base_confidence = base_probs[top_class]
        
        attributions = np.zeros(len(x_scaled))
        for j in range(len(x_scaled)):
            perturbed = x_scaled.copy()
            perturbed[j] = 0.0  # Zero out feature
            new_probs = model.predict_proba(perturbed.reshape(1, -1))[0]
            attributions[j] = np.abs(base_confidence - new_probs[top_class])
            
        return attributions
