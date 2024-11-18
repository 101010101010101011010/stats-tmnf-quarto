
import sklearn
import numpy as np
import pandas as pd
import sklearn.metrics
import xgboost as xgb
import shap

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import OrdinalEncoder

###################################

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

###################################

# Constants
FILE_NAME = "./collected-data/flat-replay-data-5rep.csv"
SEED = 19842

# load data
full_dataset = pd.read_csv(FILE_NAME) # For Pandas
full_dataset = full_dataset.astype({"Tag": str})

mappingNumToCat = {
  "0": "Normal",
  # "Stunt": 1,
  # "Maze": 2,
  "3": "Offroad",
  # "Laps": 4,
  "5": "Fullspeed",
  "6": "LOL",
  "7": "Tech",
  "8": "SpeedTech",
  # "RPG": 9,
  "10": "PressForward",
  # "Trial": 11,
  "12": "Grass",
}
  
dataset = full_dataset.copy()

dataset['Tag'] = dataset['Tag'].replace(mappingNumToCat) # Map to categorical
  # if removed is not None: dataset = dataset.drop(removed, axis=1)
  # print(dataset.head)

print(dataset)

# split data into X and y
X, y = dataset.drop("Tag", axis=1), dataset[['Tag']] # For Pandas
# X = dataset[:,1:]
# y = dataset[:,0]

# Encode y to numeric
y_encoded = OrdinalEncoder().fit_transform(y)

# split data into train and test sets
# test_size = 0.15

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, random_state=SEED, stratify=y_encoded)

# Dummy model #####################################

if True:
  print("\nStart dummy model")
  dummy_model = sklearn.dummy.DummyClassifier()
  dummy_model.fit(X, y_encoded)
  
  y_pred = dummy_model.predict(X_test)
  print(sklearn.metrics.confusion_matrix(y_test, y_pred))
  print(sklearn.metrics.classification_report(y_test, y_pred))
  
  # print(dummy_model.predict(X))
  print("Dummy best %: ", dummy_model.score(X, y_encoded))

# Linear regression model #########################

if True:
  print("\nStart linear regression model")
  from sklearn.linear_model import LogisticRegression
  
  logistic_classifier = LogisticRegression(max_iter=10000, solver="liblinear")
  logistic_classifier.fit(X_train, y_train)
  y_pred = logistic_classifier.predict(X_test)
  print(sklearn.metrics.confusion_matrix(y_test, y_pred))
  print(sklearn.metrics.classification_report(y_test, y_pred))

  count_correct = 0
  for i in range(len(y_test)):
    if (y_pred[i] == y_test[i]):
      count_correct += 1
  percent_correct = count_correct / len(y_test)

  print("Linear Regression %: ", percent_correct)

# XGBoost Model ###################################

if True:
  print("\nStart XGBoost Model")
  # Create classification matrices
  dtrain_clf = xgb.DMatrix(X_train, y_train, enable_categorical=True)
  dtest_clf = xgb.DMatrix(X_test, y_test, enable_categorical=True)

  params = {
    "objective": "multi:softmax",
    "tree_method": "hist",
    "num_class": 8,
    "device": "cuda",
    "max_depth": 5,
    "eval_metric": "mlogloss",
  }
  n_rounds = 100

  results = xgb.cv(
    params, dtrain_clf,
    num_boost_round=n_rounds,
    nfold=2,
    metrics=["mlogloss", "auc", "merror"]
  )

  print("Average test-auc-mean: ", results['test-auc-mean'].sum() / results['test-auc-mean'].count())

  print("Best test-auc-mean: ", results['test-auc-mean'].max())

  # GPU accelerated training
  watchlist = [(dtrain_clf, "train"), (dtest_clf, "validation")]
  evals_result = {}
  model = xgb.train(
    params,
    dtrain_clf,
    n_rounds,
    evals=watchlist,
    evals_result=evals_result,
    early_stopping_rounds=10,
    verbose_eval=10,
  )

  y_pred = model.predict(dtest_clf)

  print(sklearn.metrics.confusion_matrix(y_test, y_pred))
  print(sklearn.metrics.classification_report(y_test, y_pred))

  count_correct = 0
  for i in range(len(y_test)):
    if (y_pred[i] == y_test[i]):
      count_correct += 1
  percent_correct = count_correct / len(y_test)

  print("XGBoost %: ", percent_correct)




  # Compute shap values using GPU with xgboost
  model.set_param({"device": "cuda"})
  shap_values = model.predict(dtrain_clf, pred_contribs=True)

  # Compute shap interaction values using GPU
  shap_interaction_values = model.predict(dtrain_clf, pred_interactions=True)

  # shap will call the GPU accelerated version as long as the device parameter is set to "cuda"
  explainer = shap.TreeExplainer(model)
  shap_values = explainer.shap_values(X)

  # Show a summary of feature importance
  shap.summary_plot(shap_values, features=X, feature_names=X.columns, plot_type="bar", max_display=5)