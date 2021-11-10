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
    def __init__(self, current_route_plan, event, num_requests, first):
        self.route_plan = current_route_plan  # dictionary with variable values
        self.event = event  # dataframe row
        self.num_requests = num_requests
        self.first = first

    def update(self):
        pickups_remaining = []  # set of remaining pick-up nodes
        pickups_new = []  # set of new pick-up nodess
        pickups = []  # set of all pick-up nodes
        nodes_remaining = []  # set of remaining pick-up and drop-off nodes
        nodes_new = []  # set of new pick-up and drop-off nodes
        nodes = []  # set of all pick-up and drop-off nodes
        E_S = (
            []
        )  # standard seats load of vehicle k in lower time window of rolling horizon
        E_W = (
            []
        )  # wheelchair load of vehickle k in lower time window of rolling horizon
        T_O = []  # time of service of request i in original plan
        vehicle_times = (
            {}
        )  # dictionary used to find start and end point of each vehicle within opened time frame
        fixate_x = []   # a list of all x_ijk variables that must be set to one
        fixate_t = {}   # a dict of all t variables that must be fixed to its value

        # Sets
        n = self.num_requests  # number of pickup nodes
        self.num_nodes = 2 * n
        self.num_nodes_and_depots = 2 * num_vehicles + 2 * n

        # CREATE NEW SETS
        pickups_new.append(self.num_requests - 1)
        nodes_new.append(self.num_requests - 1)
        nodes_new.append(2 * (self.num_requests - 1))

        # CREATE ALL SETS
        pickups = [i for i in range(self.num_requests)]
        nodes = [i for i in range(2 * self.num_requests)]
        vehicles = [i for i in range(num_vehicles)]
        nodes_depots = [i for i in range(self.num_nodes_and_depots)]

        # FETCH DATA
        if self.first:
            df = pd.read_csv(config("data_path_test"), nrows=self.num_requests - 1)
            df = df.append(self.event, ignore_index=True)
            df.to_csv(f"data_requests_for:{self.num_requests}.csv")

        else:
            df = pd.read_csv(f"data_requests_for:{self.num_requests-1}.csv")
            df = df.append(self.event, ignore_index=True)
            df.to_csv(f"data_requests_for:{self.num_requests}.csv")

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
            T_O.append(self.route_plan["t"][t_i])
            if (
                pd.to_datetime(self.route_plan["t"][t_i], unit="s") < time_request_U
                and pd.to_datetime(self.route_plan["t"][t_i], unit="s") > time_request_L
            ):
                if t_i <= self.num_requests - 1:
                    pickups_remaining.append(t_i)
                    nodes_remaining.append(t_i)
                    vehicle_times[t_i] = pd.to_datetime(
                        self.route_plan["t"][t_i], unit="s"
                    )
                else:
                    nodes_remaining.append(t_i)
                    vehicle_times[t_i] = pd.to_datetime(
                        self.route_plan["t"][t_i], unit="s"
                    )


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

        # Origins for each vehicle
        origins = {}
        for t in vehicle_times.keys():
            v = next(
                a[2]
                for a in self.route_plan["x"].keys()
                if a[1] == t and self.route_plan["x"][a] == 1
            )
            if v not in origins.keys():
                origins[v] = (vehicle_times[t], t)
            else:
                if vehicle_times[t] < origins[v][0]:
                    origins[v] = (vehicle_times[t], t)
        for k in vehicles:
            # A vehicle might not be used
            if k not in origins.keys():
                origins[k] = ()

        for item in sorted(origins.items()):
            if len(item[1]) == 0:
                vehicle_lat_lon.append(
                    (radians(59.946829115276145), radians(10.779841653639243))
                )

            else:
                if item[1][1] <= self.num_requests - 1:
                    vehicle_lat_lon.append(
                        (
                            np.deg2rad(df.loc[item[1][1], "Origin Lat"]),
                            np.deg2rad(df.loc[item[1][1], "Origin Lng"]),
                        )
                    )
                else:
                    vehicle_lat_lon.append(
                        (
                            np.deg2rad(
                                df.loc[
                                    (item[1][1] - self.num_requests - 1),
                                    "Destination Lat",
                                ]
                            ),
                            np.deg2rad(
                                df.loc[
                                    (item[1][1] - self.num_requests - 1),
                                    "Destination Lng",
                                ]
                            ),
                        )
                    )

        # Loads of each vehicle
        for k in sorted(origins.keys()):
            if (
                len(origins[k]) == 0
            ):  # the vehicle is not used and get default value of load
                E_S.append(0)
                E_W.append(0)
            else:
                E_S.append(self.route_plan["q_S"][origins[k][1], k])
                E_W.append(self.route_plan["q_W"][origins[k][1], k])

        # Destinations for each vehicle
        destinations = {}
        for t in vehicle_times.keys():
            v = next(
                a[2]
                for a in self.route_plan["x"].keys()
                if a[1] == t and self.route_plan["x"][a] == 1
            )
            if v not in destinations.keys():
                destinations[v] = (vehicle_times[t], t)
            else:
                if vehicle_times[t] > destinations[v][0]:
                    destinations[v] = (vehicle_times[t], t)
        for k in vehicles:
            # A vehicle might not be used
            if k not in destinations.keys():
                destinations[k] = ()

        for item in sorted(destinations.items()):
            if len(item[1]) == 0:
                vehicle_lat_lon.append(
                    (radians(59.946829115276145), radians(10.779841653639243))
                )

            else:
                if item[1][1] <= self.num_requests - 1:
                    vehicle_lat_lon.append(
                        (
                            np.deg2rad(df.loc[item[1][1], "Origin Lat"]),
                            np.deg2rad(df.loc[item[1][1], "Origin Lng"]),
                        )
                    )
                else:
                    vehicle_lat_lon.append(
                        (
                            np.deg2rad(
                                df.loc[
                                    item[1][1] - self.num_requests - 1,
                                    "Destination Lat",
                                ]
                            ),
                            np.deg2rad(
                                df.loc[
                                    item[1][1] - self.num_requests - 1,
                                    "Destination Lng",
                                ]
                            ),
                        )
                    )

        # Find x-variables to fixate
        for x in nodes_depots - nodes_remaining:
            fixate_x.append(
                next(
                    a
                    for a in self.route_plan["x"].keys()
                    if a[0] == x or a[1] == x  and self.route_plan["x"][a] == 1
                )
            )
        # need to add origins and destinations for vehicles within time window
        for t in origins.keys():
            fixate_x.append(next(
                    a
                    for a in self.route_plan["x"].keys()
                    if a[2] == t and a[1] == origins[t][1]  and self.route_plan["x"][a] == 1
                ))
         for t in destinations.keys():
            fixate_x.append(next(
                    a
                    for a in self.route_plan["x"].keys()
                    if a[2] == t and a[0] == destinations[t][1]  and self.route_plan["x"][a] == 1
                ))     
         # need to remove x-variables for vehicles not initially used
         not_used_vehicles = [k for k in origins.keys() if len(origins[k])==0] 
         fixate_x = filter(lambda x: x[0] in not_used_vehicles or x[1] in not_used_vehicles,fixate_x)

        # Find t-variables to fixate
        for t_i in self.route_plan["t"].keys():
            if pd.to_datetime(self.route_plan["t"][t_i], unit="s") <= time_request_L:
                fixate_t[t_i] = self.route_plan["t"][t_i]
                

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
                T_ij[i][j] = timedelta(hours=(D_ij[i][j] / speed))

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

        # Big M
        M_ij = np.empty(shape=(self.num_nodes, self.num_nodes), dtype=datetime)
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                M_ij[i][j] = T_H_U[i] + T_ij[i][j] - T_H_L[j]

        return (
            pickups_remaining,
            pickups_new,
            pickups,
            nodes_depots,
            nodes_remaining,
            nodes_new,
            nodes,
            fixate_x,
            E_S,
            E_W,
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
            
        )
