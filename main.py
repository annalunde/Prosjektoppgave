import time
import json
import pandas as pd
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from decouple import config
from datetime import datetime, timedelta
from models import *
from main_config import *
from models.initial_model import InitialModel
from models.initial_model_validineq import InitialModelValidIneq
from models.reoptimization_model import ReoptModel
from models.reoptimization_model_validineq import ReoptModelValidIneq


def main(
    num_events,
    sleep,
    start_time,
    test_instance,
    valid_ineq,
    subtour,
    complexity_instance,
    num_vehicles,
    n,
    runtime_instance,
    H,
    C_K,
    ride_sharing_instance,
):
    """
    This function performs a run for the DDDARP problem, where requests that are known in advance are planned and routed initially,
    as well as new requests are received throughout the day. When a new request arrives, a reoptimization model is utilized to first
    decide if the new request is accepted or rejected, and if accepted, a new optimal route is planned based off of the earlier plan
    and the new request.
    """

    # Initial Route Plan
    print("Running Initial Model")
    runtime_track = []
    init_model = (
        InitialModelValidIneq(subtour, num_vehicles, n)
        if valid_ineq
        else InitialModel(num_vehicles, n)
    )
    (
        initial_route_plan,
        unused_vehicles,
        operational,
        quality,
        ride_sharing,
        productivity,
    ) = init_model.run_model()
    num_requests = init_model.get_n()
    rejected = []
    runtime_track.append(
        [
            num_requests,
            (datetime.now() - start_time).total_seconds(),
            False,
            operational,
            quality,
            ride_sharing,
            productivity,
        ]
    )
    operational = None
    quality = 0
    cumulative_z = 0
    r_init = 0
    print("Unused vehicles after initial: ", unused_vehicles)

    # Event Based Rerouting
    for i in range(num_events):
        print("Event Based Reoptimization")
        first = True if i == 0 else False
        event = get_event(i, test_instance, complexity_instance, runtime_instance)
        num_requests += 1
        reopt_model = (
            ReoptModelValidIneq(
                initial_route_plan,
                event,
                num_requests,
                first,
                rejected,
                num_vehicles,
                H,
                C_K,
            )
            if valid_ineq
            else ReoptModel(initial_route_plan, event, num_requests, first, rejected, H)
        )
        (
            reopt_plan,
            rejected,
            num_unused_vehicles,
            operational,
            quality,
            single_z,
            unused_vehicles,
            ride_sharing,
            productivity,
        ) = reopt_model.run_model(unused_vehicles)
        if i != num_events - 1:
            print("Waiting for new request")
        time.sleep(sleep)
        initial_route_plan = reopt_plan
        rej = True if len(rejected) > r_init else False
        r_init = len(rejected)
        runtime_track.append(
            [
                num_requests,
                (datetime.now() - start_time).total_seconds(),
                rej,
                operational,
                (quality + single_z),
                ride_sharing,
                productivity,
            ]
        )
        print("Unused vehicles after event: ", unused_vehicles)
        if i != num_events - 1:
            cumulative_z += single_z

    df_runtime = pd.DataFrame(
        runtime_track,
        columns=[
            "Number of Requests",
            "Solution Time",
            "Rejected",
            "Operational",
            "Quality",
            "Ride Sharing",
            "Productivity",
        ],
    )
    # if n == 1:
    df_runtime.to_csv("Economic/ride_sharing_{}.csv".format(num_vehicles))
    """
    else:
        df_total = pd.read_csv("Runtime/runtime_{}.csv".format(num_vehicles))
        df_total = df_total.append(df_runtime, ignore_index=True)
        df_total.to_csv("Runtime/runtime_{}.csv".format(num_vehicles))"""
    # plot(df_runtime)

    print(
        "Service Rate Whole: ",
        str(round(100 * (num_requests - len(rejected)) / (num_requests), 2)) + "%",
    )
    if num_events > 0:
        print(
            "Service Rate of New Events: ",
            str(round(100 * (num_events - len(rejected)) / (num_events), 2)) + "%",
        )

        print(
            "Number of Vehicles Not Used: ",
            num_unused_vehicles,
        )
    print("Runtime: ", df_runtime.tail(1))

    return operational, quality + cumulative_z, df_runtime


def plot(df):
    ax = plt.gca()
    df.plot(kind="line", x="Number of Requests", y="Solution Time", color="pink", ax=ax)
    # df.plot(kind='line',x='name',y='num_pets', , ax=ax)

    # the plot gets saved to 'solution_time.png'
    plt.savefig("solution_time.png")

    plt.show()


def get_event(
    i, test_instance, complexity_instance, runtime_instance, ride_sharing_instance
):
    if test_instance:
        df = pd.read_csv(config("data_path_test_instances_events"))
        return df.iloc[i]
    if complexity_instance:
        df = pd.read_csv(config("data_path_complexity_events"))
        return df.iloc[i]
    if runtime_instance:
        df = pd.read_csv(config("data_path_runtime_events"))
        return df.iloc[i]
    if ride_sharing_instance:
        df = pd.read_csv(config("data_path_ride_sharing_events"))
        return df.iloc[i]
    else:
        df = pd.read_csv(config("data_path_events"))
        return df.iloc[i]


if __name__ == "__main__":
    vehicles_set = [2, 3, 4]
    C_K = 0  # cost of using vehicle k
    H = 0.25  # Number of hours to open to reoptimize
    for v in vehicles_set:
        start_time = datetime.now()
        num_vehicles = v
        num_events = 8
        n = 16  # number of pickup nodes
        operational, quality, runtime = main(
            num_events,
            sleep,
            start_time,
            test_instance,
            valid_inequalities,
            subtour,
            complexity_instance,
            num_vehicles,
            n,
            runtime_instance,
            H,
            C_K,
            ride_sharing_instance,
        )
