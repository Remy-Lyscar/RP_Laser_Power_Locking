import time 
import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
import pickle 
import os  
from scipy.optimize import curve_fit
import scienceplots 


plt.style.use('science')



##### Etape 1: coefficients de la lame séparatrice #####

"""

tout ceci peut être fait sans la RP, avec mon ordi par exemple. 
Placer le powermètre en sortie de la lame sur le chemin du faisceau utile.
Faire varier la puissance (5 à 10 points, à voir de combien à chaque fois pour couvrir la gamme de puissance dont on aura 
besoin en pratique dans les expériences) -> Comment? avec le robinet ou avec autre chose? 
Pour chaque configuration: Puissance_apres = (Puissance avant la lame)*T 
On peut donc calculer plusieurs valeurs de T et faire la moyenne, ...

On en déduit enfin R = 1-T

"""


P_av = []
P_ap = []
T = []

for i in range(len(P_av)): 
    T.append(P_ap[i] / P_av[i])

m = np.mean(T)
d = np.stf(T, ddof=1)

R = 1- m

print(m, d)

df = pd.DataFrame({
    'Puissance avant la lame': P_av, 
    'Puissance après la lame': P_ap, 
    'Valeurs de T calculées': T
}
)



##### Etape 2 : relation entre voltage de la photodiode et puissance qu'elle recoit #####

"""
On va faire mieux qu'à l'oeil comme la dernière fois. 
Sur l'ordi dans la même salle, histoire de pas avoir à trop bouger. 

On change la puissance sur la même gamme que précédemment, en mesurant la puissance avant la lame séparatrice
On en déduit P_ph et on lance une acquisition sur quelques secondes (quelques milliers de points) pour cette puissance. 
On fait la moyenne de V_ph pour chaque point et on trace V_ph en fonction de P_ph, pour déterminer les 
paramètres de la loi affine ou linéaire
"""

P_av = []
P_ph = [R * p for p in P_av]

V_ph = []  # Ce tableau ne va contenir que les valeurs moyennes calculées par un autre programme PyRPL (sur une dizaine de secondes)


def linear_fit(x, a, b): 
    return a*x + b


plt.plot(P_ph, V_ph)
popt, pcov = curve_fit(linear_fit, P_ph, V_ph)
a = popt[0]
b = popt[1]
plt.plot(P_ph, linear_fit(P_ph, a, b), color='red', linestyle = 'dashed', label = f'{a:.4f}x + {b:.4f}')
perr3 = np.sqrt(np.diag(pcov))
plt.legend()
plt.show()



