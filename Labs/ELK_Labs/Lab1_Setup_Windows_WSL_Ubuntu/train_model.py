import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

data = load_iris()
X, y = data.data, data.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LogisticRegression(max_iter=300)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
f1 = f1_score(y_test, model.predict(X_test), average="weighted")
print(f"Accuracy: {accuracy:.4f} | F1: {f1:.4f}")

joblib.dump(model, "iris_model.pkl")
print("Model saved to iris_model.pkl")
