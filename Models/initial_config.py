import pandas as pd
from sklearn.metrics.pairwise import haversine_distances
from math import radians, degrees
from decouple import config
import numpy as np
from datetime import datetime, timedelta
from models.reoptimization_config import *
from main_config import *


# Costs and penalties
C_D = 1  # per vehicle
C_F = 60
C_T = 60

# Capacity per vehicle
Q_S = 5
Q_W = 1

# Allowed excess ride time
F = 0.5

# Weighting of Operational Costs vs Quality of Service
alpha = 0.5

# Service time
S = timedelta(minutes=2).total_seconds() / 3600
