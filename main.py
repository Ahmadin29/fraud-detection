# -*- coding: utf-8 -*-
"""Fraud Detections.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1gg_TZoCLIL4ThSY0TQbsnDMKnqyPYepk
"""

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

data = pd.read_csv('/content/drive/MyDrive/fraud_data/fraudTrain.csv')

data

data.info()

for col in data.columns:
  print(col, data[col].nunique())

def calculate_age(birthdate,transaction_date):
    age = transaction_date.year - birthdate.year - ((transaction_date.month, transaction_date.day) < (birthdate.month, birthdate.day))
    return age

def classify_age(age):
    if age < 21:
        return 'young'
    elif age < 35:
        return 'middle'
    elif age < 55:
        return 'old'
    else:
        return 'oldest'

import math

def calculate_distance(merchant_lat,merchant_long,holder_lat,holder_long):
    lat1, lon1, lat2, lon2 = map(math.radians, [merchant_lat, merchant_long, holder_lat, holder_long])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371
    return c * r

def classify_distance(distance):
    if distance < 50:
        return 'high'
    elif distance < 110:
        return 'medium'
    else:
        return 'long'

def classify_hour(hour):
    if hour in [22, 23, 0, 1, 2, 3]:
        return 'high'
    elif hour in [14, 18, 19, 13, 15, 17, 16, 21, 12, 20]:
        return 'medium'
    else:
        return 'low'

def parse_feature(data_to_parse):
  data_to_parse['trans_date_trans_time'] = pd.to_datetime(data_to_parse['trans_date_trans_time'])
  data_to_parse['dob'] = pd.to_datetime(data_to_parse['dob'])
  data_to_parse['time'] = data_to_parse['trans_date_trans_time'].dt.time
  data_to_parse['date'] = data_to_parse['trans_date_trans_time'].dt.date
  data_to_parse['year'] = data_to_parse['trans_date_trans_time'].dt.year
  data_to_parse['month'] = data_to_parse['trans_date_trans_time'].dt.month
  data_to_parse['day'] = data_to_parse['trans_date_trans_time'].dt.day
  data_to_parse['dayofweek'] = data_to_parse['trans_date_trans_time'].dt.dayofweek
  data_to_parse['hour'] = data_to_parse['trans_date_trans_time'].dt.hour
  data_to_parse['minute'] = data_to_parse['trans_date_trans_time'].dt.minute
  data_to_parse['second'] = data_to_parse['trans_date_trans_time'].dt.second

  data_to_parse['age'] = data_to_parse.apply(lambda row: calculate_age(row['dob'], row['trans_date_trans_time']), axis=1)
  data_to_parse['age_class'] = data_to_parse.apply(lambda row: classify_age(row['age']), axis=1)

  data_to_parse['distance'] = data_to_parse.apply(lambda row: calculate_distance(row['merch_lat'],row['merch_long'],row['lat'],row['long']), axis=1)
  data_to_parse['distance_risk_class'] = data_to_parse.apply(lambda row: classify_distance(row['distance']), axis=1)

  data_to_parse['hour_risk_class'] = data_to_parse['hour'].apply(classify_hour)

  data_to_parse['cc_order_index'] = data_to_parse.groupby(['cc_num', 'day']).cumcount() + 1
  data_to_parse['merchant'] = data_to_parse['merchant'].str.replace('fraud_', '', regex=False)
  data_to_parse['category_fraud_rate'] = data_to_parse.groupby('category')['is_fraud'].transform('mean')
  data_to_parse['merchant_fraud_rate'] = data_to_parse.groupby('merchant')['is_fraud'].transform('mean')
  data_to_parse['cc_fraud_rate'] = data_to_parse.groupby('cc_num')['is_fraud'].transform('mean')
  data_to_parse['job_fraud_rate'] = data_to_parse.groupby('job')['is_fraud'].transform('mean')
  data_to_parse = pd.get_dummies(data_to_parse, columns=['hour_risk_class','distance_risk_class','age_class'],dtype=int)
  return data_to_parse

parsed_data = parse_feature(data)

