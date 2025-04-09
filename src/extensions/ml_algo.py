#ml_algo.py

import sys
from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

if getattr(sys, 'frozen', False):  # Running as a PyInstaller .exe
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent  # Running as a normal script

CSV_PATH = BASE_DIR / "dataset" / "av.csv"

print(f"🔍 Checking database at: {CSV_PATH}")

def get_ml_results(input_values):
    input_values = np.array([input_values])
    av_df = pd.read_csv(CSV_PATH)

    #print(av_df.head())

    x = av_df.drop('action', axis = 1)
    y = av_df.action

    #SPLIT INTO TEST AND TRAIN
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.25, random_state = 42)
    
    #MODEL CREATION
    model_tree = DecisionTreeClassifier()
    model_tree.fit(x_train, y_train)
    #print("Model Trained")

    #PREDICTION
    y_pred = model_tree.predict(input_values)

    # y_pred = model_tree.predict(X_test)
    #print("Accuarcy Score of Model : ", accuracy_score(y_test, y_pred))

    return y_pred[0]