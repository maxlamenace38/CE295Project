import pandas as pd
from gurobipy import Model, GRB, quicksum

# Read data from csv files
storage_cost_data = pd.read_csv('storage_cost.csv')
solar_cost_data = pd.read_csv('solar_cost.csv')
grid_cost_data = pd.read_csv('grid_cost.csv')
efficiency_data = pd.read_csv('efficiency.csv')

# Extract parameters 
C_BESS = storage_cost_data['cost_per_kWh'].values[0]
C_sol = solar_cost_data['cost_per_sqm'].values[0]
C_grid = grid_cost_data['cost_per_kWh'].values

MC_BESS = storage_cost_data['marginal_cost_per_kW'].values[0]
MC_sol = solar_cost_data['marginal_cost_per_kW'].values[0]

P_BESS = storage_cost_data['max_power_per_kWh'].values[0]
P_sol = solar_cost_data['max_power_per_sqm'].values[0]

eta_C = efficiency_data['charging_efficiency'].values[0]
eta_D = efficiency_data['discharging_efficiency'].values[0]
demand = pd.read_csv('demand.csv')['demand'].values
model = Model('EnergyOptimization')

# Decision variables
D_BESS = model.addVars(len(C_grid), name='D_BESS')  # Power supplied by the storage system
C_BESS = model.addVars(len(C_grid), name='C_BESS')  # Power charged into the storage system
P_grid = model.addVars(len(C_grid), name='P_grid')  # Power supplied by the grid
P_sol = model.addVars(len(C_grid), name='P_sol')   # Power supplied by solar panels

# Objective function: Minimize total cost
objective = quicksum(C_BESS[h] * D_BESS[h] + C_sol * P_sol[h] + C_grid[h] * P_grid[h] for h in range(len(C_grid)))
model.setObjective(objective, GRB.MINIMIZE)

# Constraints
for h in range(len(C_grid)):
    # Storage system state of charge constraint
    q_h = model.addVar(name=f'q_{h}')
    model.addConstr(q_h == q_h - D_BESS[h] / eta_D + C_BESS[h] * eta_C, name=f'SOC_{h}')

    # Power balance constraint
    model.addConstr(D_BESS[h] + P_sol[h] + P_grid[h] == demand[h], name=f'PowerBalance_{h}')

    # Maximum power constraints
    model.addConstr(D_BESS[h] <= P_BESS, name=f'MaxPowerBESS_{h}')
    model.addConstr(P_sol[h] <= P_sol, name=f'MaxPowerSol_{h}')

# Optimize the model
model.optimize()

# Output results
if model.status == GRB.OPTIMAL:
    print('Optimal solution found:')
    for h in range(len(C_grid)):
        print(f'Hour {h}: D_BESS = {D_BESS[h].x}, C_BESS = {C_BESS[h].x}, P_grid = {P_grid[h].x}, P_sol = {P_sol[h].x}')
else:
    print('No optimal solution found.')