parsed_data = parsed_data.drop(columns=[
    'Unnamed: 0',
    'first',
    'last',
    'gender',
    'street',
    'zip',
    'state',
    'city_pop',
    'trans_num',
    'unix_time',
    'trans_date_trans_time',
    'city',
    'date',
    'year',
    'month',
    'day',
    'dob',
    'time',
    'second',
    'minute',
    'lat',
    'long',
    'merch_lat',
    'merch_long',
    'merchant',
    'category',
    'job',
    'cc_num',
])

fraud_data = parsed_data[parsed_data['is_fraud'] == 1]

for col in fraud_data.columns:
  if fraud_data[col].dtype != 'object':
    with sns.axes_style('darkgrid'):
      fig, ax = plt.subplots(1, 2, figsize=(20, 6))
      sns.histplot(data=fraud_data, x=col, kde=True, ax=ax[0])
      sns.boxplot(data=fraud_data, x=col, ax=ax[1])
    plt.show()

parsed_data.info()

corr = parsed_data.corr()
plt.subplots(figsize=(20, 20))
sns.heatmap(corr, annot=True)
plt.show()

from mlxtend.preprocessing import minmax_scaling
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import StandardScaler

features  = parsed_data.drop(columns=['is_fraud'])
target    = parsed_data['is_fraud']

features_scaled = minmax_scaling(features, columns=features.columns)

rob_scaler = RobustScaler()
features_scaled = rob_scaler.fit_transform(features_scaled)

sta_scaler = StandardScaler()
features_scaled = sta_scaler.fit_transform(features_scaled)

features

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier
from sklearn.metrics import confusion_matrix
from sklearn.utils import class_weight

class_weights = class_weight.compute_class_weight('balanced',
                                                 classes=np.unique(target),
                                                 y=target)
class_weights

X_train, X_test, y_train, y_test = train_test_split(features_scaled, target, test_size = 0.2, random_state = 25)

def modeling_xgboost(X_train, y_train):
  model = XGBClassifier(
    objective='binary:logistic',  # For binary classification
    eval_metric='logloss'          # Evaluation metric to monitor during training
  )

  model.fit(X_train, y_train)

  return model

from sklearn.ensemble import AdaBoostClassifier
def modeling_adaboost(X_train, y_train):
  model = AdaBoostClassifier(n_estimators=100)
  model.fit(X_train, y_train)
  return model

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import tensorflow as tf
from keras import backend as K
import random

# Set seeds
np.random.seed(42)
tf.random.set_seed(42)
random.seed(42)

def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))


def modeling_mlp(X_train, y_train):
  model = Sequential()
  model.add(Dense(32, activation=tf.keras.layers.LeakyReLU(alpha=0.01), input_shape=[len(features.keys())]))
  model.add(Dense(16, activation=tf.keras.layers.LeakyReLU(alpha=0.01)))
  model.add(Dense(16, activation=tf.keras.layers.LeakyReLU(alpha=0.0125)))
  model.add(Dense(8, activation=tf.keras.layers.LeakyReLU(alpha=0.0125)))
  model.add(Dense(8, activation=tf.keras.layers.LeakyReLU(alpha=0.015)))
  model.add(Dense(4, activation=tf.keras.layers.LeakyReLU(alpha=0.015)))
  model.add(Dense(4, activation=tf.keras.layers.LeakyReLU(alpha=0.015)))
  model.add(Dense(1, activation='sigmoid'))

  model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy', f1_m, precision_m, recall_m])
  history = model.fit(X_train, y_train, epochs=1000, batch_size=20000, validation_split=0.2, verbose=0)

  return model, history

from sklearn.linear_model import LogisticRegression
def modeling_logistic(X_train, y_train):
  model = LogisticRegression(solver='saga',penalty='l1', C=0.1)
  model.fit(X_train, y_train)
  return model

from sklearn.ensemble import RandomForestClassifier
def modeling_randomforest(X_train, y_train):
  model = RandomForestClassifier(n_estimators=100, random_state=42)
  model.fit(X_train, y_train)
  return model

