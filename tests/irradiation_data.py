import numpy as np
import matplotlib.pyplot as plt
import timeit

def find_closest_array_element(array, index, target):
    pos = np.searchsorted(array[:,index], target)
    if pos < len(array) and array[pos, index] == target:
        return array[pos]
    if pos == 0:
        element1 = array[0]
        element2 = array[1]
    elif pos == len(array):
        element1 = array[pos-2]
        element2 = array[pos-1]
    else:
        element1 = array[pos-1]
        element2 = array[pos]
    b_thr = (element2[1]-element1[1])/(element2[0]-element1[0])*(target-element1[0])+element1[1]
    u_thr = (element2[2]-element1[2])/(element2[0]-element1[0])*(target-element1[0])+element1[2]
    area = (element2[3]-element1[3])/(element2[0]-element1[0])*(target-element1[0])+element1[3]
    return [target, b_thr, u_thr, area]

def save_threshold_list(data_array, data_max):
    optimised_thresholds = []
    for capacity_ratio in np.arange(1.01, 1000, .01):
        print(f"capacity_ratio:\t{capacity_ratio}")
        used_area = []
        bt_opt = data_max/2
        for i in range(1, 10):
            bt_min = max([0, bt_opt-10**(1-i)])
            bt_max = min([data_max, bt_opt+10**(1-i)])
            bottom_thresholds = np.arange(bt_min, bt_max, (bt_max-bt_min)/100)
            bottom_thresholds = bottom_thresholds[bottom_thresholds*capacity_ratio <= data_max]
            upper_thresholds = bottom_thresholds * capacity_ratio
            for ti in range(len(bottom_thresholds)):
                used_area.append([
                    capacity_ratio,
                    bottom_thresholds[ti], 
                    upper_thresholds[ti], 
                    sum(data_array[(data_array<upper_thresholds[ti]) & (data_array>bottom_thresholds[ti])])
                ])
            used_area_array = np.array(used_area)
            bt_opt_idx = np.argmax(used_area_array[:,3])
            bt_opt = used_area_array[bt_opt_idx,1]
        optimised_threshold_idx = np.argmax(used_area_array[:,3])
        plt.figure()
        plt.plot(used_area_array[:,1], used_area_array[:,3])
        plt.scatter(used_area_array[optimised_threshold_idx, 1], used_area_array[optimised_threshold_idx, 3], color="red")
        plt.show()
        optimised_thresholds.append(used_area_array[optimised_threshold_idx])
    np.savetxt("tests/results/opt-capacity_ratio.csv", optimised_thresholds, delimiter=",", fmt="%f")

def load_threshold_list(filename):
    return np.loadtxt(filename, delimiter=",")

raw_data = []
with open("tests/results/irradiation_data.txt", "r") as f:
    raw_data = f.readlines()
data_array = np.array([float(line) for line in raw_data])
data_max = max(data_array)

save_threshold_list(data_array, data_max)
optimised_thresholds_array = load_threshold_list("tests/results/opt-capacity_ratio.csv")


ratio_data = []
min_cp = 500
for max_cp in range(510, 50000, 10):
    opt = find_closest_array_element(optimised_thresholds_array, index=0, target=max_cp/min_cp)
    print(opt)
    scale = min_cp/opt[1]
    print(f"scale:\t\t{scale}\nscaled:\t\t{opt[3]*scale}")
    scaled_data_array = data_array*scale
    unused_energy = sum(scaled_data_array[(scaled_data_array<min_cp) | (scaled_data_array>max_cp)])
    print(f"unused energy:\t{unused_energy}")
    ratio_data.append([max_cp/min_cp, unused_energy])

ratio_data_array = np.array(ratio_data)
#plt.figure()
#plt.plot(ratio_data_array[:,0], ratio_data_array[:,1])
#plt.show()

plt.figure()
plt.plot(optimised_thresholds_array[:,0], optimised_thresholds_array[:,3])
plt.show()