# Reoptimization Model
import numpy as np
from datetime import datetime, timedelta
from scipy.spatial import distance

# Vehicles
num_vehicles = 2  # NOTE: cannot be set lower than initial config num_vehicles

# Costs and penalties
C_D = [1, 1, 1, 1, 1, 1]  # per vehicle
C_F = 1
C_T = 1
C_R = 10  # lost revenue from not serving a request
C_K = [100, 100, 100, 100, 100]  # cost of using vehicle k
C_O = 10  # cost of deviation from original plan

# Capacity per vehicle
Q_S = [5, 5, 5, 5]
Q_W = [1, 1, 1, 1]

# Allowed excess ride time
F = 0.5

# Number of hours to open to reoptimize
H = 1

# Big M
M = timedelta(hours=2).total_seconds()  # in hours

# Service time
S = timedelta(minutes=2).total_seconds()
