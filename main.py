import time
import pandas as pd
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from decouple import config
from datetime import datetime, timedelta
from Models import *
from Models.initial_model import InitialModel
from Models.reoptimization_model import ReoptModel


def main(num_events, sleep, start_time, tuning):
    """
    This function performs a run for the DDDARP problem, where requests that are known in advance are planned and routed initially,
    as well as new requests are received throughout the day. When a new request arrives, a reoptimization model is utilized to first
    decide if the new request is accepted or rejected, and if accepted, a new optimal route is planned based off of the earlier plan
    and the new request.
    """

    # Initial Route Plan
    print("Running Initial Model")
    runtime_track = []
    init_model = InitialModel()
    initial_route_plan = init_model.run_model()
    num_requests = init_model.get_n()
    rejected = []
    runtime_track.append([num_requests, (datetime.now() - start_time).total_seconds()])

    # Event Based Rerouting
    for i in range(num_events):
        print("Event Based Reoptimization")
        first = True if i == 0 else False
        event = get_event(i, tuning)
        num_requests += 1
        reopt_model = ReoptModel(
            initial_route_plan, event, num_requests, first, rejected
        )
        reopt_plan, rejected_after, num_unused_vehicles = reopt_model.run_model()
        if i != num_events - 1:
            print("Waiting for new request")
        time.sleep(sleep)
        initial_route_plan = reopt_plan
        runtime_track.append(
            [num_requests, (datetime.now() - start_time).total_seconds()]
        )
        rejected = rejected_after

    df = pd.DataFrame(runtime_track, columns=["Number of Requests", "Solution Time"])
    plot(df)

    print(
        "Service Rate Whole: ",
        str(round(100 * (num_requests - len(rejected)) / (num_requests), 2)) + "%",
    )

    print(
        "Service Rate of New Events: ",
        str(round(100 * (num_events - len(rejected)) / (num_events), 2)) + "%",
    )

    print(
        "Number of Vehicles Not Used: ",
        num_unused_vehicles,
    )


def plot(df):
    ax = plt.gca()
    df.plot(kind="line", x="Number of Requests", y="Solution Time", color="pink", ax=ax)
    # df.plot(kind='line',x='name',y='num_pets', , ax=ax)

    # the plot gets saved to 'solution_time.png'
    plt.savefig("solution_time.png")

    plt.show()


def get_event(i, tuning):
    if tuning:
        df = pd.read_csv(config("data_path_tuning_events"))
        return df.iloc[i]
    else:
        df = pd.read_csv(config("data_path_events"))
        return df.iloc[i]


if __name__ == "__main__":
    num_events = 5
    sleep = 1
    start_time = datetime.now()
    tuning = True
    main(num_events, sleep, start_time, tuning)
