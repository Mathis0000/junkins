import pandas as pd

df = pd.read_csv('insurance.csv')
# Ex. vérifier que l'âge est dans un intervalle raisonnable
assert df['age'].between(18, 100).all(), "Âge hors bornes détecté !"
print("Data quality OK")
