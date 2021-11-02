# Reoptimization Model

import numpy as np
from datetime import datetime, timedelta
from scipy.spatial import distance

# Sets
n = 10                                  # number of pickup nodes, equivalent to number of requests
num_vehicles = 16
num_nodes = 2 * n
num_nodes_and_depots = 2 * num_vehicles + 2 * n


# Parameters
C_D = [1, 1, 1]
C_R = 10                                # lost revenue from not serving a request
C_K = [100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100]                     # cost of using vehicle k
C_O = 10                                # cost of deviation from original plan
C_F = 1
C_T = 1
Q_S = [5, 4, 16]
Q_W = [1, 1, 1,1, 1, 1,1, 1, 1,1, 1, 1,1, 1, 1,1]
L_S =                                  # load for each request
L_W =                                  # wheelchair load for request


Position = []

D_ij = distance.cdist(Position, Position, "euclidean")

speed = 40

T_ij = np.empty(shape=(num_nodes_and_depots, num_nodes_and_depots), dtype=timedelta)

for i in range(num_nodes_and_depots):
    for j in range(num_nodes_and_depots):
        T_ij[i][j] = timedelta(hours=(D_ij[i][j] / speed))

T_S_L = []

T_S_U = []

T_H_L = []

T_H_U = []

F = 2
M_ij = np.empty(shape=(num_nodes, num_nodes), dtype=datetime)
for i in range(num_nodes):
    for j in range(num_nodes):
        M_ij[i][j] = T_H_U[i] + T_ij[i][j] - T_H_L[j]
M = timedelta(hours=24).total_seconds()  # in hours
