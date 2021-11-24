import datetime
import pandas as pd
import gurobipy as gp
from decouple import config
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from math import radians, degrees
from models.reoptimization_config import *
from sklearn.metrics.pairwise import haversine_distances


class Updater:
    def __init__(
        self, current_route_plan, event, num_requests, first, rejected, subtour
    ):
        self.route_plan = current_route_plan  # dictionary with variable values
        self.event = event  # dataframe row
        self.num_requests = num_requests
        self.first = first
        self.rejected = rejected
        self.subtour = subtour

    def update(self):
        pickups_remaining = []  # set of remaining pick-up nodes
        pickups_new = []  # set of new pick-up nodess
        pickups = []  # set of all pick-up nodes
        nodes_remaining = []  # set of remaining pick-up and drop-off nodes
        nodes_new = []  # set of new pick-up and drop-off nodes
        nodes = []  # set of all pick-up and drop-off nodes
        T_O_t = {}  # time of service of request i in original plan
        vehicle_times = (
            {}
        )  # dictionary used to find start and end point of each vehicle within opened time frame
        fixate_x = []  # a list of all x_ijk variables that must be set to one
        fixate_t = {}  # a dict of all t variables that must be fixed to its value

        # Sets
        self.num_nodes = 2 * self.num_requests
        self.num_nodes_and_depots = 2 * num_vehicles + 2 * self.num_requests

        # CREATE NEW SETS
        pickups_new.append(self.num_requests - 1)
        nodes_new.append(self.num_requests - 1)
        nodes_new.append(2 * (self.num_requests) - 1)

        # CREATE ALL SETS
        pickups = [i for i in range(self.num_requests)]
        nodes = [i for i in range(2 * self.num_requests)]
        vehicles = [i for i in range(num_vehicles)]
        nodes_depots = [i for i in range(self.num_nodes_and_depots)]
        pickups_previous = [i for i in range(len(pickups) - 1)]
        pickups_previous_not_rejected = []
        nodes_previous_not_rejected = []
        for i in pickups_previous:
            if i not in self.rejected:
                pickups_previous_not_rejected.append(i)
                nodes_previous_not_rejected.append(i)
                nodes_previous_not_rejected.append(self.num_requests + i)

        # FETCH DATA
        if self.first:
            df = pd.read_csv(
                config("data_path_test_instances_init"), nrows=self.num_requests - 1
            )
            df = df.append(self.event, ignore_index=True)
            df.to_csv(
                "Data/Running/data_requests_for:" + str(self.num_requests) + ".csv"
            )

        else:
            df = pd.read_csv(
                "Data/Running/data_requests_for:" + str(self.num_requests - 1) + ".csv"
            )
            df = df.append(self.event, ignore_index=True)
            df.to_csv(
                "Data/Running/data_requests_for:" + str(self.num_requests) + ".csv"
            )

        # CREATE REMAINING SETS
        time_now = pd.to_datetime(self.event["Request Creation Time"])
        time_request = pd.to_datetime(self.event["Requested Pickup Time"])
        time_request = (
            pd.to_datetime(self.event["Requested Dropoff Time"])
            if pd.isna(self.event["Requested Pickup Time"])
            else time_request
        )
        time_request_U = time_request + timedelta(hours=H)
        time_request_L = (
            time_request - timedelta(hours=H)
            if (time_request - timedelta(hours=H)) > time_now
            else time_now
        )

        for t_i in self.route_plan["t"].keys():
            if t_i < self.num_requests - 1:
                T_O_t[t_i] = self.route_plan["t"][t_i]
            else:
                T_O_t[t_i + 1] = self.route_plan["t"][t_i]

            if (
                pd.to_datetime(self.route_plan["t"][t_i], unit="h") < time_request_U
                and pd.to_datetime(self.route_plan["t"][t_i], unit="h") > time_request_L
            ):
                if t_i < self.num_requests - 1:
                    pickups_remaining.append(t_i)
                    nodes_remaining.append(t_i)
                    vehicle_times[t_i] = pd.to_datetime(
                        self.route_plan["t"][t_i], unit="h"
                    )
                else:
                    nodes_remaining.append(t_i + 1)
                    vehicle_times[t_i] = pd.to_datetime(
                        self.route_plan["t"][t_i], unit="h"
                    )
        filter_rejected = []
        for j in nodes_remaining:
            if j in self.rejected:
                filter_rejected.append(j)

        for h in filter_rejected:
            nodes_remaining.remove(h)
            if (h + self.num_requests) in nodes_remaining:
                nodes_remaining.remove(h + self.num_requests)
            pickups_remaining.remove(h)

        for i in nodes_new:
            T_O_t[i] = -1
        T_O = []
        for i in sorted(T_O_t.keys()):
            T_O.append(T_O_t[i])

        # Load for each request
        L_S = df["Number of Passengers"].tolist()
        L_W = df["Wheelchair"].tolist()

        # Lat and lon for each request
        origin_lat_lon = list(
            zip(np.deg2rad(df["Origin Lat"]), np.deg2rad(df["Origin Lng"]))
        )
        destination_lat_lon = list(
            zip(
                np.deg2rad(df["Destination Lat"]),
                np.deg2rad(df["Destination Lng"]),
            )
        )
        request_lat_lon = origin_lat_lon + destination_lat_lon

        vehicle_lat_lon = []

        for item in range(num_vehicles):
            vehicle_lat_lon.append(
                (radians(59.946829115276145), radians(10.779841653639243))
            )

        not_used_vehicles = [
            k
            for k in vehicles
            if self.route_plan["x"][
                (
                    2 * (self.num_requests - 1) + k,
                    2 * (self.num_requests - 1) + k + num_vehicles,
                    k,
                )
            ]
            == 1
        ]

        for item in range(num_vehicles):
            vehicle_lat_lon.append(
                (radians(59.946829115276145), radians(10.779841653639243))
            )

        # FIND X-VARIABLES TO FIXATE
        for a in self.route_plan["x"].keys():
            if self.route_plan["x"][a] == 1:
                b = None
                if a[0] > self.num_requests - 2:
                    b = ((a[0] + 1), a[1], a[2])
                    if a[0] >= 2 * (self.num_requests - 1):
                        b = ((a[0] + 2), a[1], a[2])
                if a[1] > self.num_requests - 2:
                    if b:
                        if a[1] >= 2 * (self.num_requests - 1):
                            b = (b[0], (b[1] + 2), b[2])
                        else:
                            b = (b[0], (b[1] + 1), b[2])
                    else:
                        if a[1] >= 2 * (self.num_requests - 1):
                            b = (a[0], (a[1] + 2), a[2])
                        else:
                            b = (a[0], (a[1] + 1), a[2])
                if not b:
                    b = a
                fixate_x.append(b)

        filtered = []
        for el in fixate_x:
            if el[0] in nodes_remaining and el[1] in nodes_remaining:
                filtered.append(el)
        for e in filtered:
            fixate_x.remove(e)

        # need to remove x-variables for vehicles not initially used
        fixate_x = [el for el in fixate_x if el[2] not in not_used_vehicles]

        # FIND T-VARIABLES TO FIXATE
        for t_i in self.route_plan["t"].keys():
            if (
                pd.to_datetime(self.route_plan["t"][t_i], unit="h")
                <= time_request_L
                # and t_i not in self.rejected
            ):
                c = None
                if t_i > self.num_requests - 2:
                    c = t_i + 1
                    if t_i >= 2 * (self.num_requests - 1):
                        c = t_i + 2
                if not c:
                    c = t_i
                fixate_t[c] = self.route_plan["t"][t_i]

        # Positions
        lat_lon = request_lat_lon + vehicle_lat_lon

        # Distance matrix
        D_ij = haversine_distances(lat_lon, lat_lon) * 6371
        # Travel time matrix
        speed = 40

        T_ij = np.empty(
            shape=(self.num_nodes_and_depots, self.num_nodes_and_depots),
            dtype=timedelta,
        )

        for i in range(self.num_nodes_and_depots):
            for j in range(self.num_nodes_and_depots):
                T_ij[i][j] = (
                    timedelta(hours=(D_ij[i][j] / speed)).total_seconds() / 3600
                )

        # Time windows
        T_S_L = (
            pd.to_datetime(df["T_S_L_P"]).tolist()
            + pd.to_datetime(df["T_S_L_D"]).tolist()
        )
        T_S_U = (
            pd.to_datetime(df["T_S_U_P"]).tolist()
            + pd.to_datetime(df["T_S_U_D"]).tolist()
        )
        T_H_L = (
            pd.to_datetime(df["T_H_L_P"]).tolist()
            + pd.to_datetime(df["T_H_L_D"]).tolist()
        )
        T_H_U = (
            pd.to_datetime(df["T_H_U_P"]).tolist()
            + pd.to_datetime(df["T_H_U_D"]).tolist()
        )
        T_S_L = [i.timestamp() / 3600 for i in T_S_L]
        T_S_U = [i.timestamp() / 3600 for i in T_S_U]
        T_H_L = [i.timestamp() / 3600 for i in T_H_L]
        T_H_U = [i.timestamp() / 3600 for i in T_H_U]

        # Big M
        M_ij = np.empty(shape=(self.num_nodes, self.num_nodes), dtype=datetime)
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                M_ij[i][j] = T_H_U[i] + T_ij[i][j] - T_H_L[j]

        return (
            pickups_remaining,
            pickups_new,
            pickups,
            pickups_previous_not_rejected,
            nodes_previous_not_rejected,
            nodes_depots,
            nodes_remaining,
            nodes_new,
            nodes,
            fixate_x,
            fixate_t,
            T_O,
            D_ij,
            T_ij,
            T_S_L,
            T_S_U,
            T_H_L,
            T_H_U,
            M_ij,
            L_S,
            L_W,
            self.rejected,
        )
