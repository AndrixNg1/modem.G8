import csv
from pathlib import Path
base=Path('mesures/module3/simulation')
def lire(n): return list(csv.DictReader((base/n).open()))
a,s=lire('resultats_awgn_arq.csv'),lire('resultats_awgn_sans_arq.csv')
l=[]
for sb in (6,3,0,-3,-6,-9,-12):
 x=[r for r in a if int(r['sb_db'])==sb]; y=[r for r in s if int(r['sb_db'])==sb]
 ok=lambda z:sum(r['statut']=='OK' for r in z)
 l.append({'sb_db':sb,'essais':len(x),'succes_arq':ok(x),'succes_sans_arq':ok(y),'taux_arq':ok(x)/len(x),'taux_sans_arq':ok(y)/len(y),'gain_points':100*(ok(x)-ok(y))/len(x),'retransmissions':sum(int(r['retransmissions']) for r in x),'duree_moyenne':sum(float(r['duree_simulee']) for r in x)/len(x),'debit_moyen':sum(float(r['debit_utile']) for r in x)/len(x),'abandons':sum(r['statut']!='OK' for r in x)})
with (base/'synthese_awgn.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=l[0]);w.writeheader();w.writerows(l)
print(l)
