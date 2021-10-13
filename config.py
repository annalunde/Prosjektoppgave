# Model 1
import numpy as np
from datetime import datetime,timedelta

# Sets
num_pickup_nodes = 1
n = num_pickup_nodes
num_vehicles = 1
num_nodes = 2*n
num_nodes_depots = 2*num_vehicles + 2*n


# Parameters
C_D = [1]
D_ij = [[0, 5], [5, 0]]     # in kms
C_R = 10
C_F = 1
C_T = 1
Q_S = [10]
Q_W = [1]
L_S = [1]
L_W = [0]
T_ij = [[timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=30)], [timedelta(hours=0, minutes=30), timedelta(hours=0, minutes=0)]]
T_S_L = [datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"), datetime.strptime("2021-10-13 09:55:00", "%Y-%m-%d %H:%M:%S")]
T_S_U = [datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"), datetime.strptime("2021-10-13 10:05:00", "%Y-%m-%d %H:%M:%S")]
T_H_L = [datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"), datetime.strptime("2021-10-13 09:45:00", "%Y-%m-%d %H:%M:%S")]
T_H_U = [datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"), datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S")]
F = 1.15
M_ij = np.empty(shape=(num_nodes, num_nodes),dtype=datetime)
for i in range(num_nodes):
    for j in range(num_nodes):
        M_ij[i][j] = T_H_L[i] + T_ij[i][j] - T_H_U[j]
M = timedelta(hours=24).total_seconds()     # in hours