def max_metric(history):
  max_precission = max(history.history['precision_m'])
  max_recall = max(history.history['recall_m'])
  max_f1 = max(history.history['f1_m'])
  max_val_precission = max(history.history['val_precision_m'])
  max_val_recall = max(history.history['val_recall_m'])
  max_val_f1 = max(history.history['val_f1_m'])

  print('max_precission -',max_precission)
  print('max_recall -',max_recall)
  print('max_f1 -',max_f1)
  print('max_val_precission -',max_val_precission)
  print('max_val_recall -',max_val_recall)
  print('max_val_f1 -',max_val_f1)

def evaluate_model_mlp(model,X_test, y_test):
  y_pred_prob = model.predict(X_test)
  threshold = 0.5
  y_pred = (y_pred_prob >= threshold).astype(int)
  print(classification_report(y_test, y_pred))

  confusion_mtx = confusion_matrix(y_test, y_pred)
  f,ax = plt.subplots(figsize=(6, 6))
  sns.heatmap(confusion_mtx, annot=True, linewidths=0.01,cmap="Greens",linecolor="gray", fmt= '.1f',ax=ax)
  plt.xlabel("Predicted Label")
  plt.ylabel("True Label")
  plt.title("Confusion Matrix")
  plt.show()

  return classification_report(y_test, y_pred), confusion_mtx

def evaluate_model(model,X_test, y_test):
  y_pred = model.predict(X_test)
  print(classification_report(y_test, y_pred))

  confusion_mtx = confusion_matrix(y_test, y_pred)
  f,ax = plt.subplots(figsize=(6, 6))
  sns.heatmap(confusion_mtx, annot=True, linewidths=0.01,cmap="Greens",linecolor="gray", fmt= '.1f',ax=ax)
  plt.xlabel("Predicted Label")
  plt.ylabel("True Label")
  plt.title("Confusion Matrix")
  plt.show()

  return classification_report(y_test, y_pred), confusion_mtx

def train_and_evaluate(features_train, target_train):
  print("------ MLP Modeling -------")
  print("------ Modeling -------")
  mlp_modeling , history = modeling_mlp(features_train, target_train)
  print("------ Train Evaluate -------")
  evaluate_model_mlp(mlp_modeling,features_train, target_train)
  print("------ Test Evaluate -------")
  mlp_classification_report,mlp_confusion_mtx = evaluate_model_mlp(mlp_modeling,X_test, y_test)
  print("--------------------------------\n\n\n")



  print("------ XG Boost Modeling -------")
  print("------ Modeling -------")
  XGB_model = modeling_xgboost(features_train, target_train)
  print("------ Train Evaluate -------")
  evaluate_model(XGB_model,features_train, target_train)
  print("------ Test Evaluate -------")
  xgb_classification_report,xgb_confusion_mtx = evaluate_model(XGB_model,X_test, y_test)
  print("--------------------------------\n\n\n")



  print("------ Logistic Regression Modeling -------")
  print("------ Modeling -------")
  log_model = modeling_logistic(features_train, target_train)
  print("------ Train Evaluate -------")
  evaluate_model(log_model,features_train, target_train)
  print("------ Test Evaluate -------")
  log_classification_report,log_confusion_mtx = evaluate_model(log_model,X_test, y_test)
  print("--------------------------------\n\n\n")



  print("------ Random Forest Modeling -------")
  print("------ Modeling -------")
  rf_model = modeling_randomforest(features_train, target_train)
  print("------ Train Evaluate -------")
  evaluate_model(rf_model,features_train, target_train)
  print("------ Test Evaluate -------")
  rf_classification_report,rf_confusion_mtx = evaluate_model(rf_model,X_test, y_test)
  print("--------------------------------\n\n\n")

  return {
      "mlp":{
          "model": mlp_modeling,
          "classification_report": mlp_classification_report,
          "confusion_mtx": mlp_confusion_mtx
      },
      "xgb":{
          "model": XGB_model,
          "classification_report": xgb_classification_report,
          "confusion_mtx": xgb_confusion_mtx
      },
      "log":{
          "model": log_model,
          "classification_report": log_classification_report,
          "confusion_mtx": log_confusion_mtx
      },
      "rf":{
          "model": rf_model,
          "classification_report": rf_classification_report,
          "confusion_mtx": rf_confusion_mtx
      }
  }

