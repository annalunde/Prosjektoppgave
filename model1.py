import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
import graphviz
from config_RAT_data import *


class Model:
    def _init_(self):
        model = "MIP 1"

    def vizualize_route(self, results):
        dot = graphviz.Digraph(engine="neato")

        colors = [
            "fuchsia",
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

        nodes = [i for i in range(num_nodes_and_depots)]

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
                        next(
                            a.x for a in results if a.varName == f"t[{var[0]}]"
                        )
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

            pickups = [i for i in range(n)]
            dropoffs = [i for i in range(n, 2 * n)]
            nodes = [i for i in range(2 * n)]
            nodes_depots = [i for i in range(num_nodes_and_depots)]
            vehicles = [i for i in range(num_vehicles)]

            # Create variables
            x = m.addVars(
                nodes_depots, nodes_depots, vehicles, vtype=GRB.BINARY, name="x"
            )
            w = m.addVars(pickups, vtype=GRB.BINARY, name="w")
            q_S = m.addVars(nodes_depots, vehicles, vtype=GRB.INTEGER, name="q_S")
            q_W = m.addVars(nodes_depots, vehicles, vtype=GRB.INTEGER, name="q_W")
            t = m.addVars(nodes, name="t")
            l = m.addVars(nodes, name="l")
            u = m.addVars(nodes, name="u")
            d = m.addVars(pickups, name="d")

            # OBJECTIVE FUNCTION
            m.setObjective(
                quicksum(
                    C_D[k] * D_ij[i][j] * x[i, j, k]
                    for i in nodes_depots
                    for j in nodes_depots
                    for k in vehicles
                )
                + quicksum(C_T * (l[i] + u[i]) for i in nodes)
                + quicksum(C_F * d[i] for i in pickups),
                GRB.MINIMIZE,
            )

            # FLOW CONSTRAINTS
            m.addConstrs(
                (
                    quicksum(x[i, j, k] for j in nodes_depots for k in vehicles) == 1
                    for i in pickups
                ),
                name="Flow1",
            )

            m.addConstrs(
                (x[i, i, k] == 0 for i in nodes_depots for k in vehicles),
                name="Flow2",
            )

            m.addConstrs(
                (
                    quicksum(x[nodes_depots[2 * n + k], j, k] for j in nodes_depots)
                    == 1
                    for k in vehicles
                ),
                name="Flow3.1",
            )

            m.addConstrs(
                (
                    quicksum(
                        x[i, nodes_depots[2 * n + k + num_vehicles], k]
                        for i in nodes_depots
                    )
                    == 1
                    for k in vehicles
                ),
                name="Flow3.2",
            )

            # vehicles cannot drive into an origin
            m.addConstrs(
                (
                    quicksum(
                        x[i, nodes_depots[2 * n + v], k]
                        for i in nodes_depots
                        for k in vehicles
                    )
                    == 0
                    for v in vehicles
                ),
                name="Flow4.1",
            )

            # vehicles cannot drive from a destination
            m.addConstrs(
                (
                    quicksum(
                        x[nodes_depots[2 * n + v + num_vehicles], j, k]
                        for j in nodes_depots
                        for k in vehicles
                    )
                    == 0
                    for v in vehicles
                ),
                name="Flow4.2",
            )

            # vehicles cannot drive from origins that are not their own
            m.addConstrs(
                (
                    quicksum(
                        x[nodes_depots[2 * n + v], j, k]
                        for j in nodes_depots
                        for k in vehicles
                        if k != v
                    )
                    == 0
                    for v in vehicles
                ),
                name="Flow5.1",
            )

            # vehicles cannot drive into destinations that are not their own
            m.addConstrs(
                (
                    quicksum(
                        x[i, nodes_depots[2 * n + v + num_vehicles], k]
                        for i in nodes_depots
                        for k in vehicles
                        if k != v
                    )
                    == 0
                    for v in vehicles
                ),
                name="Flow5.2",
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
                (q_S[nodes_depots[2 * n + k], k] == 0 for k in vehicles),
                name="SCapacity1",
            )

            m.addConstrs(
                (
                    q_S[i, k] + L_S[j] - q_S[j, k] <= quicksum(Q_S[k] for k in vehicles) * (1 - x[i, j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="SCapacity2",
            )
            m.addConstrs(
                (
                    q_S[i, k] - L_S[j] - q_S[n + j, k] <= Q_S[k] * (1 - x[i, n + j, k])
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
                    q_S[i, k] <= quicksum(Q_S[k] * x[i, j, k] for j in nodes_depots)
                    for i in pickups
                    for k in vehicles
                ),
                name="SCapacity4.2",
            )
            m.addConstrs(
                (
                    quicksum((Q_S[k] - L_S[i]) * x[n + i, j, k] for j in nodes_depots)
                    >= q_S[n + i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="SCapacity5",
            )

            m.addConstrs(
                (
                    q_S[i, k] <= Q_S[k] * (1 - x[i, 2 * n + k + num_vehicles, k])
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="SCapacity6",
            )

            # WHEELCHAIR SEATS CAPACITY CONSTRAINTS
            m.addConstrs(
                (q_W[nodes_depots[2 * n + k], k] == 0 for k in vehicles),
                name="WCapacity1",
            )
            m.addConstrs(
                (
                    q_W[i, k] + L_W[j] - q_W[j, k] <= quicksum(Q_W[k] for k in vehicles) * (1 - x[i, j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="WCapacity2",
            )
            m.addConstrs(
                (
                    q_W[i, k] - L_W[j] - q_W[n + j, k] <= Q_W[k] * (1 - x[i, n + j, k])
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
                    q_W[i, k] <= quicksum(Q_W[k] * x[i, j, k] for j in nodes_depots)
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity4.2",
            )
            m.addConstrs(
                (
                    quicksum((Q_W[k] - L_W[i]) * x[n + i, j, k] for j in nodes_depots)
                    >= q_W[n + i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity5",
            )

            m.addConstrs(
                (
                    q_W[i, k] <= Q_W[k] * (1 - x[i, 2 * n + k + num_vehicles, k])
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="WCapacity6",
            )

            # TIME WINDOW CONSTRAINTS

            m.addConstrs(
                (
                    T_S_L[i].timestamp() - l[i] <= t[i]
                    for i in nodes
                ),
                name="TimeWindow1.1",
            )


            m.addConstrs(
                (
                    t[i] <= T_S_U[i].timestamp() + u[i]
                    for i in nodes
                ),
                name="TimeWindow1.2",
            )

            m.addConstrs(
                (T_H_L[i].timestamp() <= t[i] for i in nodes),
                name="TimeWindow2.1",
            )

            m.addConstrs(
                (t[i] <= T_H_U[i].timestamp() for i in nodes),
                name="TimeWindow2.2",
            )

            m.addConstrs(
                (
                    t[i] + T_ij[i][j].total_seconds() - t[j]
                    <= M_ij[i][j].total_seconds() * (1 - x[i, j, k])
                    for i in nodes
                    for j in nodes
                    for k in vehicles
                ),
                name="TimeWindow3",
            )

            m.addConstrs(
                (
                    t[i] + T_ij[i][n + i].total_seconds() - t[n + i] <= 0
                    for i in pickups
                    for k in vehicles
                ),
                name="TimeWindow4",
            )


            # RIDE TIME CONSTRAINTS
            m.addConstrs(
                (
                    t[n + i] - t[i] - (1 + F) * T_ij[i][n + i].total_seconds()
                    <= M * w[i]
                    for i in pickups
                ),
                name="RideTime1",
            )
            m.addConstrs(
                (
                    d[i] >= t[n + i] - t[i] - M * (1 - w[i])
                    for i in pickups
                ),
                name="RideTime2",
            )

            # RUN MODEL
            m.optimize()

            for v in m.getVars():
                if v.x > 0:
                    print("%s %g" % (v.varName, v.x))

            for i in nodes:
                print(
                        t[i].varName,
                        datetime.fromtimestamp(t[i].x).strftime("%Y-%m-%d %H:%M:%S"),
                    )

            print("Obj: %g" % m.objVal)
            self.vizualize_route(results=m.getVars())

        except GurobiError as e:
            print("Error reported")
            print(e.message)


if __name__ == "__main__":
    model = Model()
    model.run_model()
