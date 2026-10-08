import json
import os
import sys
import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from features.extract_features import extract_session_features

UNSEEN_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "unseen_trajectories.json"
)

MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "model",
    "agentguard_model.pkl"
)


def main():
    if not os.path.exists(UNSEEN_PATH):
        print("unseen_trajectories.json not found.")
        print("Run features/unseen_test_generator.py first.")
        return

    if not os.path.exists(MODEL_PATH):
        print("agentguard_model.pkl not found.")
        return

    with open(UNSEEN_PATH, "r", encoding="utf-8") as f:
        sessions = json.load(f)

    rows = []

    for session in sessions:
        row = extract_session_features(session)
        if row is not None:
            rows.append(row)

    df = pd.DataFrame(rows)

    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    feature_columns = bundle["features"]

    X = df[feature_columns]
    y_true = df["label"]

    y_pred = model.predict(X)

    if hasattr(model, "predict_proba"):
        malicious_prob = model.predict_proba(X)[:, 1]
        df["malicious_probability"] = malicious_prob

    df["prediction"] = y_pred

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    print("===================================")
    print(" Unseen Test Evaluation")
    print("===================================")
    print(f"Total samples: {len(df)}")
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-score : {f1:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_true,
            y_pred,
            target_names=["Normal", "Malicious"],
            zero_division=0
        )
    )

    print("Confusion Matrix:")
    print(confusion_matrix(y_true, y_pred))

    result_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "unseen_results.csv"
    )

    df.to_csv(
        result_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nDetailed results -> {result_path}")


if __name__ == "__main__":
    main()
