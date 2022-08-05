from dante import DanteTreeNode
import pickle

with open('amh_datierung.pkl', 'rb') as date_file:
    datierungen = pickle.load(date_file)

print(datierungen.flatten(3))