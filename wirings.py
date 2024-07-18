# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
Branchements du sequenceur-compteur
"""
version = "2019_02_18" 

# branchements device - sequenceur - compteur

# branchements device - sequenceur - compteur
Wirings = {
            "heat"    : (15, 5),
            "ir"      : (3 , 1),
            "beam0"   : (4 , 2),
            "beam1"   : (6 , 3),
            "switch1" : (8, 4),
            "switch2" : (1 , 0),
            "ilock01" : (9 ,-1),
            "ilock11" : (14,-1),
            "ilock00" : (16,-1),
            "gate"    : (2 ,-1),
          }

#BEAM_NAME_MODE | RF_ALIM_ID  RF_ALIM_CH | ILOCK_ID  ILOCK_CH | SWITCHES
lasers_cfg = {
    "laser01" : {"rf_alim" : ("rigol0",1),"ilock" : (0,1),"switches" : "beam0"},
    "laser02" : {"rf_alim" : ("rigol3",2),"ilock" : (1,1),"switches" : "beam0 switch1"},
    "laser11" : {"rf_alim" : ("rigol0",2),"ilock" : (0,0),"switches" : "beam1 switch2"}
}
