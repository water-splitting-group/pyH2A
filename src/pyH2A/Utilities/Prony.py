import numpy as np
from scipy.optimize import curve_fit

# Target: approximate 1/sqrt(t) over [1 hour, 1 year]
t_fit = np.linspace(3600, 365*24*3600*2, 10000)
k_fit = 1 / np.sqrt(t_fit)

def prony6(t, c1, g1, c2, g2, c3, g3, c4, g4, c5, g5, c6, g6):
    return c1*np.exp(-g1*t) + c2*np.exp(-g2*t) + c3*np.exp(-g3*t) + c4*np.exp(-g4*t) + c5*np.exp(-g5*t) + c6*np.exp(-g6*t)

p0 = [1e-3, 1e-4, 1e-4, 1e-6, 1e-8, 1e-5, 1e-5, 1e-6, 1e-4, 1e-4, 1e-5, 1e-8 ]
popt, _ = curve_fit(prony6, t_fit, k_fit, p0=p0, maxfev=1000000)
c = popt[0::2]   # [ci]
gamma = popt[1::2]  # [gi]

print(c)
print('------')
print(gamma)
