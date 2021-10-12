import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from config import *

try:
    m = gp.Model("mip1")

    pickups = range(num_pickup_nodes)
    dropoffs = range(num_dropoff_nodes)
    nodes = range(num_nodes)
    vehicles = range(num_vehicles)

    # Create variables
    x = m.addVars(nodes, nodes, vehicles, vtype=GRB.BINARY, name="x")
    w = m.addVars(pickups, vtype=GRB.BINARY, name="w")
    q_S = m.addVars(nodes, vehicles, vtype=GRB.INTEGER, name="q_S")
    q_W = m.addVars(nodes, vehicles, vtype=GRB.INTEGER, name="q_W")
    t = m.addVars(nodes, vehicles, name="t")
    l = m.addVars(nodes, name="l")
    u = m.addVars(nodes, name="u")
    d = m.addVars(pickups, name="d")

    # OBJECTIVE FUNCTION
    m.setObjective(quicksum(C_ijk*x[i,j,k] for i in nodes for j in nodes for k in vehicles) + quicksum(C_R*(1 - quicksum(x[i,j,k] for j in nodes for k in vehicles)) for i in pickups) + quicksum(C_T*(l[i] + u[i]) for i in nodes) + quicksum(C_F*d[i] for i in pickups), GRB.MINIMIZE)



    # FLOW CONSTRAINTS
    # mangler o(k) og d(k) i summene
    m.addConstrs((quicksum(x[o_k[k],j,k] for j in pickups) == quicksum(x[i,d_k[k],k] for i in dropoffs) == 1 for k in vehicles), name="Flow1")

    m.addConstrs((quicksum(x[i,j,k] for j in nodes) - quicksum(x[n+i,j,k] for j in nodes) == 0 for i in pickups for k in vehicles), name="Flow2")

    m.addConstrs((quicksum(x[j,i,k] for j in nodes) - quicksum(x[i,j,k] for j in nodes) == 0 for i in nodes for k in vehicles), name="Flow3")



    # STANDARD SEATS CAPACITY CONSTRAINTS
    m.addConstrs((q_S[o_k[k],k] == 0 for k in vehicles), name="SCapacity1")

    m.addConstrs((q_S[i,k] + L_S[j] - q_S[j,k] <= Q_S[k]*(1 - x[i,j,k]) for j in pickups for i in nodes for k in vehicles), name="SCapacity2")

    m.addConstrs((q_S[i, k] - L_S[j] - q_S[n+j, k] <= Q_S[k] * (1 - x[i, j, k]) for j in pickups for i in nodes for k in vehicles), name="SCapacity3")

    m.addConstrs((quicksum(L_S[i]*x[i,j,k] for j in nodes) <= q_S[i,k] <= quicksum(Q_S[k]*x[i,j,k] for j in nodes) for i in pickups for k in vehicles), name="SCapacity4")

    m.addConstrs((quicksum((Q_S[k] - L_S[i])*x[n+i,j,k] for j in nodes) >= q_S[n+i,k] >= 0 for i in pickups for k in vehicles), name="SCapacity5")



    # WHEELCHAIR SEATS CAPACITY CONSTRAINTS
    m.addConstrs((q_W[o_k[k], k] == 0 for k in vehicles), name="WCapacity1")

    m.addConstrs((q_W[i, k] + L_W[j] - q_W[j, k] <= Q_W[k] * (1 - x[i, j, k]) for j in pickups for i in nodes for k in vehicles), name="WCapacity2")

    m.addConstrs((q_W[i, k] - L_W[j] - q_W[n + j, k] <= Q_W[k] * (1 - x[i, j, k]) for j in pickups for i in nodes for k in vehicles), name="WCapacity3")

    m.addConstrs((quicksum(L_W[i] * x[i, j, k] for j in nodes) <= q_W[i, k] <= quicksum(Q_W[k] * x[i, j, k] for j in nodes) for i in pickups for k in vehicles), name="WCapacity4")

    m.addConstrs((quicksum((Q_W[k] - L_W[i]) * x[n + i, j, k] for j in nodes) >= q_W[n + i, k] >= 0 for i in pickups for k in vehicles), name="WCapacity5")



    # TIME WINDOW CONSTRAINTS
    m.addConstrs((T_S_L[i] - l[i] <= t[i,k] <= T_S_U[i] + u[i] for i in nodes for k in vehicles), name="TimeWindow1")

    m.addConstrs((T_H_L[i] <= t[i,k] <= T_H_U[i] for i in nodes for k in vehicles), name="TimeWindow2")

    m.addConstrs((t[i,k] + T_ij[i,j] - t[j,k] <= M_ij[i,j]*(1 - x[i,j,k]) for i in nodes for j in nodes for k in vehicles), name="TimeWindow3")

    m.addConstrs((t[i,k] + T_ij[i,n+i] - t[n+i,k] <= 0 for i in pickups for k in vehicles), name="TimeWindow4")



    # RIDE TIME CONSTRAINTS
    m.addConstrs((t[n+i,k] - t[i,k] - (1 + F)*T_ij[i,n+i] <= M*w[i] for i in pickups for k in vehicles), name="RideTime1")

    m.addConstrs((d[i] >= t[n+i,k] - t[i,k] -M*(1 - w[i]) for i in pickups for k in vehicles), name="RideTime2")



    # RUN MODEL
    #m.optimize()

except GurobiError as e:
    print('Error reported')
    print(e.message)