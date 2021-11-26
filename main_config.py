from datetime import datetime, timedelta
from decouple import config


sleep = 0.01

initial_events_path = config("data_path_ride_sharing_init")
test_instance = False
complexity_instance = False
runtime_instance = False
ride_sharing_instance = True
valid_inequalities = True
subtour = False
