import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
from decouple import config
from Models import *


def main():
    """
    This function performs a run for the DDDARP problem, where requests that are known in advance are planned and routed initially,
    as well as new requests are received throughout the day. When a new request arrives, a reoptimization model is utilized to first
    decide if the new request is accepted or rejected, and if accepted, a new optimal route is planned based off of the earlier plan
    and the new request.
    """

    initial_route_plan = 


if __name__ == "__main__":
    main()
