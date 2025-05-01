import pandas as pd
from gurobipy import Model, GRB, quicksum

# Read data from csv files
storage_cost_data = pd.read_csv('storage_cost.csv')
solar_cost_data = pd.read_csv('solar_cost.csv')
grid_cost_data = pd.read_csv('hourly_prices.csv')
efficiency_data = pd.read_csv('efficiency.csv')
capacity_factor_data = pd.read_csv('hourly_solar_capacity_factor.csv')

# Extract parameters 
C_BESS = storage_cost_data['cost_per_kWh'].values[0]
C_sol = solar_cost_data['cost_per_sqm'].values[0]
C_grid = grid_cost_data['cost_per_kWh'].values
CF_solar = capacity_factor_data['capacity_factor'].values
# we plan here to put a 8760 values list (for the whole year), then the rest of the code adapts to it.

MC_BESS = storage_cost_data['marginal_cost_per_kWh'].values[0]
MC_sol = solar_cost_data['marginal_cost_per_kWh'].values[0]

P_max_BESS = storage_cost_data['max_power_per_kWh'].values[0]
P_max_sol = solar_cost_data['max_power_per_sqm'].values[0]

eta_C = efficiency_data['charging_efficiency'].values[0]
eta_D = efficiency_data['discharging_efficiency'].values[0]
demand = pd.read_csv('hourly_demand.csv')['demand'].values
model = Model('EnergyOptimization')

# Decision variables
n_BESS = model.addVar(name='n_BESS')  # Number of storage systems kWh
n_sol = model.addVar(name='n_sol')  # Number of solar panels sqm
p_D_BESS = model.addVars(len(C_grid), name='D_BESS')  # Power supplied by the storage system
p_C_BESS = model.addVars(len(C_grid), name='C_BESS')  # Power charged into the storage system
P_grid = model.addVars(len(C_grid), name='P_grid')  # Power supplied by the grid
P_sol = model.addVars(len(C_grid), name='P_sol')   # Power supplied by solar panels
q = model.addVars(len(C_grid), name='q')  # State of charge of the storage system


# Limit to 3 hours for the optimization
C_grid = C_grid[:3]
demand = demand[:3]
CF_solar = CF_solar[:3]


# Redefine decision variables for 3 hours
p_D_BESS = model.addVars(3, name='D_BESS')
p_C_BESS = model.addVars(3, name='C_BESS')
P_grid = model.addVars(3, name='P_grid')
P_sol = model.addVars(3, name='P_sol')
q = model.addVars(3, name='q')

# Objective function: Minimize total cost
objective = C_BESS * n_BESS + C_sol * n_sol + quicksum(C_grid[h] * P_grid[h] + MC_sol * P_sol[h] + MC_BESS * p_C_BESS[h] for h in range(len(C_grid)))
model.setObjective(objective, GRB.MINIMIZE)

# Constraints
for h in range(len(C_grid)):
    # Storage system state of charge constraint
    q = model.addVar(name=f'q_{h}')
    model.addConstr(q == q - p_D_BESS[h] / eta_D + p_C_BESS[h] * eta_C, name=f'SOC_{h}')

    # Power balance constraint
    model.addConstr(p_D_BESS[h] + P_sol[h] + P_grid[h] == demand[h], name=f'PowerBalance_{h}') #maybe need to relax to >=

    # Maximum power constraints
    model.addConstr(p_D_BESS[h] <= P_max_BESS * n_BESS, name=f'MaxPowerBESS_{h}')
    model.addConstr(P_sol[h] <= P_max_sol * n_sol * CF_solar[h]/30, name=f'MaxPowerSol_{h}')

# Optimize the model
model.optimize()

# Output results
if model.status == GRB.OPTIMAL:
    print('Optimal solution found:')
    for h in range(len(C_grid)):
        print(f'Hour {h}: p_D_BESS = {p_D_BESS[h].x}, p_C_BESS = {p_C_BESS[h].x}, P_grid = {P_grid[h].x}, P_sol = {P_sol[h].x}')
else:
    print('No optimal solution found.')
