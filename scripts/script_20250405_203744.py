# Importing required libraries
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

# Step 1: Create a synthetic dataset
# Features: Budget, Number of Action Scenes, Humor Level, Star Power
# Target: Movie Success (1 = Successful, 0 = Not Successful)
np.random.seed(42)
data = {
    "Budget (in millions)": np.random.randint(10, 300, 200),  # Movie budget
    "Action Scenes": np.random.randint(1, 20, 200),          # Number of action scenes
    "Humor Level": np.random.randint(1, 10, 200),            # Humor level (1-10)
    "Star Power": np.random.randint(1, 5, 200),              # Star power (1-5)
    "Success": np.random.choice([0, 1], 200, p=[0.4, 0.6])   # Movie success (binary target)
}

# Convert the data into a DataFrame
df = pd.DataFrame(data)

# Step 2: Split the dataset into training and testing sets
X = df.drop("Success", axis=1)  # Features
y = df["Success"]               # Target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 3: Train the Random Forest Classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Step 4: Make predictions
y_pred = model.predict(X_test)

# Step 5: Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)

print("Accuracy of Random Forest Classifier:", accuracy)
print("Confusion Matrix:\n", conf_matrix)

# Step 6: Feature Importance
feature_importances = model.feature_importances_
print("\nFeature Importances:")
for feature, importance in zip(X.columns, feature_importances):
    print(f"{feature}: {importance:.2f}")