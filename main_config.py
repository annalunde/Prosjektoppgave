from datetime import datetime, timedelta
from decouple import config


vehicles_set = [2, 3, 4]  # this also gives the number of vehicles for initial model

sleep = 0.01

initial_events_path = config("data_path_runtime_init")
test_instance = False
complexity_instance = False
runtime_instance = True
valid_inequalities = True
subtour = False
