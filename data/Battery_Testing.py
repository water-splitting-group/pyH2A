import numpy as np

data = np.array([100., 50., 25., 15., 10., 5., 10., 15., 25., 50., 100.])
demand = 50.
threshold = 15.

demand *= np.ones(len(data)) 

difference = data - demand
print(np.sum(difference))


