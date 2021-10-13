import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from config import *

try:
    m = gp.Model("mip1")

    pickups = [i for i in range(n)]
    dropoffs = [i for i in range(n,2*n)]
    nodes = [i for i in range(2*n)]
    nodes_depots = [i for i in range(num_nodes_depots)]
    vehicles = [i for i in range(num_vehicles)]


    # Create variables
    x = m.addVars(nodes_depots, nodes_depots, vehicles, vtype=GRB.BINARY, name="x")
    w = m.addVars(pickups, vtype=GRB.BINARY, name="w")
    q_S = m.addVars(nodes_depots, vehicles, vtype=GRB.INTEGER, name="q_S")
    q_W = m.addVars(nodes_depots, vehicles, vtype=GRB.INTEGER, name="q_W")
    t = m.addVars(nodes, vehicles, name="t")
    l = m.addVars(nodes, name="l")
    u = m.addVars(nodes, name="u")
    d = m.addVars(pickups, name="d")


    # OBJECTIVE FUNCTION
    m.setObjective(quicksum(C_D[k]*D_ij[i][j]*x[i,j,k] for i in nodes for j in nodes for k in vehicles)
                   + quicksum(C_R*(1 - quicksum(x[i,j,k] for j in nodes for k in vehicles)) for i in pickups)
                   + quicksum(C_T*(l[i] + u[i]) for i in nodes)
                   + quicksum(C_F*d[i] for i in pickups), GRB.MINIMIZE)



    # FLOW CONSTRAINTS
    print("Flow1")
    m.addConstrs((quicksum(x[nodes_depots[2*n+k],j,k] for j in (pickups + [nodes_depots[2*n+k+num_vehicles]])) == 1 for k in vehicles), name="Flow1")
    print("Flow2")
    m.addConstrs((quicksum(x[i,nodes_depots[2*n+k+num_vehicles],k] for i in (dropoffs + [nodes_depots[2*n+k]])) == 1 for k in vehicles), name="Flow2")
    print("Flow3")
    m.addConstrs((quicksum(x[i,j,k] for j in nodes) - quicksum(x[n+i,j,k] for j in nodes) == 0 for i in pickups for k in vehicles), name="Flow3")
    print("Flow4")
    m.addConstrs((quicksum(x[j,i,k] for j in nodes) - quicksum(x[i,j,k] for j in nodes) == 0 for i in nodes for k in vehicles), name="Flow4")



    # STANDARD SEATS CAPACITY CONSTRAINTS
    print("SCapacity1")
    m.addConstrs((q_S[nodes_depots[2*n+k],k] == 0 for k in vehicles), name="SCapacity1")
    print("SCapacity2")
    m.addConstrs((q_S[i,k] + L_S[j] - q_S[j,k] <= Q_S[k]*(1 - x[i,j,k]) for j in pickups for i in nodes for k in vehicles), name="SCapacity2")
    print("SCapacity3")
    m.addConstrs((q_S[i, k] - L_S[j] - q_S[n+j, k] <= Q_S[k] * (1 - x[i, j, k]) for j in pickups for i in nodes for k in vehicles), name="SCapacity3")
    print("SCapacity4")
    m.addConstrs((quicksum(L_S[i]*x[i,j,k] for j in nodes) <= q_S[i,k] for i in pickups for k in vehicles), name="SCapacity4")
    print("SCapacity5")
    m.addConstrs((q_S[i,k] <= quicksum(Q_S[k]*x[i,j,k] for j in nodes) for i in pickups for k in vehicles), name="SCapacity5")
    print("SCapacity6")
    m.addConstrs((quicksum((Q_S[k] - L_S[i])*x[n+i,j,k] for j in nodes) >= q_S[n+i,k] for i in pickups for k in vehicles), name="SCapacity6")



    # WHEELCHAIR SEATS CAPACITY CONSTRAINTS
    print("WCapacity1")
    m.addConstrs((q_W[nodes_depots[2*n+k], k] == 0 for k in vehicles), name="WCapacity1")
    print("WCapacity2")
    m.addConstrs((q_W[i, k] + L_W[j] - q_W[j, k] <= Q_W[k] * (1 - x[i, j, k]) for j in pickups for i in nodes for k in vehicles), name="WCapacity2")
    print("WCapacity3")
    m.addConstrs((q_W[i, k] - L_W[j] - q_W[n + j, k] <= Q_W[k] * (1 - x[i, j, k]) for j in pickups for i in nodes for k in vehicles), name="WCapacity3")
    print("WCapacity4")
    m.addConstrs((quicksum(L_W[i] * x[i, j, k] for j in nodes) <= q_W[i, k] for i in pickups for k in vehicles),name="WCapacity4")
    print("WCapacity5")
    m.addConstrs((q_W[i, k] <= quicksum(Q_W[k] * x[i, j, k] for j in nodes) for i in pickups for k in vehicles),name="WCapacity5")
    print("WCapacity6")
    m.addConstrs((quicksum((Q_W[k] - L_W[i]) * x[n + i, j, k] for j in nodes) >= q_W[n + i, k] for i in pickups for k in vehicles), name="WCapacity6")



    # TIME WINDOW CONSTRAINTS
    print("TimeWindow1")
    m.addConstrs((T_S_L[i].timestamp() - l[i] <= t[i,k] for i in nodes for k in vehicles), name="TimeWindow1")
    print("TimeWindow2")
    m.addConstrs((t[i,k] <= T_S_U[i].timestamp() + u[i] for i in nodes for k in vehicles), name="TimeWindow2")
    print("TimeWindow3")
    m.addConstrs((T_H_L[i].timestamp() <= t[i,k] for i in nodes for k in vehicles), name="TimeWindow3")
    print("TimeWindow4")
    m.addConstrs((t[i,k] <= T_H_U[i].timestamp() for i in nodes for k in vehicles), name="TimeWindow4")
    print("TimeWindow5")
    m.addConstrs((t[i,k] + T_ij[i][j].total_seconds() - t[j,k] <= M_ij[i][j].total_seconds()*(1 - x[i,j,k]) for i in nodes for j in nodes for k in vehicles), name="TimeWindow5")
    print("TimeWindow6")
    m.addConstrs((t[i,k] + T_ij[i][n+i].total_seconds() - t[n+i,k] <= 0 for i in pickups for k in vehicles), name="TimeWindow6")



    # RIDE TIME CONSTRAINTS
    print("RideTime1")
    m.addConstrs((t[n+i,k] - t[i,k] - (1 + F)*T_ij[i][n+i].total_seconds() <= M*w[i] for i in pickups for k in vehicles), name="RideTime1")
    print("RideTime2")
    m.addConstrs((d[i] >= t[n+i,k] - t[i,k] -M*(1 - w[i]) for i in pickups for k in vehicles), name="RideTime2")



    # RUN MODEL
    m.optimize()

except GurobiError as e:
    print('Error reported')
    print(e.message)