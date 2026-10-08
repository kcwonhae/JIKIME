import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)


def get_paths():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    features_path = os.path.join(project_root, "data", "features.csv")
    model_path = os.path.join(project_root, "model", "agentguard_model.pkl")
    importance_path = os.path.join(project_root, "model", "feature_importance.csv")

    return features_path, model_path, importance_path


def main():
    features_path, model_path, importance_path = get_paths()

    if not os.path.exists(features_path):
        print("features.csv not found.")
        print(f"Expected path: {features_path}")
        return

    df = pd.read_csv(features_path)

    print("===================================")
    print(" AgentGuard Model Training v2")
    print("===================================")
    print(f"Total rows: {len(df)}")

    # 정답 누출 가능성이 큰 risk 기반 feature 제거
    excluded_features = [
        "session_id",
        "agent_type",
        "label",
        "mean_risk",
        "max_risk",
        "risk_escalation",
        "risk_slope",
    ]

    feature_columns = [
        col for col in df.columns
        if col not in excluded_features
    ]

    X = df[feature_columns]
    y = df["label"]

    print("\nFeatures used:")
    for feature in feature_columns:
        print(f" - {feature}")

    print("\nExcluded:")
    for feature in excluded_features:
        if feature in df.columns:
            print(f" - {feature}")

    print("\nClass distribution:")
    print(y.value_counts().sort_index())

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print(f"\nTrain size: {len(X_train)}")
    print(f"Test size : {len(X_test)}")

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
        max_depth=8,
        min_samples_leaf=3
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print("\n===================================")
    print(" Evaluation")
    print("===================================")
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1-score : {f1:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["Normal", "Malicious"],
            zero_division=0
        )
    )

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    importance_df = pd.DataFrame({
        "feature": feature_columns,
        "importance": model.feature_importances_
    }).sort_values(
        by="importance",
        ascending=False
    )

    print("\n===================================")
    print(" Feature Importance")
    print("===================================")

    for _, row in importance_df.iterrows():
        print(f"{row['feature']:<25} {row['importance']:.4f}")

    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    model_bundle = {
        "model": model,
        "features": feature_columns
    }

    joblib.dump(model_bundle, model_path)

    importance_df.to_csv(
        importance_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n===================================")
    print(" Saved")
    print("===================================")
    print(f"Model -> {model_path}")
    print(f"Feature importance -> {importance_path}")


if __name__ == "__main__":
    main()
