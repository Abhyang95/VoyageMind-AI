import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


# ============================================================
# VoyageMind AI — ML Recommendation Model Training
# ============================================================

print()
print("=" * 60)
print("VoyageMind AI ML Recommendation Model Training")
print("=" * 60)
print()


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.path.join(
    BASE_DIR,
    "data",
    "travel_recommendation_dataset.csv",
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models",
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "travel_recommender.pkl",
)


# ============================================================
# CREATE MODEL DIRECTORY
# ============================================================

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# LOAD DATASET
# ============================================================

print("📂 Loading dataset...")

if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError(
        f"Dataset not found:\n{DATASET_PATH}"
    )

df = pd.read_csv(DATASET_PATH)

print(f"✅ Dataset loaded")
print(f"   Rows: {len(df)}")
print(f"   Columns: {len(df.columns)}")
print()


# ============================================================
# DISPLAY DATASET INFORMATION
# ============================================================

print("📊 Dataset columns:")

for column in df.columns:
    print(f"   • {column}")

print()


# ============================================================
# TARGET
# ============================================================

TARGET_COLUMN = "match_score"


if TARGET_COLUMN not in df.columns:
    raise ValueError(
        f"Target column '{TARGET_COLUMN}' not found in dataset."
    )


# ============================================================
# FEATURES
# ============================================================

FEATURE_COLUMNS = [
    "architecture_score",
    "history_score",
    "food_score",
    "nightlife_score",
    "museums_score",
    "nature_score",
    "shopping_score",
    "adventure_score",
    "average_daily_cost",
    "walkability_score",
    "weather_score",
    "hotel_price",
    "restaurant_price",
    "budget",
    "walking_preference",
]


# ============================================================
# VERIFY FEATURES
# ============================================================

missing_features = [
    column
    for column in FEATURE_COLUMNS
    if column not in df.columns
]

if missing_features:
    raise ValueError(
        "Missing feature columns:\n"
        + "\n".join(f" - {column}" for column in missing_features)
    )


# ============================================================
# PREPARE X AND Y
# ============================================================

X = df[FEATURE_COLUMNS].copy()
y = df[TARGET_COLUMN].copy()


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

X = X.fillna(0)
y = y.fillna(y.mean())


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

print("✂️ Splitting dataset...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
)

print(f"   Training samples: {len(X_train)}")
print(f"   Testing samples:  {len(X_test)}")
print()


# ============================================================
# CREATE RANDOM FOREST MODEL
# ============================================================

print("🌲 Creating Random Forest Regressor...")

model = RandomForestRegressor(
    n_estimators=250,
    max_depth=18,
    min_samples_split=4,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
)


# ============================================================
# TRAIN
# ============================================================

print("🧠 Training model...")

model.fit(
    X_train,
    y_train,
)

print("✅ Model training completed.")
print()


# ============================================================
# PREDICTIONS
# ============================================================

print("🔮 Generating predictions...")

y_pred = model.predict(X_test)


# ============================================================
# EVALUATION
# ============================================================

mae = mean_absolute_error(
    y_test,
    y_pred,
)

mse = mean_squared_error(
    y_test,
    y_pred,
)

rmse = mse ** 0.5

r2 = r2_score(
    y_test,
    y_pred,
)


# ============================================================
# DISPLAY METRICS
# ============================================================

print()
print("=" * 60)
print("MODEL EVALUATION")
print("=" * 60)

print(f"MAE  : {mae:.4f}")
print(f"RMSE : {rmse:.4f}")
print(f"R²   : {r2:.4f}")

print("=" * 60)
print()


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("📈 Feature Importance")
print("-" * 60)

feature_importance = pd.DataFrame(
    {
        "feature": FEATURE_COLUMNS,
        "importance": model.feature_importances_,
    }
)

feature_importance = feature_importance.sort_values(
    by="importance",
    ascending=False,
)

for _, row in feature_importance.iterrows():
    print(
        f"{row['feature']:<25} "
        f"{row['importance']:.4f}"
    )

print()


# ============================================================
# SAVE MODEL
# ============================================================

print("💾 Saving trained model...")

model_package = {
    "model": model,
    "features": FEATURE_COLUMNS,
    "target": TARGET_COLUMN,
}


joblib.dump(
    model_package,
    MODEL_PATH,
)


# ============================================================
# VERIFY MODEL FILE
# ============================================================

if os.path.exists(MODEL_PATH):
    file_size = os.path.getsize(MODEL_PATH)

    print()
    print("✅ Model saved successfully!")
    print(f"📦 Model: {MODEL_PATH}")
    print(f"📏 Size: {file_size / 1024:.2f} KB")
else:
    raise RuntimeError(
        "Model file was not created."
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 60)
print("TRAINING COMPLETE 🚀")
print("=" * 60)

print(f"Dataset       : {len(df)} rows")
print(f"Features      : {len(FEATURE_COLUMNS)}")
print(f"Target        : {TARGET_COLUMN}")
print(f"MAE           : {mae:.4f}")
print(f"RMSE          : {rmse:.4f}")
print(f"R²            : {r2:.4f}")
print(f"Model         : {MODEL_PATH}")

print("=" * 60)
print()