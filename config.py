# Model 1
import numpy as np

# Sets
num_pickup_nodes = 1
num_dropoff_nodes = 1
num_nodes = 2
num_vehicles = 1

# Parameters
C_ijk = 1
C_R = 1
C_F = 1
C_T = 1
Q_S = [1]
Q_W = [1]
L_S = [1]
L_W = [0]
T_ij = [[0, 1], [1, 0]]
T_S_L = [8]
T_S_U = [8.5]
T_H_L = [7.75]
T_H_U = [8.6]
F = 1.15
M_ij = np.zeros((num_nodes, num_nodes))
for i in range(num_nodes):
    for j in range(num_nodes):
        M_ij[i, j] = T_H_L + T_ij[i, j] - T_H_U
M = 24      # in hours


# Origin and destination
o_k = [0]
d_k = [3]
n = num_pickup_nodes

