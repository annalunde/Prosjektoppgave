import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
import graphviz
from config import *


class Model:
    def _init_(self):
        model = "MIP 1"

    def vizualize_route(self, results):
        dot = graphviz.Digraph(engine="neato")

        colors = ["green", "red", "blue"]

        nodes = [i for i in range(2 * n)]

        for node in nodes:
            state = "Pickup" if node < n else "Dropoff"  # legg til depots state
            printable_label = (
                f"State: {state}"
                f"\nPos: {Position[node][0],Position[node][1]}"
                f"\nToS: {Position[node][0],Position[node][1]}"
            )
            dot.node(
                name=str(node),
                label=printable_label,
                pos=f"{Position[node][0]},{Position[node][1]}!",
            )

        for v in results:
            if v.varName.startswith("x") and v.x > 0:
                print("%s %g" % (v.varName, v.x))
                # edgelabel = str(v.varName[6])
                dot.edge(
                    str(v.varName[2]),
                    str(v.varName[4]),
                    # label=edgelabel,
                    color=colors[int(v.varName[6])],
                )

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
            t = m.addVars(nodes, vehicles, name="t")
            l = m.addVars(nodes, name="l")
            u = m.addVars(nodes, name="u")
            d = m.addVars(pickups, name="d")

            # OBJECTIVE FUNCTION
            m.setObjective(
                quicksum(
                    C_D[k] * D_ij[i][j] * x[i, j, k]
                    for i in nodes
                    for j in nodes
                    for k in vehicles
                )
                + quicksum(C_T * (l[i] + u[i]) for i in nodes)
                + quicksum(C_F * d[i] for i in pickups),
                GRB.MINIMIZE,
            )

            # FLOW CONSTRAINTS
            m.addConstrs(
                (
                    quicksum(x[nodes_depots[2 * n + k], j, k] for j in nodes_depots)
                    == 1
                    for k in vehicles
                ),
                name="Flow1",
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
                name="Flow2",
            )

            m.addConstrs(
                (
                    quicksum(x[j, nodes_depots[2 * n + k], k] for j in nodes_depots)
                    == 0
                    for k in vehicles
                ),
                name="Flow3",
            )

            m.addConstrs(
                (
                    quicksum(
                        x[nodes_depots[2 * n + k + num_vehicles], i, k]
                        for i in nodes_depots
                    )
                    == 0
                    for k in vehicles
                ),
                name="Flow4",
            )

            m.addConstrs(
                (
                    quicksum(x[i, j, k] for j in nodes_depots)
                    - quicksum(x[n + i, j, k] for j in nodes_depots)
                    == 0
                    for i in pickups
                    for k in vehicles
                ),
                name="Flow5",
            )
            m.addConstrs(
                (
                    quicksum(x[j, i, k] for j in nodes_depots)
                    - quicksum(x[i, j, k] for j in nodes_depots)
                    == 0
                    for i in nodes
                    for k in vehicles
                ),
                name="Flow6",
            )

            m.addConstrs(
                (x[i, i, k] == 0 for i in nodes_depots for k in vehicles),
                name="Flow7",
            )

            m.addConstrs(
                (
                    quicksum(x[i, j, k] for j in nodes_depots for k in vehicles) == 1
                    for i in pickups
                ),
                name="Flow8",
            )
            print("Flow9")
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
                name="Flow9",
            )

            print("Flow10")
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
                name="Flow10",
            )

            # vehicles cannot drive from origins that are not their own
            print("Flow11")
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
                name="Flow11",
            )

            # vehicles cannot drive into destinations that are not their own
            print("Flow12")
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
                name="Flow12",
            )

            # STANDARD SEATS CAPACITY CONSTRAINTS
            m.addConstrs(
                (q_S[nodes_depots[2 * n + k], k] == 0 for k in vehicles),
                name="SCapacity1",
            )

            m.addConstrs(
                (
                    q_S[i, k] + L_S[j] - q_S[j, k] <= Q_S[k] * (1 - x[i, j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="SCapacity2",
            )
            m.addConstrs(
                (
                    q_S[i, k] - L_S[j] - q_S[n + j, k] <= Q_S[k] * (1 - x[i, j, k])
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
                name="SCapacity4",
            )
            m.addConstrs(
                (
                    q_S[i, k] <= quicksum(Q_S[k] * x[i, j, k] for j in nodes_depots)
                    for i in pickups
                    for k in vehicles
                ),
                name="SCapacity5",
            )
            m.addConstrs(
                (
                    quicksum((Q_S[k] - L_S[i]) * x[n + i, j, k] for j in nodes_depots)
                    >= q_S[n + i, k]
                    for i in pickups
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
                    q_W[i, k] + L_W[j] - q_W[j, k] <= Q_W[k] * (1 - x[i, j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="WCapacity2",
            )
            m.addConstrs(
                (
                    q_W[i, k] - L_W[j] - q_W[n + j, k] <= Q_W[k] * (1 - x[i, j, k])
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
                name="WCapacity4",
            )
            m.addConstrs(
                (
                    q_W[i, k] <= quicksum(Q_W[k] * x[i, j, k] for j in nodes_depots)
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity5",
            )
            m.addConstrs(
                (
                    quicksum((Q_W[k] - L_W[i]) * x[n + i, j, k] for j in nodes_depots)
                    >= q_W[n + i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity6",
            )

            # TIME WINDOW CONSTRAINTS
            m.addConstrs(
                (
                    T_S_L[i].timestamp() - l[i] <= t[i, k]
                    for i in nodes
                    for k in vehicles
                ),
                name="TimeWindow1",
            )

            m.addConstrs(
                (
                    t[i, k] <= T_S_U[i].timestamp() + u[i]
                    for i in nodes
                    for k in vehicles
                ),
                name="TimeWindow2",
            )

            m.addConstrs(
                (T_H_L[i].timestamp() <= t[i, k] for i in nodes for k in vehicles),
                name="TimeWindow3",
            )

            m.addConstrs(
                (t[i, k] <= T_H_U[i].timestamp() for i in nodes for k in vehicles),
                name="TimeWindow4",
            )

            m.addConstrs(
                (
                    t[i, k] + T_ij[i][j].total_seconds() - t[j, k]
                    <= M_ij[i][j].total_seconds() * (1 - x[i, j, k])
                    for i in nodes
                    for j in nodes
                    for k in vehicles
                ),
                name="TimeWindow5",
            )

            m.addConstrs(
                (
                    t[i, k] + T_ij[i][n + i].total_seconds() - t[n + i, k] <= 0
                    for i in pickups
                    for k in vehicles
                ),
                name="TimeWindow6",
            )

            # RIDE TIME CONSTRAINTS
            m.addConstrs(
                (
                    t[n + i, k] - t[i, k] - (1 + F) * T_ij[i][n + i].total_seconds()
                    <= M * w[i]
                    for i in pickups
                    for k in vehicles
                ),
                name="RideTime1",
            )
            m.addConstrs(
                (
                    d[i] >= t[n + i, k] - t[i, k] - M * (1 - w[i])
                    for i in pickups
                    for k in vehicles
                ),
                name="RideTime2",
            )

            # RUN MODEL
            m.optimize()

            for v in m.getVars():
                if v.x > 0:
                    print("%s %g" % (v.varName, v.x))

            for i in nodes:
                for k in vehicles:
                    print(
                        t[i, k].varName,
                        datetime.fromtimestamp(t[i, k].x).strftime("%Y-%m-%d %H:%M:%S"),
                    )

            print("Obj: %g" % m.objVal)
            self.vizualize_route(results=m.getVars())

        except GurobiError as e:
            print("Error reported")
            print(e.message)


if __name__ == "__main__":
    model = Model()
    model.run_model()
