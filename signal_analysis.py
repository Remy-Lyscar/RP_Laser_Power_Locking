#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 10:50:40 2024

@author: ipiq
"""

import time 
import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
import pickle 
import os 
# import path
import allantools 
# import tqdm 
from scipy.optimize import curve_fit
import scienceplots 
from numpy.fft import fft
# import pathlib
# import matplotlib as mpl

# pathlib.Path.rmdir( mpl.get_cachedir())


plt.style.use('science')




current_dir = os.path.dirname(os.path.abspath(__file__))
figures_dir = os.path.join(current_dir, 'Figures et Data')
df_dir = os.path.join(current_dir, 'Dataframes')


if not os.path.exists(figures_dir):
    os.makedirs(figures_dir)
    


free = pickle.load(open(os.path.join(df_dir,'free_running_signal_mer_26_juin.pkl'), "rb"))
locked = pickle.load(open(os.path.join(df_dir,'locked_laser_mer_26_juin.pkl'), "rb"))


times_free = free['times']
times_locked = locked['times']
signal_free = free['signal']
signal_locked = locked['signal']



times_free = np.array(times_free)
signal_free = np.array(signal_free)


### Free running laser ###


m = np.mean(signal_free)
d = np.std(signal_free, ddof = 1)

y_up = m + d
y_down = m - d

y_up2 = m + 2*d
y_down2 = m - 2*d


# Computation of the percentage of the points which are within the red band and in the orange band 
in_band_free = [s for s in signal_free if s >= y_down and s <= y_up]
prop = (len(in_band_free)/len(signal_free)) * 100

in_band_free2 = [s for s in signal_free if s >= y_down2 and s <= y_up2]
prop2 = (len(in_band_free2)/len(signal_free)) * 100



print(y_up - y_down)
print(y_up2 - y_down2)

# fig = plt.figure()
# plt.plot(times_free, signal_free, color = 'cornflowerblue', marker = '.', linestyle = '', zorder = 0)

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
# plt.hlines(y_up, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1, label = f'std = {d:.4f}')
# plt.hlines(y_down, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1)
# plt.hlines(m, x_bounds[0] ,x_bounds[1], colors='black', linestyles='dashed', zorder=1, label = f'mean = {m:.4f}') 


# plt.legend(fontsize = 20) 
# plt.xlabel('times (seconds)')
# plt.ylabel('voltage (V)')
# plt.title('Photodiode Voltage when the laser is free')
# plt.rc('axes', titlesize=20)
# plt.rc('axes', labelsize = 20) 
# plot_file = os.path.join(figures_dir, "free_laser.png")
# plt.show()
# # plt.savefig(plot_file)

# print(m, d)


def fit_function(x, a, b, c, d, e, f, g, h, i, j, k, l):
    return a*x**11 + b*x**10 + c*x**9 + d*x**8+ e*x**7 + f*x**6 + g*x**5 + h*x**4 + i*x**3 + j*x**2 +k*x + l 


tmp = [(times_free[i], signal_free[i]) for i in range(len(times_free))]
tmp = [x for x in tmp if x[0] < 1200 and x[0] > 1000]


popt, pcov = curve_fit(fit_function, times_free, signal_free)
a, b, c, d, e, f, g, h, i, j,  k, l = popt[0], popt[1], popt[2], popt[3], popt[4], popt[5], popt[6], popt[7], popt[8], popt[9], popt[10], popt[11]
perr = np.sqrt(np.diag(pcov))
fig = plt.figure()
plt.plot(times_free, signal_free, times_free, fit_function(times_free, a, b, c, d, e, f, g, h, i, j, k, l))
plt.show()


Y = fit_function(times_free, a, b, c, d, e, f, g,h, i, j , k , l)
err_free = [signal_free[i] - Y[i] for i in range(len(times_free))]

errstd = np.std(err_free, ddof = 1)


fig = plt.figure()
plt.hist(err_free, bins = 'auto', zorder = 0)
ax=plt.gca()
x_bounds = ax.get_xbound()
y_bounds = ax.get_ybound()
ax.set_xlim(x_bounds[0], x_bounds[1])
ax.set_ylim(y_bounds[0], y_bounds[1])
plt.vlines(errstd, y_bounds[0], y_bounds[1], colors = 'red', linestyles = 'dashed', zorder = 1, label = f'std: {errstd:.4f}' )
plt.vlines(-errstd, y_bounds[0], y_bounds[1], colors = 'red', linestyles = 'dashed', zorder = 1)
plt.vlines(2*errstd, y_bounds[0], y_bounds[1], colors = 'orange', linestyles = 'dashed', zorder = 1)
plt.vlines(-2*errstd, y_bounds[0], y_bounds[1], colors = 'orange', linestyles = 'dashed', zorder = 1)
plt.xlabel('Dispersion (V)')
plt.ylabel('Number of points')
plt.legend()
plt.show()



### Power-locked laser ###


m = np.mean(signal_locked)
d = np.std(signal_locked, ddof = 1)

y_up = m + d
y_down = m - d


y_up2 = m + 2*d
y_down2 = m - 2*d


# Computation of the percentage of the points which are within the red band and in the orange band 
in_band_locked = [s for s in signal_locked if s >= y_down and s <= y_up]
prop = (len(in_band_locked)/len(signal_locked)) * 100

in_band_locked2 = [s for s in signal_locked if s >= y_down2 and s <= y_up2]
prop2 = (len(in_band_locked2)/len(signal_locked)) * 100



print(y_up - y_down)
print(y_up2 - y_down2)


# fig = plt.figure()
# plt.plot(times_locked, signal_locked, color = 'cornflowerblue', marker = '.', linestyle = '', zorder = 0)

xmax = times_locked[np.argmax(signal_locked)]
ymax = signal_locked.max()
xmin = times_locked[np.argmin(signal_locked)]
ymin = signal_locked.min()
# ax=plt.gca()
# x_bounds = ax.get_xbound()
# y_bounds = ax.get_ybound()
# ax.set_xlim(x_bounds[0], x_bounds[1])
# ax.set_ylim(y_bounds[0], y_bounds[1])
# plt.hlines(y_up2, x_bounds[0] ,x_bounds[1], colors ='orange', linestyles='dashed')
# plt.hlines(y_down2, x_bounds[0] ,x_bounds[1], colors='orange', linestyles='dashed')
# plt.hlines(y_up, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1, label = f'std = {d:.4f}')
# plt.hlines(y_down, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1)
# plt.hlines(m, x_bounds[0] ,x_bounds[1], colors='black', linestyles='dashed', zorder=1, label = f'mean = {m:.4f}') 


# plt.legend(fontsize=20) 
# plt.xlabel('times (seconds)')
# plt.ylabel('voltage (V)')
# plt.title('Photodiode Voltage for a lock at 0.08V')
# plt.rc('axes', titlesize=20)
# plt.rc('axes', labelsize = 20) 
# plot_file = os.path.join(figures_dir, "locked_laser.png")
# plt.show()
# # plt.savefig(plot_file)

# print(m, d)

err_locked = [v - m for v in signal_locked]
bins = (ymax - ymin)/0.002 

errstd = np.std(err_locked, ddof=1)

fig = plt.figure()
plt.hist(err_locked, bins = 'auto', zorder = 0)
ax=plt.gca()
x_bounds = ax.get_xbound()
y_bounds = ax.get_ybound()
ax.set_xlim(x_bounds[0], x_bounds[1])
ax.set_ylim(y_bounds[0], y_bounds[1])
plt.vlines(errstd, y_bounds[0], y_bounds[1], colors = 'red', linestyles = 'dashed', zorder = 1, label = f'std: {errstd:.4f}' )
plt.vlines(-errstd, y_bounds[0], y_bounds[1], colors = 'red', linestyles = 'dashed', zorder = 1)
plt.vlines(2*errstd, y_bounds[0], y_bounds[1], colors = 'orange', linestyles = 'dashed', zorder = 1)
plt.vlines(-2*errstd, y_bounds[0], y_bounds[1], colors = 'orange', linestyles = 'dashed', zorder = 1)
plt.xlabel('Dispersion (V)')
plt.ylabel('Number of points')
plt.legend()
plt.show()


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



# def fit_function(tau, a, b): 
#     return a*tau**b


# ### Free running signal ### 

# t = np.logspace(0,3.55, 50)
# t2, ad2, aderr2, adn2 = allantools.oadev(signal_free, rate = 0.25, data_type = 'phase', taus = t)
# # Rq: je mets les deux en type 'phase' car c'est le seul qui marche pour le signal_locked -> Pourquoi ??


# fig = plt.figure()
# plt.loglog(t2, ad2, label = 'free running laser', color = 'b', linestyle = '', marker = '.')
# plt.xlabel('Taus (seconds)')
# plt.ylabel('Overlapping Allan deviation')
# plt.grid()
# popt, pcov = curve_fit(fit_function, t2,ad2)
# a2 = popt[0]
# b2 = popt[1]
# plt.loglog(t2, fit_function(t2, *popt), color='r', linestyle = 'dashed', label = f'fit:  a = {a2:.4f} \n b = {b2:.4f}')
# perr2 = np.sqrt(np.diag(pcov))
# plt.legend()
# plt.show()


# ### Power-locked laser ### 



# t3, ad3, aderr3, adn3 = allantools.oadev(signal_locked, rate = 0.25, data_type="phase", taus = t)

# fig = plt.figure()
# plt.loglog(t3, ad3, label = "locked laser", color = 'b', linestyle = '', marker = '.')
# plt.xlabel('Taus (seconds)')
# plt.ylabel('Overlapping Allan deviation')
# plt.grid()
# popt, pcov = curve_fit(fit_function, t3, ad3)
# a3 = popt[0]
# b3 = popt[1]
# plt.loglog(t3, fit_function(t3, *popt), color='r', linestyle = 'dashed', label = f'fit:  a = {a3:.4f} \n b = {b3:.4f}')
# perr3 = np.sqrt(np.diag(pcov))
# plt.legend()
# plt.show()