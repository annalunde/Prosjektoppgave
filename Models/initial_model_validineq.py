import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
import graphviz
from models.initial_config import *
from main_config import *

# from models.reoptimization_config import num_vehicles


class InitialModelValidIneq:
    def __init__(self, subtour, num_vehicles, n):
        self.model = "MIP 1"
        self.subtour = subtour
        self.num_vehicles = num_vehicles
        self.n = n

    def get_n(self):
        return self.n

    def vizualize_route(self, results):
        dot = graphviz.Digraph(engine="neato")

        colors = [
            "blue",
            "green",
            "aquamarine",
            "bisque",
            "black",
            "blueviolet",
            "brown",
            "chartreuse",
            "cornflowerblue",
            "purple",
            "darkmagenta",
            "dodgerblue",
            "greenyellow",
            "mediumseagreen",
            "navy",
        ]

        for node in nodes:
            # nodes
            state = "Pickup" if node < n else "Dropoff"
            state = "Depot" if node >= 2 * n else state
            number = node if node < n else node - n
            printable_label = (
                f"State: {state}"
                f"\nPos: {Position[node][0]*500,Position[node][1]*500}"
                f"\nRequest No: {number}"
            )
            dot.node(
                name=str(node),
                label=printable_label,
                pos=f"{Position[node][0]*500},{Position[node][1]*500}!",
            )

        for v in results:
            # edges
            if v.varName.startswith("x") and v.x > 0:
                var = (
                    str(v.varName)
                    .replace("x", "")
                    .replace("[", "")
                    .replace("]", "")
                    .split(",")
                )
                try:
                    edgelabel = datetime.fromtimestamp(
                        next(a.x for a in results if a.varName == f"t[{var[0]}]")
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    dot.edge(
                        str(var[0]),
                        str(var[1]),
                        label=edgelabel,
                        color=colors[int(var[2])],
                    )
                except StopIteration as e:
                    dot.edge(
                        str(var[0]),
                        str(var[1]),
                        color=colors[int(var[2])],
                    )
                    continue

        dot.render(filename="route.gv", cleanup=True, view=True)

    def run_model(self):
        try:
            m = gp.Model("mip1")
            m.setParam("NumericFocus", 3)
            m.setParam("TimeLimit", 2500)

            # Sets
            num_nodes = 2 * self.n
            num_nodes_and_depots = (
                2 * self.num_vehicles + 2 * self.n
            )  # num_vehicles is fetched from reopt config

            # Different parameters per node

            df = pd.read_csv(initial_events_path, nrows=self.n)

            # Load for each request
            L_S = df["Number of Passengers"].tolist()
            L_W = df["Wheelchair"].tolist()

            # Lat and lon for each request
            origin_lat_lon = list(
                zip(np.deg2rad(df["Origin Lat"]), np.deg2rad(df["Origin Lng"]))
            )
            destination_lat_lon = list(
                zip(
                    np.deg2rad(df["Destination Lat"]), np.deg2rad(df["Destination Lng"])
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
            for i in range(self.num_vehicles):
                vehicle_lat_lon.append(
                    (radians(59.946829115276145), radians(10.779841653639243))
                )
                vehicle_lat_lon_deg.append((59.946829115276145, 10.779841653639243))

            # Destinations for each vehicle
            for i in range(self.num_vehicles):
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
            M_ij = np.empty(shape=(num_nodes, num_nodes), dtype=datetime)
            for i in range(num_nodes):
                for j in range(num_nodes):
                    M_ij[i][j] = T_H_U[i] + T_ij[i][j] - T_H_L[j]

            pickups = [i for i in range(self.n)]
            dropoffs = [i for i in range(self.n, 2 * self.n)]
            nodes = [i for i in range(2 * self.n)]
            nodes_depots = [i for i in range(num_nodes_and_depots)]
            vehicles = [i for i in range(self.num_vehicles)]
            n = self.n

            if self.subtour:
                df_sub = pd.read_csv(config("data_path_subtour_elimination"))
                df_sub.drop("Minutes", inplace=True, axis=1)

            # Create variables
            x = m.addVars(
                nodes_depots, nodes_depots, vehicles, vtype=GRB.BINARY, name="x"
            )
            q_S = m.addVars(nodes_depots, vehicles, vtype=GRB.INTEGER, name="q_S")
            q_W = m.addVars(nodes_depots, vehicles, vtype=GRB.INTEGER, name="q_W")
            t = m.addVars(nodes, vtype=GRB.CONTINUOUS, name="t")
            l = m.addVars(nodes, vtype=GRB.CONTINUOUS, name="l")
            u = m.addVars(nodes, vtype=GRB.CONTINUOUS, name="u")
            d = m.addVars(pickups, vtype=GRB.CONTINUOUS, name="d")

            # OBJECTIVE FUNCTION

            m.setObjectiveN(
                alpha
                * quicksum(
                    C_D * D_ij[i][j] * x[i, j, k]
                    for i in nodes_depots
                    for j in nodes_depots
                    for k in vehicles
                    if j != (2 * self.n + k + self.num_vehicles)
                ),
                index=0,
            )
            m.setObjectiveN(
                (1 - alpha)
                * (
                    quicksum(C_T * (l[i] + u[i]) for i in nodes)
                    + quicksum(C_F * d[i] for i in pickups)
                ),
                index=1,
            )

            m.ModelSense = GRB.MINIMIZE

            # ARC ELIMINATION
            # cannot drive from pick-up nodes to destinations
            for v in vehicles:
                for k in vehicles:
                    for i in pickups:
                        x[i, 2 * self.n + v + self.num_vehicles, k].lb = 0
                        x[i, 2 * self.n + v + self.num_vehicles, k].ub = 0

            # cannot drive from origins to drop-offs
            for v in vehicles:
                for k in vehicles:
                    for j in dropoffs:
                        x[2 * self.n + v, j, k].lb = 0
                        x[2 * self.n + v, j, k].ub = 0

            # cannot drive from own drop-off to own pick-up
            for k in vehicles:
                for i in pickups:
                    x[n + i, i, k].lb = 0
                    x[n + i, i, k].ub = 0

            # cannot drive from itself to itself
            for k in vehicles:
                for i in pickups:
                    x[i, i, k].lb = 0
                    x[i, i, k].ub = 0

            # cannot drive into an origin
            for v in vehicles:
                for k in vehicles:
                    for i in nodes_depots:
                        x[i, 2 * n + v, k].lb = 0
                        x[i, 2 * n + v, k].ub = 0

            # cannot drive from a destination
            for v in vehicles:
                for k in vehicles:
                    for j in nodes_depots:
                        x[2 * self.n + v + self.num_vehicles, j, k].lb = 0
                        x[2 * self.n + v + self.num_vehicles, j, k].ub = 0

            # cannot drive from origins that are not their own
            for v in vehicles:
                for k in vehicles:
                    if k != v:
                        for j in nodes_depots:
                            x[2 * n + v, j, k].lb = 0
                            x[2 * n + v, j, k].ub = 0

            # cannot drive into destinations that are not their own
            for v in vehicles:
                for k in vehicles:
                    if k != v:
                        for i in nodes_depots:
                            x[i, 2 * self.n + v + self.num_vehicles, k].lb = 0
                            x[i, 2 * self.n + v + self.num_vehicles, k].ub = 0

            # not add arc if vehicle cannot reach node j from node i within the time window of j
            for k in vehicles:
                for i in nodes:
                    for j in nodes:
                        if T_H_L[i] + S + T_ij[i][j] > T_H_U[j]:
                            x[i, j, k].lb = 0
                            x[i, j, k].ub = 0

            # not add swip-tour to node i from node j if that means node (j+n) cannot be reached in time
            for k in vehicles:
                for i in pickups:
                    for j in pickups:
                        if (
                            T_H_L[j] + S + T_ij[j][i] + S + T_ij[i][j + n]
                            > T_H_U[j + n]
                        ):
                            x[i, j + n, k].lb = 0
                            x[i, j + n, k].ub = 0

            # not add arc if route from node (i+n) to node j means that node (j+n) cannot be reached in time
            for k in vehicles:
                for i in pickups:
                    for j in pickups:
                        if (
                            T_H_L[i]
                            + S
                            + T_ij[i][i + n]
                            + S
                            + T_ij[i + n][j]
                            + S
                            + T_ij[j][j + n]
                            > T_H_U[j + n]
                        ):
                            x[i + n, j, k].lb = 0
                            x[i + n, j, k].ub = 0

            # FLOW CONSTRAINTS
            m.addConstrs(
                (
                    quicksum(x[i, j, k] for j in nodes_depots for k in vehicles) == 1
                    for i in pickups
                ),
                name="Flow1",
            )

            m.addConstrs(
                (
                    quicksum(x[2 * n + k, j, k] for j in nodes_depots) == 1
                    for k in vehicles
                ),
                name="Flow3.1",
            )

            m.addConstrs(
                (
                    quicksum(
                        x[i, 2 * self.n + k + self.num_vehicles, k]
                        for i in nodes_depots
                    )
                    == 1
                    for k in vehicles
                ),
                name="Flow3.2",
            )

            m.addConstrs(
                (
                    quicksum(x[i, j, k] for j in nodes_depots)
                    - quicksum(x[n + i, j, k] for j in nodes_depots)
                    == 0
                    for i in pickups
                    for k in vehicles
                ),
                name="Flow6",
            )
            m.addConstrs(
                (
                    quicksum(x[j, i, k] for j in nodes_depots)
                    - quicksum(x[i, j, k] for j in nodes_depots)
                    == 0
                    for i in nodes
                    for k in vehicles
                ),
                name="Flow7",
            )

            # STANDARD SEATS CAPACITY CONSTRAINTS

            m.addConstrs(
                (q_S[2 * n + k, k] == 0 for k in vehicles),
                name="SCapacity1",
            )

            m.addConstrs(
                (
                    q_S[i, k] + L_S[j] - q_S[j, k] <= (Q_S + L_S[j]) * (1 - x[i, j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="SCapacity2",
            )

            m.addConstrs(
                (
                    q_S[i, k] - L_S[j] - q_S[n + j, k] <= Q_S * (1 - x[i, n + j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="SCapacity3",
            )

            m.addConstrs(
                (
                    quicksum(L_S[i] * x[i, j, k] for j in nodes_depots) <= q_S[i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="SCapacity4.1",
            )

            m.addConstrs(
                (
                    q_S[i, k] <= quicksum(Q_S * x[i, j, k] for j in nodes_depots)
                    for i in pickups
                    for k in vehicles
                ),
                name="SCapacity4.2",
            )

            m.addConstrs(
                (
                    quicksum((Q_S - L_S[i]) * x[n + i, j, k] for j in nodes_depots)
                    >= q_S[n + i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="SCapacity5",
            )

            m.addConstrs(
                (
                    q_S[i, k] <= Q_S * (1 - x[i, 2 * self.n + k + self.num_vehicles, k])
                    for i in dropoffs
                    for k in vehicles
                ),
                name="SCapacity6",
            )

            # WHEELCHAIR SEATS CAPACITY CONSTRAINTS
            m.addConstrs(
                (q_W[2 * n + k, k] == 0 for k in vehicles),
                name="WCapacity1",
            )

            m.addConstrs(
                (
                    q_W[i, k] + L_W[j] - q_W[j, k] <= (Q_W + L_W[j]) * (1 - x[i, j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="WCapacity2",
            )

            m.addConstrs(
                (
                    q_W[i, k] - L_W[j] - q_W[n + j, k] <= Q_W * (1 - x[i, n + j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="WCapacity3",
            )

            m.addConstrs(
                (
                    quicksum(L_W[i] * x[i, j, k] for j in nodes_depots) <= q_W[i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity4.1",
            )

            m.addConstrs(
                (
                    q_W[i, k] <= quicksum(Q_W * x[i, j, k] for j in nodes_depots)
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity4.2",
            )

            m.addConstrs(
                (
                    quicksum((Q_W - L_W[i]) * x[n + i, j, k] for j in nodes_depots)
                    >= q_W[n + i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity5",
            )

            m.addConstrs(
                (
                    q_W[i, k] <= Q_W * (1 - x[i, 2 * self.n + k + self.num_vehicles, k])
                    for i in dropoffs
                    for k in vehicles
                ),
                name="WCapacity6",
            )

            # TIME WINDOW CONSTRAINTS

            m.addConstrs(
                (T_S_L[i] - l[i] <= t[i] for i in nodes),
                name="TimeWindow1.1",
            )

            m.addConstrs(
                (t[i] <= T_S_U[i] + u[i] for i in nodes),
                name="TimeWindow1.2",
            )

            m.addConstrs(
                (T_H_L[i] <= t[i] for i in nodes),
                name="TimeWindow2.1",
            )

            m.addConstrs(
                (t[i] <= T_H_U[i] for i in nodes),
                name="TimeWindow2.2",
            )

            m.addConstrs(
                (
                    t[i] + S + T_ij[i][j] - t[j] <= M_ij[i][j] * (1 - x[i, j, k])
                    for i in nodes
                    for j in nodes
                    for k in vehicles
                ),
                name="TimeWindow3",
            )

            m.addConstrs(
                (t[i] + S + T_ij[i][n + i] - t[n + i] <= 0 for i in pickups),
                name="TimeWindow4",
            )

            # RIDE TIME CONSTRAINTS
            m.addConstrs(
                (d[i] >= t[n + i] - (t[i] + (1 + F) * T_ij[i][n + i]) for i in pickups),
                name="RideTime1",
            )

            # VALID INEQUALITIES
            m.addConstr(
                (
                    quicksum(
                        x[i, j, k]
                        for i in nodes_depots
                        for j in nodes_depots
                        for k in vehicles
                    )
                    <= num_nodes + self.num_vehicles
                ),
                name="ValidInequality1",
            )
            """
            # SUBTOUR ELIMINATION SIZE 2
            counter = 0

            for _, row in df_sub.iterrows():
                counter += 1
                row = row.values.tolist()
                m.addConstr(
                    (
                        quicksum(x[i, j, k] for i in row for j in row for k in vehicles)
                        <= len(row) - 1
                    ),
                    name="Subtour" + str(counter),
                )

            # SYMMETRY BREAKING
            # costs used by vehicle k must be larger than for vehicle (k+1)
            m.addConstrs(
                (
                    quicksum(
                        C_D * D_ij[i][j] * x[i, j, k]
                        for i in nodes_depots
                        for j in nodes_depots
                    )
                    >= quicksum(
                        C_D * D_ij[i][j] * x[i, j, k + 1]
                        for i in nodes_depots
                        for j in nodes_depots
                    )
                    for k in vehicles
                    if k != num_vehicles - 1
                ),
                name="SymmetryCost",
            )
            """

            # RUN MODEL
            m.optimize()

            """
            for v in m.getVars():
                if v.varName.startswith("t"):
                    continue
                if v.x > 0:
                    print("%s %g" % (v.varName, v.x))

            for i in nodes:
                print(
                    t[i].varName,
                    datetime.utcfromtimestamp(t[i].x * 3600).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )

            for i in nodes:
                for k in vehicles:
                    print(q_S[i, k].varName, q_S[i, k].x)

            for i in pickups:
                print(d[i].varName, d[i].x)

            for i in nodes:
                print(t[i].varName, t[i].x)

            print("Obj: %g" % m.objVal)

            """

            obj1 = m.getObjective(index=0)
            print("Operational costs")
            print(obj1.getValue())
            obj2 = m.getObjective(index=1)
            print("Quality of service")
            print(obj2.getValue())

            obj3 = obj1.getValue() + obj2.getValue()
            print("Total")
            print(obj3)

            # self.vizualize_route(results=m.getVars())

            route_plan = dict()
            route_plan["x"] = {k: v.X for k, v in x.items()}
            route_plan["t"] = {k: v.X for k, v in t.items()}
            route_plan["q_S"] = {k: v.X for k, v in q_S.items()}
            route_plan["q_W"] = {k: v.X for k, v in q_W.items()}

            unused_vehicles = [
                k
                for k in vehicles
                if route_plan["x"][
                    (
                        2 * (self.n) + k,
                        2 * (self.n) + k + self.num_vehicles,
                        k,
                    )
                ]
                == 1
            ]

            obj1 = m.getObjective(index=0)
            print("Operational costs: ", obj1.getValue())
            obj2 = m.getObjective(index=1)
            print("Quality of service: ", obj2.getValue())
            operational = obj1.getValue()
            quality = obj2.getValue()

            ride_sharing_sum = 0
            counter = 0
            for i in nodes_depots:
                for j in vehicles:
                    if q_S[i, j].x >= 0.9:
                        ride_sharing_sum += q_S[i, j].x
                        counter += 1

            ride_sharing = round(ride_sharing_sum / counter, 2)

            t_min = min(route_plan["t"].values())
            t_max = max(route_plan["t"].values())

            productivity = round(ride_sharing_sum / (t_max - t_min), 2)

            return (
                route_plan,
                unused_vehicles,
                operational,
                quality,
                ride_sharing,
                productivity,
            )

        except GurobiError as e:
            print("Error reported")
            print(e.message)


if __name__ == "__main__":
    model = InitialModel()
    model.run_model()
