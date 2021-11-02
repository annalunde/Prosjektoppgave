import pandas as pd
from sklearn.metrics.pairwise import haversine_distances
from math import radians, degrees
from decouple import config
import numpy as np
from datetime import datetime, timedelta

# Sets
n = 24  # number of pickup nodes
num_vehicles = 4
num_nodes = 2 * n
num_nodes_and_depots = 2 * num_vehicles + 2 * n

# Costs and penalties
C_D = [1, 1, 1, 1, 1, 1]  # per vehicle
C_F = 1
C_T = 1

# Capacity per vehicle
Q_S = [16, 16, 16, 16]
Q_W = [1, 0, 1, 1]

# Allowed excess ride time
F = 2

# Different parameters per node
df = pd.read_csv(config("data_path_test"), nrows=n)

# Load for each request
L_S = df["Number of Passengers"].tolist()
L_W = df["Wheelchair"].tolist()

# Lat and lon for each request
origin_lat_lon = list(zip(np.deg2rad(df["Origin Lat"]), np.deg2rad(df["Origin Lng"])))
destination_lat_lon = list(
    zip(np.deg2rad(df["Destination Lat"]), np.deg2rad(df["Destination Lng"]))
)
request_lat_lon = origin_lat_lon + destination_lat_lon

# Positions in degrees
origin_lat_lon_deg = list(zip(df["Origin Lat"], df["Origin Lng"]))
destination_lat_lon_deg = list(zip(df["Destination Lat"], df["Destination Lng"]))
request_lat_lon_deg = origin_lat_lon_deg + destination_lat_lon_deg

vehicle_lat_lon = []
vehicle_lat_lon_deg = []

# Origins for each vehicle
for i in range(num_vehicles):
    vehicle_lat_lon.append((radians(59.946829115276145), radians(10.779841653639243)))
    vehicle_lat_lon_deg.append((59.946829115276145, 10.779841653639243))

# Destinations for each vehicle
for i in range(num_vehicles):
    vehicle_lat_lon.append((radians(59.946829115276145), radians(10.779841653639243)))
    vehicle_lat_lon_deg.append((59.946829115276145, 10.779841653639243))

# Positions
lat_lon = request_lat_lon + vehicle_lat_lon
Position = request_lat_lon_deg + vehicle_lat_lon_deg

# Distance matrix
D_ij = haversine_distances(lat_lon, lat_lon) * 6371

# Travel time matrix
speed = 40

T_ij = np.empty(shape=(num_nodes_and_depots, num_nodes_and_depots), dtype=timedelta)

for i in range(num_nodes_and_depots):
    for j in range(num_nodes_and_depots):
        T_ij[i][j] = timedelta(hours=(D_ij[i][j] / speed))

# Time windows
T_S_L = pd.to_datetime(df["T_S_L_P"]).tolist() + pd.to_datetime(df["T_S_L_D"]).tolist()
T_S_U = pd.to_datetime(df["T_S_U_P"]).tolist() + pd.to_datetime(df["T_S_U_D"]).tolist()
T_H_L = pd.to_datetime(df["T_H_L_P"]).tolist() + pd.to_datetime(df["T_H_L_D"]).tolist()
T_H_U = pd.to_datetime(df["T_H_U_P"]).tolist() + pd.to_datetime(df["T_H_U_D"]).tolist()

# Big M
# dette må ses på - noen blir negative
M_ij = np.empty(shape=(num_nodes, num_nodes), dtype=datetime)
for i in range(num_nodes):
    for j in range(num_nodes):
        M_ij[i][j] = T_H_U[i] + T_ij[i][j] - T_H_L[j]

M = timedelta(hours=2).total_seconds()  # in hours
