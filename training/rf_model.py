"""
RANDOM FOREST TRAINING & TESTING 
"""

# Import libraries
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt
import pickle

# Load the CSV file
file_path = "./training/dataset.csv"
df = pd.read_csv(file_path)

# Missing data cleaning and label processing

# --- RANDOM FOREST MODEL --- #
# Select features
X = df.drop(columns=['name', 'address', 'label_2x'])
label = df['label_2x']

# Split the dataset (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(X, label, test_size=0.2, random_state=42)

# Define the RandomForestClassifier
rf = RandomForestClassifier(random_state=42, class_weight='balanced')

# Define hyperparameters grid for optimization
param_grid = {
    'n_estimators': [50, 100, 200, 300],
    'max_depth': [None, 10, 20, 30, 40],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

# Perform GridSearchCV to find the best hyperparameters
rf_grid = GridSearchCV(rf, param_grid, cv=5, n_jobs=-1, scoring='f1')
rf_grid.fit(X_train, y_train)

# Train the best model found
rf_trained = rf_grid.best_estimator_
rf_trained.fit(X_train, y_train)

# Make predictions on the test set
y_pred = rf_trained.predict(X_test)

# ==== REPORT ====
def print_report(name, y_true, y_pred):
    print(f"\n{name} PERFORMANCE")
    print("---------------------------")
    print(f"Accuracy:  {accuracy_score(y_true, y_pred):.4f}")
    print(f"Precision: {precision_score(y_true, y_pred):.4f}")
    print(f"Recall:    {recall_score(y_true, y_pred):.4f}")
    print(f"F1 Score:  {f1_score(y_true, y_pred):.4f}")

print_report("Random Forest", y_test, y_pred)

# --- DATA VISUALIZATION --- #
# Visualize first tree
plt.figure(figsize=(20, 10))
plot_tree(rf_trained.estimators_[0], feature_names=X.columns, filled=True, rounded=True)
plt.show()

# Features importance chart
importances = rf_trained.feature_importances_
features = X.columns
importance_df = pd.DataFrame({'Feature': features, 'Importance': importances})
importance_df = importance_df.sort_values(by='Importance', ascending=False)

plt.figure(figsize=(10, 6))
plt.barh(importance_df['Feature'], importance_df['Importance'])
plt.xlabel("Importanza")
plt.title("Importanza delle feature nella Random Forest")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

# --- PICKEL THE TRAINED MODEL --- #
# Save the trained model
def save_model(model, filename="patricio.pkl"):
    with open(filename, 'wb') as file:
        pickle.dump(model, file)
    print(f"Model saved as {filename}")

# Load the trained model
def load_model(filename="patricio.pkl"):
    with open(filename, 'rb') as file:
        model = pickle.load(file)
    print(f"Model loaded from {filename}")
    return model

# Save the model
save_model(rf_trained)
# Load the model
rf_trained = load_model()
