"""
legacy_v1/src: baseline_models.py
Initial unoptimized baseline classifiers before modular pipeline architecture.
"""
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

def get_baselines():
    return {
        "LogisticRegression": LogisticRegression(max_iter=500),
        "DecisionTree": DecisionTreeClassifier(max_depth=10)
    }