default_data_results = train_and_evaluate(X_train, y_train)

from imblearn.over_sampling import RandomOverSampler
ros = RandomOverSampler(random_state=42)
X_over, y_over = ros.fit_resample(X_train, y_train)

ROS_data_results = train_and_evaluate(X_over, y_over)

from imblearn.under_sampling import RandomUnderSampler
rus = RandomUnderSampler(random_state=42)
X_under, y_under = rus.fit_resample(X_train, y_train)

RUS_data_results = train_and_evaluate(X_under, y_under)

from imblearn.over_sampling import SMOTE

smote = SMOTE(random_state=42)
X_smote, y_smote = smote.fit_resample(X_train, y_train)

SMOTE_data_results = train_and_evaluate(X_smote, y_smote)

for key in default_data_results.keys():
  print(f"=======-------      {key} Default      ------========\n")
  print(default_data_results[key]['classification_report'])
  print(f"=======-------#################------========\n\n\n")

for key in ROS_data_results.keys():
  print(f"=======-------      {key} ROS      ------========\n")
  print(ROS_data_results[key]['classification_report'])
  print(f"=======-------#################------========\n\n\n")

for key in RUS_data_results.keys():
  print(f"=======-------      {key} RUS      ------========\n")
  print(RUS_data_results[key]['classification_report'])
  print(f"=======-------#################------========\n\n\n")

for key in SMOTE_data_results.keys():
  print(f"=======-------      {key} SMOTE      ------========\n")
  print(SMOTE_data_results[key]['classification_report'])
  print(f"=======-------#################------========\n\n\n")

def plot_cm(cm,key,data):
  f,ax = plt.subplots(figsize=(3, 3))
  sns.heatmap(cm, annot=True, linewidths=0.01,cmap="Greens",linecolor="gray", fmt= '.1f',ax=ax)
  plt.xlabel("Predicted Label")
  plt.ylabel("True Label")
  plt.title(f"Confusion Matrix {key} {data}")
  plt.show()

for key in default_data_results.keys():
  confusion_mtx=default_data_results[key]['confusion_mtx']
  plot_cm(confusion_mtx,key,'default')

for key in ROS_data_results.keys():
  confusion_mtx=ROS_data_results[key]['confusion_mtx']
  plot_cm(confusion_mtx,key,'ROS')

for key in RUS_data_results.keys():
  confusion_mtx=RUS_data_results[key]['confusion_mtx']
  plot_cm(confusion_mtx,key,'RUS')

for key in SMOTE_data_results.keys():
  confusion_mtx=SMOTE_data_results[key]['confusion_mtx']
  plot_cm(confusion_mtx,key,'SMOTE')

from sklearn.metrics import f1_score, make_scorer

best_model = default_data_results['xgb']['model']

param_grid = {
    'n_estimators': [5, 10, 15],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 4, 5],
}

f1_scorer = make_scorer(f1_score)

grid_search = GridSearchCV(estimator=best_model, param_grid=param_grid, scoring=f1_scorer, cv=2, verbose=1, n_jobs=-1)
grid_search.fit(X_train, y_train)

best_xgb = grid_search.best_estimator_

y_pred = best_xgb.predict(X_test)

print(classification_report(y_test, y_pred))

confusion_mtx = confusion_matrix(y_test, y_pred)
f,ax = plt.subplots(figsize=(6, 6))
sns.heatmap(confusion_mtx, annot=True, linewidths=0.01,cmap="Greens",linecolor="gray", fmt= '.1f',ax=ax)
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.title("Confusion Matrix")
plt.show()

data_test = pd.read_csv('/content/drive/MyDrive/fraud_data/fraudTest.csv')

parsed_test_data = parse_feature(data_test)

parsed_test_data = parsed_test_data.drop(columns=[
    'Unnamed: 0',
    'first',
    'last',
    'gender',
    'street',
    'zip',
    'state',
    'city_pop',
    'trans_num',
    'unix_time',
    'trans_date_trans_time',
    'city',
    'date',
    'year',
    'month',
    'day',
    'dob',
    'time',
    'second',
    'minute',
    'lat',
    'long',
    'merch_lat',
    'merch_long',
    'merchant',
    'category',
    'job',
    'cc_num',
])

