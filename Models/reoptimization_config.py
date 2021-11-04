# Reoptimization Model
import numpy as np
from datetime import datetime, timedelta
from scipy.spatial import distance

# Vehicles
num_vehicles = 3

# Costs and penalties
C_D = [1, 1, 1, 1, 1, 1]  # per vehicle
C_F = 1
C_T = 1
C_R = 10  # lost revenue from not serving a request
C_K = [100, 100, 100, 100, 100]  # cost of using vehicle k
C_O = 10  # cost of deviation from original plan

# Capacity per vehicle
Q_S = [16, 16, 16, 16]
Q_W = [1, 1, 1, 1]

# Allowed excess ride time
F = 0.5

# Number of hours to open to reoptimize
H = 1
