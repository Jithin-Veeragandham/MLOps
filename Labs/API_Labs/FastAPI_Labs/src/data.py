import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split

def load_data():
    """
    Load the Titanic dataset and return the features and target values.
    Returns:
        X (numpy.ndarray): The features of the Titanic dataset.
        y (numpy.ndarray): The target values of the Titanic dataset.
    """
    titanic = fetch_openml('titanic', version=1, as_frame=True)
    df = titanic.frame.copy()
    df['age'] = df['age'].fillna(df['age'].median())
    df['fare'] = df['fare'].fillna(df['fare'].median())
    df['sex'] = df['sex'].map({'male': 0, 'female': 1})
    features = ['pclass', 'sex', 'age', 'sibsp', 'parch', 'fare']
    X = df[features].values.astype(float)
    y = (df['survived'] == '1').astype(int).values
    return X, y

def split_data(X, y):
    """
    Split the data into training and testing sets.
    Args:
        X (numpy.ndarray): The features of the dataset.
        y (numpy.ndarray): The target values of the dataset.
    Returns:
        X_train, X_test, y_train, y_test (tuple): The split dataset.
    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=12)
    return X_train, X_test, y_train, y_test