import pandas as pd

df = pd.read_csv('insurance.csv')
# Simple contrôle : pas de valeurs manquantes
assert not df.isnull().any().any(), "Des valeurs manquantes sont présentes !"
print("Data validation OK")
