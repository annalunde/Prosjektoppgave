# A Rolling Horizon Approach to a Dynamic Dial-a-Ride Formulation of Ruter Aldersvennlig Transport

This project studies the dial-a-ride problem (DARP) faced by Ruter Aldersvennlig Trans-port (RAT), a door-to-door transportation service for the elderly in Oslo.  The problem consists of designing vehicle routes and schedules for a number of requests for transportation between given locations.  Each request also specifies a desired pick-up or drop-off time, along with the number of passengers to be transported.  A subset of the requests is known beforehand, while others are revealed throughout the day, thus making the problem partlydynamic.  The problem aims to minimize operational costs while maintaining a sufficientquality of service. We propose a mixed-integer linear program (MILP) formulation of the dynamic DARP faced by RAT. The formulation consists of a model for initial set-up and a re-optimization model for handling incoming events.  These models are used to produce an event-based dynamic solution process for the problem.  The procedure is based on a rolling-horizon framework,  where  parts  of  the  solution  are  iteratively  modified  as  new  requests  arrive throughout the day. 

Figure 1 provides a high-level view of the solution method.

<img src=implementation_flow.PNG width="400" height="500">

**File structure:**

- Models
  - initial_config.py - config file of the initial model
  - initial_model.py - initial model
  - initial_model_validineq.py - initial model with valid inequalities
  - reoptimization_config.py - config file of the reoptimization model
  - reoptimization_model.py - reoptimization model
  - reoptimization_model_validineq.py - reoptimization model with valid inequalities
  - updater_for_reopt.py - updater between intial and reoptimization model
- Preprocessing - preprocessing of initial data
