#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 10:50:40 2024

@author: ipiq
"""

import time 
from pyrpl.async_utils import sleep
import numpy as np
import matplotlib.pyplot as plt 
from pyrpl import Pyrpl
import pandas as pd 
import pickle 
import os 
# import path
import allantools 
# import tqdm 
from scipy.optimize import curve_fit
import scienceplots 
from numpy.fft import fft


plt.style.use('science')




current_dir = os.path.dirname(os.path.abspath(__file__))
figures_dir = os.path.join(current_dir, 'Figures et Data')


if not os.path.exists(figures_dir):
    os.makedirs(figures_dir)
    


free = pickle.load(open('free_running_signal.pkl', "rb"))
locked = pickle.load(open('locked_laser.pkl', "rb"))


times_free = free['times']
times_locked = locked['times']
signal_free = free['signal']
signal_locked = locked['signal']


tmp = [(times_free[i], signal_free[i]) for i in range(len(times_free))]
tmp = [x for x in tmp if x[1] < 0.125]
times_free = [tmp[i][0] for i in range(len(tmp))]
signal_free = [tmp[i][1] for i in range(len(tmp))]

times_free = np.array(times_free)
signal_free = np.array(signal_free)


### Free running laser ###


# m = np.mean(signal_free)
# d = np.std(signal_free, ddof = 1)

# y_up = m + d
# y_down = m - d

# y_up2 = m + 2*d
# y_down2 = m - 2*d


# # Computation of the percentage of the points which are within the red band and in the orange band 
# in_band_free = [s for s in signal_free if s >= y_down and s <= y_up]
# prop = (len(in_band_free)/len(signal_free)) * 100

# in_band_free2 = [s for s in signal_free if s >= y_down2 and s <= y_up2]
# prop2 = (len(in_band_free2)/len(signal_free)) * 100



# print(f'{prop}%')
# print(f'{prop2}%')

# fig = plt.figure()
# plt.plot(times_free, signal_free, 'b.', zorder = 0)

# xmax = times_free[np.argmax(signal_free)]
# ymax = signal_free.max()
# xmin = times_free[np.argmin(signal_free)]
# ymin = signal_free.min()
# ax=plt.gca()
# x_bounds = ax.get_xbound()
# y_bounds = ax.get_ybound()
# ax.set_xlim(x_bounds[0], x_bounds[1])
# ax.set_ylim(y_bounds[0], y_bounds[1])
# plt.hlines(y_up2, x_bounds[0] ,x_bounds[1], colors ='orange', linestyles='dashed')
# plt.hlines(y_down2, x_bounds[0] ,x_bounds[1], colors='orange', linestyles='dashed')
# plt.hlines(y_up, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1, label = f'std = {d:.3f}')
# plt.hlines(y_down, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1)
# plt.hlines(m, x_bounds[0] ,x_bounds[1], colors='black', linestyles='dashed', zorder=1, label = f'mean = {m:.3f}') 


# plt.legend() 
# plt.xlabel('times (seconds)')
# plt.ylabel('voltage (V)')
# plt.title('Photodiode Voltage when the laser is free')
# plot_file = os.path.join(figures_dir, "free_laser.png")
# plt.show()
# # plt.savefig(plot_file)

# print(m, d)




### Power-locked laser ###


m = np.mean(signal_locked)
d = np.std(signal_locked, ddof = 1)

y_up = m + d
y_down = m - d


y_up2 = m + 2*d
y_down2 = m - 2*d


# Computation of the percentage of the points which are within the red band and in the orange band 
in_band_free = [s for s in signal_free if s >= y_down and s <= y_up]
prop = (len(in_band_free)/len(signal_free)) * 100

in_band_free2 = [s for s in signal_free if s >= y_down2 and s <= y_up2]
prop2 = (len(in_band_free2)/len(signal_free)) * 100



print(f'{prop}%')
print(f'{prop2}%')


fig = plt.figure()
plt.plot(times_locked, signal_locked, 'b.', zorder = 0)

xmax = times_locked[np.argmax(signal_locked)]
ymax = signal_locked.max()
xmin = times_locked[np.argmin(signal_locked)]
ymin = signal_locked.min()
ax=plt.gca()
x_bounds = ax.get_xbound()
y_bounds = ax.get_ybound()
ax.set_xlim(x_bounds[0], x_bounds[1])
ax.set_ylim(y_bounds[0], y_bounds[1])
plt.hlines(y_up2, x_bounds[0] ,x_bounds[1], colors ='orange', linestyles='dashed')
plt.hlines(y_down2, x_bounds[0] ,x_bounds[1], colors='orange', linestyles='dashed')
plt.hlines(y_up, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1, label = f'std = {d:.3f}')
plt.hlines(y_down, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1)
plt.hlines(m, x_bounds[0] ,x_bounds[1], colors='black', linestyles='dashed', zorder=1, label = f'mean = {m:.3f}') 


plt.legend() 
plt.xlabel('times (seconds)')
plt.ylabel('voltage (V)')
plt.title('Photodiode Voltage when the laser is locked at 0.09V')
plot_file = os.path.join(figures_dir, "locked_laser.png")
plt.show()
# plt.savefig(plot_file)

print(m, d)


# Comparison with both plots on the same figure may not be apt since there 
# would be too many points 

# Rk: les std n'étant pas trs différente en vrai, il peut être intéressante de regarder 
# quelle proportion du temps on est dans les bandes rouges pour les deux signals
# car on voit visuellement que cette proportion est beaucoup plus importante 
# pour le signal locké 



# Voir les fonctions comme psd2allan, ... et leur fonctionnement 
# pour faire le lien entre PSD et allan et confirmer les résultats



##### Allance Variance of the signals : stability over time #####

# Adev is able to measure the effect of the slow variations due to variations of the polarization 



# def fit_function(x, a, b): 
#     return a*x + b


# ### Free running signal ### 

# t = np.logspace(0,2, 50)  # tau values from 1 to 100 -> better to have more date though time 
# t2, ad2, aderr2, adn2 = allantools.oadev(signal_free, rate = 0.25, data_type = 'phase', taus = t)
# # Rq: je mets les deux en type 'phase' car c'est le seul qui marche pour le signal_locked -> Pourquoi ??


# fig = plt.figure()
# plt.plot(np.log(t2), np.log(ad2), label = 'free running laser')
# plt.xlabel('Taus (seconds)')
# plt.ylabel('Overlapping Allan deviation')
# plt.grid()
# popt, pcov = curve_fit(fit_function, np.log(t2), np.log(ad2))
# a2 = popt[0]
# b2 = popt[1]
# plt.plot(np.log(t2), fit_function(np.log(t2), *popt), color='r', linestyle = 'dashed', label = f'linear fit: y = {a2:.3f}x + {b2:.3f}')
# perr2 = np.sqrt(np.diag(pcov))
# plt.legend()
# plt.show()


# ### Power-locked laser ### 



# t3, ad3, aderr3, adn3 = allantools.oadev(signal_locked, rate = 0.25, data_type="phase", taus = t)

# fig = plt.figure()
# plt.plot(np.log(t3), np.log(ad3), label = "locked laser")
# plt.xlabel('Taus (seconds)')
# plt.ylabel('Overlapping Allan deviation')
# plt.grid()
# popt, pcov = curve_fit(fit_function, np.log(t3), np.log(ad3))
# a3 = popt[0]
# b3 = popt[1]
# plt.plot(np.log(t3), fit_function(np.log(t3), *popt), color='r', linestyle= 'dashed', label = f'linear fit: y = {a3:.3f}x + {b3:.3f}')
# perr3 = np.sqrt(np.diag(pcov))
# plt.legend()
# plt.show()







'''
L'installation via pip de AllanTools s'est bien passée jusqu'à 
WARNING: Ignoring invalid distribution -ip (c:\python39\lib\site-packages)
  WARNING: Failed to write executable - trying to use .deleteme logic
ERROR: Could not install packages due to an OSError: [WinError 2] Le fichier spécifié est introuvable: 'c:\\python39\\Scripts\\tabulate.exe' -> 'c:\\python39\\Scripts\\tabulate.exe.deleteme'

Il faudra voir si cette erreur empêche le fonctionnement de AllanTools pour ce que je veux faire ou non 
'''
















