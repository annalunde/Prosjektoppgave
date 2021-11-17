import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
import graphviz
from Models.reoptimization_config import *
from Models.updater_for_reopt import *
from Models.updater_for_reopt import Updater


class ReoptModel:
    def __init__(self, current_route_plan, event, num_requests, first, rejected):
        self.model = "MIP 1"
        self.route_plan = current_route_plan
        self.event = event
        self.num_requests = num_requests
        self.updater = Updater(
            self.route_plan, self.event, self.num_requests, first, rejected
        )

    def vizualize_route(self, results, num_nodes_and_depots):
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
            state = "Pickup" if node < self.num_requests else "Dropoff"
            state = "Depot" if node >= 2 * self.num_requests else state
            number = node if node < self.num_requests else node - self.num_requests
            printable_label = (
                f"State: {state}"
                f"\nPos: {Position[node][0],Position[node][1]}"
                f"\nRequest No: {number}"
            )
            dot.node(
                name=str(node),
                label=printable_label,
                pos=f"{Position[node][0]},{Position[node][1]}!",
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
                            a.x for a in results if a.varName == f"t[{var[0]},{var[2]}]"
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
        # update sets with new request
        (
            pickups_remaining,
            pickups_new,
            pickups,
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
            rejected,
        ) = self.updater.update()

        try:
            m = gp.Model("mip1")
            m.setParam("NumericFocus", 3)

            pickups = [i for i in range(self.num_requests)]
            dropoffs = [i for i in range(self.num_requests, 2 * self.num_requests)]
            nodes = [i for i in range(2 * self.num_requests)]
            vehicles = [i for i in range(num_vehicles)]

            # Create variables
            x = m.addVars(
                nodes_depots, nodes_depots, vehicles, vtype=GRB.BINARY, name="x"
            )
            q_S = m.addVars(nodes_depots, vehicles, vtype=GRB.INTEGER, name="q_S")
            q_W = m.addVars(nodes_depots, vehicles, vtype=GRB.INTEGER, name="q_W")
            t = m.addVars(nodes, name="t")
            l = m.addVars(nodes, name="l")
            u = m.addVars(nodes, name="u")
            d = m.addVars(pickups, name="d")
            s = m.addVars(pickups_new, vtype=GRB.BINARY, name="s")
            z_plus = m.addVars(nodes_remaining, name="z+")
            z_minus = m.addVars(nodes_remaining, name="z-")
            y = m.addVars(vehicles, vtype=GRB.BINARY, name="y")

            # OBJECTIVE FUNCTION
            m.setObjective(
                quicksum(
                    C_D[k] * D_ij[i][j] * x[i, j, k]
                    for i in nodes_depots
                    for j in nodes_depots
                    for k in vehicles
                    if j != (2 * self.num_requests + k + num_vehicles)
                )
                + quicksum(C_T * (l[i] + u[i]) for i in nodes)
                + quicksum(C_F * d[i] for i in pickups)
                + quicksum(C_R * s[i] for i in pickups_new)
                + quicksum(C_K[k] * y[k] for k in vehicles)
                + quicksum(C_O * (z_plus[i] + z_minus[i]) for i in nodes_remaining),
                GRB.MINIMIZE,
            )

            # FIXATING VALUES

            # x values - outside time window
            for f_x in fixate_x:
                x[f_x[0], f_x[1], f_x[2]].lb = 1
                x[f_x[0], f_x[1], f_x[2]].ub = 1

            # t values - historic values
            for f_t in fixate_t:
                t[f_t].lb = fixate_t[f_t]
                t[f_t].ub = fixate_t[f_t]

            # FLOW CONSTRAINTS
            m.addConstrs(
                (
                    quicksum(x[i, j, k] for j in nodes_depots for k in vehicles) == 1
                    for i in pickups_remaining
                ),
                name="Flow1",
            )

            m.addConstrs(
                (x[i, i, k] == 0 for i in nodes_depots for k in vehicles),
                name="Flow2",
            )
            m.addConstrs(
                (
                    quicksum(x[2 * self.num_requests + k, j, k] for j in nodes_depots)
                    == 1
                    for k in vehicles
                ),
                name="Flow3.1",
            )

            m.addConstrs(
                (
                    quicksum(
                        x[i, 2 * self.num_requests + k + num_vehicles, k]
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
                        x[i, 2 * self.num_requests + v, k]
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
                        x[nodes_depots[2 * self.num_requests + v + num_vehicles], j, k]
                        for j in nodes_depots
                        for k in vehicles
                    )
                    == 0
                    for v in vehicles
                ),
                name="Flow4.2",
            )

            # vehicles cannot drive into destinations that are not their own
            m.addConstrs(
                (
                    quicksum(
                        x[i, 2 * self.num_requests + v + num_vehicles, k]
                        for i in nodes_depots
                        for k in vehicles
                        if k != v
                    )
                    == 0
                    for v in vehicles
                ),
                name="Flow5.1",
            )
            # vehicles cannot drive from origins that are not their own
            m.addConstrs(
                (
                    quicksum(
                        x[2 * self.num_requests + v, j, k]
                        for j in nodes_depots
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
                    - quicksum(x[self.num_requests + i, j, k] for j in nodes_depots)
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
                (
                    q_S[i, k] + L_S[j] - q_S[j, k]
                    <= (Q_S[k] + L_S[j]) * (1 - x[i, j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="SCapacity1",
            )

            m.addConstrs(
                (
                    q_S[i, k] - L_S[j] - q_S[self.num_requests + j, k]
                    <= Q_S[k] * (1 - x[i, self.num_requests + j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="SCapacity2",
            )

            m.addConstrs(
                (
                    quicksum(L_S[i] * x[i, j, k] for j in nodes_depots) <= q_S[i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="SCapacity3.1",
            )

            m.addConstrs(
                (
                    q_S[i, k] <= quicksum(Q_S[k] * x[i, j, k] for j in nodes_depots)
                    for i in pickups
                    for k in vehicles
                ),
                name="SCapacity3.2",
            )

            m.addConstrs(
                (
                    quicksum(
                        (Q_S[k] - L_S[i]) * x[self.num_requests + i, j, k]
                        for j in nodes_depots
                    )
                    >= q_S[self.num_requests + i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="SCapacity5",
            )

            m.addConstrs(
                (
                    q_S[i, k]
                    <= Q_S[k] * (1 - x[i, 2 * self.num_requests + k + num_vehicles, k])
                    for i in dropoffs
                    for k in vehicles
                ),
                name="SCapacity6",
            )

            # WHEELCHAIR SEATS CAPACITY CONSTRAINTS
            m.addConstrs(
                (
                    q_W[i, k] + L_W[j] - q_W[j, k]
                    <= (Q_W[k] + L_W[j]) * (1 - x[i, j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="WCapacity1",
            )

            m.addConstrs(
                (
                    q_W[i, k] - L_W[j] - q_W[self.num_requests + j, k]
                    <= Q_W[k] * (1 - x[i, self.num_requests + j, k])
                    for j in pickups
                    for i in nodes_depots
                    for k in vehicles
                ),
                name="WCapacity2",
            )

            m.addConstrs(
                (
                    quicksum(L_W[i] * x[i, j, k] for j in nodes_depots) <= q_W[i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity3.1",
            )

            m.addConstrs(
                (
                    q_W[i, k] <= quicksum(Q_W[k] * x[i, j, k] for j in nodes_depots)
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity3.2",
            )

            m.addConstrs(
                (
                    quicksum(
                        (Q_W[k] - L_W[i]) * x[self.num_requests + i, j, k]
                        for j in nodes_depots
                    )
                    >= q_W[self.num_requests + i, k]
                    for i in pickups
                    for k in vehicles
                ),
                name="WCapacity4",
            )

            m.addConstrs(
                (
                    q_W[i, k]
                    <= Q_W[k] * (1 - x[i, 2 * self.num_requests + k + num_vehicles, k])
                    for i in dropoffs
                    for k in vehicles
                ),
                name="WCapacity6",
            )

            # TIME WINDOW CONSTRAINTS

            m.addConstrs(
                (T_S_L[i].timestamp() - l[i] <= t[i] for i in nodes),
                name="TimeWindow1.1",
            )

            m.addConstrs(
                (t[i] <= T_S_U[i].timestamp() + u[i] for i in nodes),
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
                    t[i] + S + T_ij[i][j].total_seconds() - t[j]
                    <= M_ij[i][j].total_seconds() * (1 - x[i, j, k])
                    for i in nodes
                    for j in nodes
                    for k in vehicles
                ),
                name="TimeWindow3",
            )

            m.addConstrs(
                (
                    t[i] + S + T_ij[i][self.num_requests + i].total_seconds()
                    <= t[self.num_requests + i]
                    for i in pickups
                ),
                name="TimeWindow4",
            )

            m.addConstrs(
                (
                    T_O[i] - t[i] == z_plus[i] - z_minus[i]
                    for i in nodes_remaining
                    for k in vehicles
                ),
                name="TimeWindow5",
            )

            # RIDE TIME CONSTRAINTS
            m.addConstrs(
                (
                    d[i]
                    >= t[self.num_requests + i]
                    - (t[i] + (1 + F) * T_ij[i][self.num_requests + i].total_seconds())
                    for i in pickups
                ),
                name="RideTime1",
            )

            # REJECTION CONSTRAINTS

            m.addConstrs(
                (
                    s[i]
                    == 1 - quicksum(x[i, j, k] for j in nodes_depots for k in vehicles)
                    for i in pickups_new
                ),
                name="Rejection1",
            )

            # RUN MODEL
            m.optimize()

            for i in pickups_new:
                print(s[i].varName, s[i].x)
                if s[i].x > 0.1:
                    print("Your request has been rejected:/")
                    rejected.append(i)

            for v in m.getVars():
                if v.varName.startswith("t"):
                    continue
                if v.x > 0:
                    print("%s %g" % (v.varName, v.x))

            for i in nodes:
                print(
                    t[i].varName,
                    datetime.utcfromtimestamp(t[i].x).strftime("%Y-%m-%d %H:%M:%S"),
                )

            print("Obj: %g" % m.objVal)

            """
            NOTE
            self.vizualize_route(
                results=m.getVars(), num_nodes_and_depots=len(nodes_depots)
            )
            """

            route_plan = dict()
            route_plan["x"] = {k: v.X for k, v in x.items()}
            route_plan["t"] = {k: v.X for k, v in t.items()}
            route_plan["q_S"] = {k: v.X for k, v in q_S.items()}
            route_plan["q_W"] = {k: v.X for k, v in q_W.items()}

            return route_plan, rejected

        except GurobiError as e:
            print("Error reported")
            print(e.message)
