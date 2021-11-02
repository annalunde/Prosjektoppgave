import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from reoptimization_config import *
import datetime


class Updater:
    def __init__(self, current_route_plan, event):
        self.route_plan = current_route_plan
        self.event = event

    def update(self):
        P_R = []  # set of remaining pick-up nodes
        P_N = []  # set of new pick-up nodes
        P = []  # set of all pick-up nodes
        N_R = []  # set of remaining pick-up and drop-off nodes
        N_N = []  # set of new pick-up and drop-off nodes
        N = []  # set of all pick-up and drop-off nodes
        E_S = []  # standard seats load of vehicle k when event occurs
        E_W = []  # wheelchair load of vehickle k when event occurs
        T_O = []  # time of service of request i in original plan

        # CREATE NEW SETS
        P_N.append(self.route_plan[n] + 1)
        N_N.append(self.route_plan[n] + 1)
        N_N.append(self.event[dropoff])  # NOTE: assume that event is one request

        # CREATE REMAINING SETS
        time_now = datetime.datetime.now()

        for t_i in self.route_plan[t].keys():
            if self.route_plan[t][t_i] > time_now:  # NOTE: legge til en lag her?
                if t_i <= self.route_plan[n]:
                    P_R.append(t_i)
                    T_O.append(self.route_plan[t][t_i])
                    N_R.append(t_i)

        for i in N_R:
            N_R.append(i + self.route_plan[n])

        for k in vehicles:
            for i in P_R:
                E_S.append(self.route_plan[q_S][i, k])
                E_W.append(self.route_plan[q_W][i, k])

        # CREATE UNION SETS
        P.append(v for v in P_R)
        P.append(v for v in P_N)
        N.append(v for v in P_R)  # append remaining pickups
        N.append(v for v in P_N)  # append new pickups
        N.append(v for v in D_R)  # append remaining dropoffs
        N.append(v for v in D_N)  # append new dropoff

        # UPDATE INDEXES

        return P_R, P_N, P, N_R, N_N, N, E_S, E_W, T_O


def main():
    updater = None

    try:
        updater = Updater()

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()


# TODO:
# lag en conversion mellom csv-requests og formatet vi trenger
# sjekk sett i modell constraints
# få opp koblingen
# låse og åpne innenfor 2 timer
