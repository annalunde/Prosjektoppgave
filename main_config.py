from datetime import datetime, timedelta
from decouple import config

n = 10  # number of pickup nodes
num_events = 5
num_vehicles = 3  # this also gives the number of vehicles for initial model

sleep = 0.01
start_time = datetime.now()
total_time = 60 * 60

 = config("")
initial_events_path = config("data_path_complexity_init")
test_instance = False
complexity_instance = True
valid_inequalities = True
subtour = False