fraud_data = parsed_test_data[parsed_test_data['is_fraud'] == 1]

for col in fraud_data.columns:
  if fraud_data[col].dtype != 'object':
    with sns.axes_style('darkgrid'):
      fig, ax = plt.subplots(1, 2, figsize=(20, 6))
      sns.histplot(data=fraud_data, x=col, kde=True, ax=ax[0])
      sns.boxplot(data=fraud_data, x=col, ax=ax[1])
    plt.show()

features = parsed_test_data.drop(columns=['is_fraud'])
target = parsed_test_data['is_fraud']

features_scaled = minmax_scaling(features, columns=features.columns)

rob_scaler = RobustScaler()
features_scaled = rob_scaler.fit_transform(features_scaled)

sta_scaler = StandardScaler()
features_scaled = sta_scaler.fit_transform(features_scaled)

for key in default_data_results.keys():

  print(f"=======-------      {key} Default      ------========\n")
  model = default_data_results[key]['model']
  test_pred = model.predict(features_scaled)
  if key == 'mlp':
    test_pred = (test_pred >= 0.5).astype(int)

  print(classification_report(target, test_pred))

  confusion_mtx = confusion_matrix(target, test_pred)
  f,ax = plt.subplots(figsize=(6, 6))
  sns.heatmap(confusion_mtx, annot=True, linewidths=0.01,cmap="Greens",linecolor="gray", fmt= '.1f',ax=ax)
  plt.xlabel("Predicted Label")
  plt.ylabel("True Label")
  plt.title("Confusion Matrix")
  plt.show()
  print(f"=======-------#################------========\n\n\n")

for key in ROS_data_results.keys():

  print(f"=======-------      {key} ROS      ------========\n")
  model = ROS_data_results[key]['model']
  test_pred = model.predict(features_scaled)
  if key == 'mlp':
    test_pred = (test_pred >= 0.5).astype(int)

  print(classification_report(target, test_pred))

  confusion_mtx = confusion_matrix(target, test_pred)
  f,ax = plt.subplots(figsize=(6, 6))
  sns.heatmap(confusion_mtx, annot=True, linewidths=0.01,cmap="Greens",linecolor="gray", fmt= '.1f',ax=ax)
  plt.xlabel("Predicted Label")
  plt.ylabel("True Label")
  plt.title("Confusion Matrix")
  plt.show()
  print(f"=======-------#################------========\n\n\n")

for key in RUS_data_results.keys():

  print(f"=======-------      {key} RUS      ------========\n")
  model = RUS_data_results[key]['model']
  test_pred = model.predict(features_scaled)
  if key == 'mlp':
    test_pred = (test_pred >= 0.5).astype(int)

  print(classification_report(target, test_pred))

  confusion_mtx = confusion_matrix(target, test_pred)
  f,ax = plt.subplots(figsize=(6, 6))
  sns.heatmap(confusion_mtx, annot=True, linewidths=0.01,cmap="Greens",linecolor="gray", fmt= '.1f',ax=ax)
  plt.xlabel("Predicted Label")
  plt.ylabel("True Label")
  plt.title("Confusion Matrix")
  plt.show()
  print(f"=======-------#################------========\n\n\n")

for key in SMOTE_data_results.keys():

  print(f"=======-------      {key} SMOTE      ------========\n")
  model = SMOTE_data_results[key]['model']
  test_pred = model.predict(features_scaled)
  if key == 'mlp':
    test_pred = (test_pred >= 0.5).astype(int)

  print(classification_report(target, test_pred))

  confusion_mtx = confusion_matrix(target, test_pred)
  f,ax = plt.subplots(figsize=(6, 6))
  sns.heatmap(confusion_mtx, annot=True, linewidths=0.01,cmap="Greens",linecolor="gray", fmt= '.1f',ax=ax)
  plt.xlabel("Predicted Label")
  plt.ylabel("True Label")
  plt.title("Confusion Matrix")
  plt.show()
  print(f"=======-------#################------========\n\n\n")