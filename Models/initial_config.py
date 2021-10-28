# Model 1
import numpy as np
from datetime import datetime, timedelta
from scipy.spatial import distance

# Sets
n = 10 # number of pickup nodes
num_vehicles = 3
num_nodes = 2 * n
num_nodes_and_depots = 2 * num_vehicles + 2 * n

# Parameters
C_D = [1, 1, 1]
"""
D_ij = [
        [0, 1, 4, 1, 3, 3],
        [1, 0, 3, 2, 2, 2],
        [4, 3, 0, 3, 2, 4],
        [1, 2, 3, 0, 2, 2],
        [3, 1, 2, 2, 0, 3],
        [3, 2, 4, 2, 3, 0]
        ]  # in kms
"""
Position = [
    (2, 3),
    (2, 6),
    (12, 4),
    (6, 10),
    (1, 4),
    (11, 11),
    (3, 3),
    (13, 0),
    (8, 4),
    (13, 9),
    (9.5, 7.5),
    (6.5, 1),
    (3, 2),
    (4, 5),
    (10, 10),
    (10, 1),
    (9, 9),
    (6, 6),
    (2, 10),
    (4, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (1, 1),
    (1, 1),
    (1, 1)
]


D_ij = distance.cdist(Position, Position, "euclidean")

speed = 40

T_ij = np.empty(shape=(num_nodes_and_depots, num_nodes_and_depots), dtype=timedelta)

for i in range(num_nodes_and_depots):
    for j in range(num_nodes_and_depots):
        T_ij[i][j] = timedelta(hours=(D_ij[i][j] / speed))


# C_R = 10
C_F = 1
C_T = 1
Q_S = [5, 4, 16]
Q_W = [1, 0 ,2]
L_S = [1, 2, 5, 2, 5, 1, 0, 4, 2, 8]  # Load for each request
L_W = [0, 0, 0, 0, 2, 0, 1, 1, 0, 1]  # Wheelchair load for request

"""
T_ij = [
    [timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=6)],
    [timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=5)],
    [timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=7)],
    [timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=5)],
    [timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=0), timedelta(hours=0, minutes=6)],
    [timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=7), timedelta(hours=0, minutes=5), timedelta(hours=0, minutes=6), timedelta(hours=0, minutes=0)]
]
"""
T_S_L = [
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:55:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:25:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:40:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:55:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:00:00", "%Y-%m-%d %H:%M:%S"),

    datetime.strptime("2021-10-13 10:20:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:50:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:20:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:50:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:20:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:30:00", "%Y-%m-%d %H:%M:%S"),
]

T_S_U = [
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:50:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:05:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:35:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:10:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:10:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:05:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:30:00", "%Y-%m-%d %H:%M:%S"),

    datetime.strptime("2021-10-13 10:25:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:40:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:45:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:50:00", "%Y-%m-%d %H:%M:%S"),
]

T_H_L = [
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:45:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:50:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:50:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 09:45:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:50:00", "%Y-%m-%d %H:%M:%S"),

    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:20:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:40:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:45:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:15:00", "%Y-%m-%d %H:%M:%S"),
]

T_H_U = [
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:50:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:45:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:20:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:20:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:40:00", "%Y-%m-%d %H:%M:%S"),

    datetime.strptime("2021-10-13 10:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 10:50:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:15:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:40:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:10:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:00:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 12:30:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 11:40:00", "%Y-%m-%d %H:%M:%S"),
    datetime.strptime("2021-10-13 13:00:00", "%Y-%m-%d %H:%M:%S"),
]

F = 2
M_ij = np.empty(shape=(num_nodes, num_nodes), dtype=datetime)
for i in range(num_nodes):
    for j in range(num_nodes):
        M_ij[i][j] = T_H_U[i] + T_ij[i][j] - T_H_L[j]
M = timedelta(hours=24).total_seconds()  # in hours