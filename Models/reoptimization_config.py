# Reoptimization Model
import numpy as np
from datetime import datetime, timedelta
from scipy.spatial import distance
from models.initial_config import *


# Vehicles
num_vehicles = 5  # this also gives the number of vehicles for initial model

# Costs and penalties
C_D = 1  # per vehicle
C_F = 60
C_T = 60
C_R = 60  # lost revenue from not serving a request
C_K = 55  # cost of using vehicle k
C_O = 60  # cost of deviation from original plan

# Capacity per vehicle
Q_S = 5
Q_W = 1

# Allowed excess ride time
F = 0.5

# Number of hours to open to reoptimize
H = 0.5

# Service time
S = timedelta(minutes=2).total_seconds() / 3600
