import xgboost as xgb
import shap
import numpy as np
import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
import math

from sklearn.preprocessing import OrdinalEncoder


from staty_base import stratified_train_test_split

FILE_NAME = "./collected-data/flat-replay-data-5rep.csv"
MODEL_STORARE_DIR = "./models/"
SHAP_STORARE_DIR = "./models/shap/"
SEED = 3142

def get_shap_values():
  dataset = pd.read_csv(FILE_NAME) # For Pandas
  dataset = dataset.astype({"Tag": str})
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
  dataset['Tag'] = dataset['Tag'].replace(mappingNumToCat) # Map to categorical
  # split data into X and y
  X, y = dataset.drop("Tag", axis=1), dataset[['Tag']] # For Pandas
  # Encode y to numeric
  y_encoded = OrdinalEncoder().fit_transform(y)
  # Split the data
  X_train, y_train, X_test, y_test = stratified_train_test_split(y_encoded, X)

  dtrain_clf = xgb.DMatrix(X_train, y_train, enable_categorical=True)
  xgboost_model = joblib.load(MODEL_STORARE_DIR + "xgboost_model.pkl")

  # SHAP values

  print("Loading SHAP values...")
  explainer = shap.TreeExplainer(xgboost_model, data=X)

  shap_values = None
  try:
    shap_values = joblib.load(SHAP_STORARE_DIR + "shap-values.pkl")
  except:
    print("Il n\'y a pas de valeurs SHAP stockées.")
    shap_values = explainer(X)
    os.makedirs(SHAP_STORARE_DIR, exist_ok=True)
    joblib.dump(shap_values, SHAP_STORARE_DIR + "shap-values.pkl") # Sauvegarde les valeurs SHAP
  
  i=3

  exp = shap.Explanation(
    shap_values.values[:,:,i],
    shap_values.base_values[:,i], 
    data=X.values, 
    feature_names=list(X.columns.values)
  )
  
  shap_as_list=[]
  for i2 in range(8):
    shap_as_list.append(shap_values.abs.values[:,:,i2])

  
  return (shap_as_list, exp)


# Plots

# def scatter_plots():
#   shap_as_list = shap_as_list()
  
#   n_cols = len(shap_as_list.feature_names)
  
#   ncols=3
  
#   fig, axs = plt.subplots(figsize=(16, 16), ncols=ncols, nrows=math.ceil(n_cols/ncols), layout="constrained")
#   fig.supylabel("Valeur SHAP")
#   fig.supxlabel("Valeur de la variable")

#   for i in range(n_cols):
#     col = exp.feature_names[i]
#     ax = axs[math.floor(i / ncols), i % ncols]
#     shap.plots.scatter(exp[:,exp.feature_names[i]], alpha=0.1, ax=ax, show=False)
#     ax.tick_params(axis='x', labelrotation=75)
#     ax.set(
#       xlabel=None,
#       ylabel=None,
#       title=col
#     )
    
#   for j in range(ncols * math.ceil(n_cols/ncols) - n_cols):
#     ax = axs[math.floor((i+j+1) / ncols), (i+j+1) % ncols]
#     ax.axis('off')
  
#   plt.suptitle("Valeurs SHAP selon la valeur de chaque variable")



def bar_plot():
  shap_as_list, exp = get_shap_values()
  
  shap.summary_plot(
    shap_as_list,
    feature_names=list(exp.feature_names),
    class_names=["Normal", "Offroad", "Fullspeed", "LOL", "Tech", "SpeedTech", "PressForward", "Grass"],
    max_display=17,
    show=False,
    plot_type="bar",
    plot_size=[9,6],
    color=plt.cm.get_cmap("Accent")
  )
  
  # shap.plots.bar(shap_as_list, max_display=17, show=True, clustering_cutoff=2)

def violin_plot(i=0):
  shap_as_list, exp = get_shap_values()
  
  shap.summary_plot(shap_as_list[i], max_display=17, show=False, plot_type="violin")
  # shap.plots.violin(
  #   exp.abs.abs,
  #   max_display=17,
  #   color="green",
  #   axis_color="#333333",
  #   title=None,
  #   alpha=1,
  #   show=True,
  #   sort=True,
  #   color_bar=True,
  #   plot_size="auto",
  #   layered_violin_max_num_bins=20,
  #   class_names=None,
  #   cmap=plt.cm.cool,
  # )
  # shap.plots.violin(exp.abs.abs, color="red", max_display=17, show=False)

# def beeswarm_plot():
#   shap_as_list, exp = get_shap_values()
  
#   shap.plots.beeswarm(shap_as_list[3], color="blue", max_display=17, show=False)
  
#   # shap.plots.beeswarm(
#   #   exp.abs,
#   #   max_display=17,
#   #   clustering=None,
#   #   cluster_threshold=0.01,
#   #   color="blue",
#   #   axis_color="#333333",
#   #   alpha=0.2,
#   #   show=False,
#   #   log_scale=False,
#   #   color_bar=False,
#   #   s=8,
#   #   plot_size=(16,8)
#   # )

def waterfall_plot(i=0):
  __, exp = get_shap_values()
  
  shap.plots.waterfall(exp[i], max_display=17, show=False)

def render_all():
  # # Scatter plot
  # scatter_plots()
  # plt.savefig("rendered-figs/fig-scatter.pdf")
  # plt.clf()
  
  # Bar plot
  bar_plot()
  plt.xlabel("Impacte moyenne sur la prédiction du modèle")
  plt.ylabel("Caractéristique (variable aplatie)")
  plt.title("Impactes de caractéristiques selon l'étiquette")
  plt.tight_layout()
  plt.savefig("rendered-figs/fig-bar.pdf")
  plt.clf()
  
  # Violin plot
  violin_plot()
  plt.savefig("rendered-figs/fig-violin.pdf")
  plt.clf()
  
  # # Beeswarm plot
  # beeswarm_plot()
  # plt.xlabel("Impacte moyenne sur la prédiction du modèle")
  # plt.savefig("rendered-figs/fig-beeswarm.pdf")
  # plt.clf()
  
  # Waterfall [0] plot
  waterfall_plot(i=3)
  plt.savefig("rendered-figs/fig-waterfall-3.pdf")
  plt.clf()

render_all()