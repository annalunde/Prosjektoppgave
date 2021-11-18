import time
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from decouple import config
from models import *
from models.initial_model import InitialModel
from models.reoptimization_model import ReoptModel


def main(num_events, sleep=60):
    """
    This function performs a run for the DDDARP problem, where requests that are known in advance are planned and routed initially,
    as well as new requests are received throughout the day. When a new request arrives, a reoptimization model is utilized to first
    decide if the new request is accepted or rejected, and if accepted, a new optimal route is planned based off of the earlier plan
    and the new request.
    """

    # Initial Route Plan
    print("Running Initial Model")
    init_model = InitialModel()
    initial_route_plan = init_model.run_model()
    num_requests = init_model.get_n()
    rejected = []

    # Event Based Rerouting
    for i in range(num_events):
        print("Event Based Reoptimization")
        first = True if i == 0 else False
        event = get_event(i)
        num_requests += 1
        reopt_model = ReoptModel(
            initial_route_plan, event, num_requests, first, rejected
        )
        reopt_plan, rejected, num_unused_vehicles = reopt_model.run_model()
        if i != num_events - 1:
            print("Waiting for new request")
        time.sleep(sleep)
        initial_route_plan = reopt_plan
    print(
        "Service Rate: ",
        str(round(100 * (num_requests - len(rejected)) / (num_requests), 2)) + "%",
    )
    print(
        "Number of Vehicles Not Used: ",
        num_unused_vehicles,
    )


def get_event(i):
    df = pd.read_csv(config("data_path_events"))
    return df.iloc[i]


if __name__ == "__main__":
    num_events = 24
    sleep = 1
    main(num_events, sleep)
