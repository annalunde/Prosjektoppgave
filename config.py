# Model 1
import numpy as np
from datetime import datetime, timedelta

# Sets
num_pickup_nodes = 3
n = num_pickup_nodes
num_vehicles = 1
num_nodes = 2 * n
num_nodes_and_depots = 2 * num_vehicles + 2 * n

# Parameters
C_D = [1]
D_ij = [
        [0, 1, 4, 1, 3, 3],
        [1, 0, 3, 2, 2, 2],
        [4, 3, 0, 3, 2, 4],
        [1, 2, 3, 0, 2, 2],
        [3, 1, 2, 2, 0, 3],
        [3, 2, 4, 2, 3, 0]
        ]  # in kms
#C_R = 10
C_F = 1
C_T = 1
Q_S = [10]
Q_W = [1]
L_S = [1, 2, 5] #Load for each request
L_W = [0, 1, 0] #Wheelchair load for request
T_ij = [
    [timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=6)],
    [timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=5)],
    [timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=7)],
    [timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=5)],
    [timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=6)],
    [timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=0)]
]

T_S_L = [
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:55:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:20:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:30:00", "%Y-%m-%d %H:%M:%S")
]
T_S_U = [
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:50:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:05:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:25:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:40:00", "%Y-%m-%d %H:%M:%S")
]

T_H_L = [
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:45:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:20:00", "%Y-%m-%d %H:%M:%S")
]
T_H_U = [
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:50:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:50:00", "%Y-%m-%d %H:%M:%S"),
]

F = 2
M_ij = np.empty(shape=(num_nodes, num_nodes), dtype=datetime)
for i in range(num_nodes):
    for j in range(num_nodes):
        M_ij[i][j] = T_H_U[i] + T_ij[i][j] - T_H_L[j]
print(M_ij)
M = timedelta(hours=24).total_seconds()  # in hours
