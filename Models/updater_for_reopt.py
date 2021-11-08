import datetime
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from reoptimization_config import *


class Updater:
    def __init__(self, current_route_plan, event, num_requests, first):
        self.route_plan = current_route_plan  # dictionary with variable values
        self.event = event  # dataframe row
        self.num_requests = num_requests
        self.first = first

    def update(self):
        pickups_remaining = []  # set of remaining pick-up nodes
        pickups_new = []  # set of new pick-up nodes
        pickups = []  # set of all pick-up nodes
        nodes_remaining = []  # set of remaining pick-up and drop-off nodes
        nodes_new = []  # set of new pick-up and drop-off nodes
        nodes = []  # set of all pick-up and drop-off nodes
        E_S = []  # standard seats load of vehicle k when event occurs
        E_W = []  # wheelchair load of vehickle k when event occurs
        T_O = []  # time of service of request i in original plan

        # Sets
        n = self.num_requests  # number of pickup nodes
        num_nodes = 2 * n
        num_nodes_and_depots = 2 * num_vehicles + 2 * n

        # CREATE NEW SETS
        P_N.append(self.num_requests)
        N_N.append(self.num_requests)
        N_N.append(2*self.num_requests)

        # CREATE ALL SETS
        P = [i for i in range(self.num_requests)]
        N = [i for i in range(2*self.num_requests)]

        # FETCH DATA
        if self.first:
            df = pd.read_csv(config("data_path_test"), nrows=self.num_requests-1)
            df = df.append(self.event)
            df.to_csv(f"data_requests_for:{self.num_requests}")
        
        else:
            df = pd.read_csv(f"data_requests_for:{self.num_requests-1}")
            df = df.append(self.event)
            df.to_csv(f"data_requests_for:{self.num_requests}")
            

        # CREATE REMAINING SETS
        time_now = event["Request Creation Time"]
        time_request = event["Requested Pickup Time"]
        time_request = event["Requested Dropoff Time"] if event["Requested Pickup Time"].isnull().sum()
        time_request_U = time_request + timedelta(hours=H)
        time_request_L = time_request - timedelta(hours=H) if (time_request - timedelta(hours=H)) > time_now else time_now

        for t_i in self.route_plan["t"].keys():
            #T_O.append(self.route_plan["t"][t_i]) #NOTE if for all pickup nodes
            if self.route_plan["t"][t_i] < time_request_U and self.route_plan["t"][t_i] > time_request_L:
                if t_i[0] <= self.num_requests - 1:
                    P_R.append(t_i[0])
                    T_O.append(self.route_plan["t"][t_i]) #NOTE if only pickup nodes that are open
                    N_R.append(t_i[0])
                    N_R.append(t_i[0] + self.num_requests)
                else:
                    N_R.append(t_i[0])
            
    

        for k in vehicles:
            for i in P_R:
                E_S.append(self.route_plan["q_S"][i, k])
                E_W.append(self.route_plan["q_W"][i, k])

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

        # Positions in degrees
        origin_lat_lon_deg = list(zip(df["Origin Lat"], df["Origin Lng"]))
        destination_lat_lon_deg = list(
            zip(df["Destination Lat"], df["Destination Lng"])
        )
        request_lat_lon_deg = origin_lat_lon_deg + destination_lat_lon_deg

        vehicle_lat_lon = []
        vehicle_lat_lon_deg = []

        # Origins for each vehicle
        for i in range(num_vehicles):
            vehicle_lat_lon.append(
                (radians(59.946829115276145), radians(10.779841653639243))
            )
            vehicle_lat_lon_deg.append((59.946829115276145, 10.779841653639243))

        # Destinations for each vehicle
        for i in range(num_vehicles):
            vehicle_lat_lon.append(
                (radians(59.946829115276145), radians(10.779841653639243))
            )
            vehicle_lat_lon_deg.append((59.946829115276145, 10.779841653639243))

        # Positions
        lat_lon = request_lat_lon + vehicle_lat_lon
        Position = request_lat_lon_deg + vehicle_lat_lon_deg

        # Distance matrix
        D_ij = haversine_distances(lat_lon, lat_lon) * 6371

        # Travel time matrix
        speed = 40

        T_ij = np.empty(
            shape=(num_nodes_and_depots, num_nodes_and_depots), dtype=timedelta
        )

        for i in range(num_nodes_and_depots):
            for j in range(num_nodes_and_depots):
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
        M_ij = np.empty(shape=(num_nodes, num_nodes), dtype=datetime)
        for i in range(num_nodes):
            for j in range(num_nodes):
                M_ij[i][j] = T_H_U[i] + T_ij[i][j] - T_H_L[j]

        # return P_R, P_N, P, N_R, N_N, N, E_S, E_W, T_O

    def update_time_windows(self, i):
            T_S_L[i] -= timedelta(minutes=5)
            T_H_L[i] -= timedelta(minutes=5)
            T_S_U[i] += timedelta(minutes=5)
            T_H_U[i] += timedelta(minutes=5)

    def remove_rejected_request(self, i):

def main():
    updater = None

    try:
        updater = Updater()

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()

