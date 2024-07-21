#FLAGS : ir laser0 laser1 gate
{T[wait]} POSPULSE   7 0  | 0        | sync scope
{T[meas]} SYNCDIGOUT 0 0  | 1 11 11 1 | signal
{T[pump]} SYNCDIGOUT 0 0  | 0 10 10 0 | pump in metastable
{T[meas]} SYNCDIGOUT 0 0  | 0 11 11 1 | background
{T[wait]} SYNCDIGOUT 0 0  | 1 10 10 0 | wait for ilock
