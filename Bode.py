# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 10:34:48 2024

@author: remyl
"""

import time 
import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
import pickle 
import os  
from scipy.optimize import curve_fit
import scienceplots 


plt.style.use('science')



def annot_max_G(x,y, ax=None):
    xmax = x[np.argmax(y)]
    ymax = y.max()
    text= "At resonance: \n f = {:.3f} Hz \n G = {:.3f}".format(xmax, ymax)
    if not ax:
        ax=plt.gca()
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    # arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=60")
    # kw = dict(xycoords='data',textcoords="axes fraction",
    #           arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")
    kw = dict(xycoords='data',textcoords="axes fraction", bbox=bbox_props, ha="right", va="top")
    ax.annotate(text, xy=(xmax, ymax), xytext=(0.5,0.3), **kw)
    
    x_bounds = ax.get_xbound()
    y_bounds = ax.get_ybound()
    ax.set_xlim(x_bounds[0], x_bounds[1])
    ax.set_ylim(y_bounds[0], y_bounds[1])
    plt.vlines(xmax, y_bounds[0], ymax, colors = 'r', linestyles='dashed')
    plt.hlines(ymax, x_bounds[0] ,xmax, colors='r', linestyles='dashed')
    
    
def annot_max_phi(x,y, ax=None):
    xmax = x[8]
    ymax = y[8] 
    text= "At resonance: \n f = {:.3f} \n phi = {:.3f}".format(xmax, ymax)
    if not ax:
        ax=plt.gca()
    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    # arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=60")
    # kw = dict(xycoords='data',textcoords="axes fraction",
    #           arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")
    kw = dict(xycoords='data',textcoords="axes fraction", bbox=bbox_props, ha="right", va="top")
    ax.annotate(text, xy=(xmax, ymax), xytext=(0.5,0.3), **kw)
    
    x_bounds = ax.get_xbound()
    y_bounds = ax.get_ybound()
    ax.set_xlim(x_bounds[0], x_bounds[1])
    ax.set_ylim(y_bounds[0], y_bounds[1])
    plt.vlines(xmax, y_bounds[0], ymax, colors = 'r', linestyles='dashed')
    plt.hlines(ymax, x_bounds[0] ,xmax, colors='r', linestyles='dashed')


f = np.array([0.1, 0.5, 1, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2, 2.5, 3, 4, 4.5, 5, 6])
G = np.array([2.6, 2.6, 2.9, 3.2, 3.25, 3.55, 3.75, 4.5, 5, 4.75, 4.45, 4.2, 3.9, 3.25, 2.5, 2, 1.56, 1.13, 0.86])
phi = np.array([-1, -1, -1, -7/8, -5/8, -1/2, -1/2, -1/2, -1/2, -1/2, -3/8, -3/8,-1/4, -1/4, -1/8, -1/16, 0, 0, 0])

f = [freq*1e6 for freq in f]
phi = [-1*p*np.pi for p in phi]
phi = np.array(phi)


Yerr = [0.05 for _ in range(len(G))]
Xerr = [0 for _ in range(len(f))]
Y_err = [np.pi/16 for _ in range(len(phi))]


fig = plt.figure()
plt.semilogx(f, G, marker = '.', linestyle = '-', color = 'b')
plt.xlabel('frequencies (Hz)')
plt.ylabel('Gain')
# for i in range(len(f)):
#     plt.errorbar(f[i], G[i], xerr = Xerr[i], yerr = Yerr[i], color='r')
plt.grid()
annot_max_G(f, G)
plt.show()


fig = plt.figure()
plt.semilogx(f, phi, marker = '.', linestyle = '-', color = 'b')
plt.xlabel('frequencies (Hz)')
plt.ylabel('Phase (rad)')
# for i in range(len(f)):
#     plt.errorbar(f[i], phi[i], xerr = Xerr[i], yerr = Y_err[i], color='r')
plt.grid()
annot_max_phi(f, phi)
plt.show()
