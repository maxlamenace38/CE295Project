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
demand = pd.to_numeric(demand, errors='coerce')  # Convert to numeric, set invalid values to NaN
model = Model('EnergyOptimization')

# Decision variables
n_BESS = model.addVar(name='n_BESS')  # Number of storage systems kWh
n_sol = model.addVar(name='n_sol')  # Number of solar panels sqm
p_D_BESS = model.addVars(len(C_grid), name='D_BESS')  # Power supplied by the storage system
p_C_BESS = model.addVars(len(C_grid), name='C_BESS')  # Power charged into the storage system
P_grid = model.addVars(len(C_grid), name='P_grid')  # Power supplied by the grid
P_sol = model.addVars(len(C_grid), name='P_sol')   # Power supplied by solar panels
q = model.addVars(len(C_grid), name='q')  # State of charge of the storage system


# Objective function: Minimize total cost
objective = C_BESS * n_BESS + C_sol * n_sol + quicksum(C_grid[h] * P_grid[h] + MC_sol * P_sol[h] + MC_BESS * p_C_BESS[h] for h in range(len(C_grid)))
model.setObjective(objective, GRB.MINIMIZE)

# Constraints
for h in range(len(C_grid)):
    # Storage system state of charge constraint
    if h == 0:
        model.addConstr(q[h] == 0 + p_C_BESS[h]*eta_C - p_D_BESS[h]/eta_D, name=f'SOC_init')
    else:
        model.addConstr(q[h] == q[h-1] + p_C_BESS[h]*eta_C - p_D_BESS[h]/eta_D, name=f'SOC_{h}')


    # Power balance constraint
    model.addConstr(p_D_BESS[h] + P_sol[h] + P_grid[h] >= demand[h], name=f'PowerBalance_{h}') #maybe need to relax to >=

    # Maximum power constraints
    model.addConstr(p_D_BESS[h] <= P_max_BESS * n_BESS, name=f'MaxPowerBESS_{h}')
    model.addConstr(P_sol[h] <= P_max_sol * n_sol * CF_solar[h]/100, name=f'MaxPowerSol_{h}')
    #SOC constraints
    model.addConstr(q[h] <= n_BESS, name=f'SOC_capacity_{h}')
    model.addConstr(q[h] >= 0, name=f'SOC_min_{h}')
    model.addConstr(p_C_BESS[h]<= P_sol[h], name=f'ChargePower_{h}') # Charging power comes from solar power


# Optimize the model
model.optimize()

# Output results
if model.status == GRB.OPTIMAL:
    print('Optimal solution found:')
    for h in range(len(C_grid)):
        print(f'Hour {h}: p_D_BESS = {p_D_BESS[h].x}, p_C_BESS = {p_C_BESS[h].x}, P_grid = {P_grid[h].x}, P_sol = {P_sol[h].x}')
else:
    print('No optimal solution found.')


### Plotting the results
import matplotlib.pyplot as plt  

# Output results
if model.status == GRB.OPTIMAL:
    print('Optimal solution found:')
    
    # Extract results for plotting
    p_D_BESS_values = [p_D_BESS[h].x for h in range(len(C_grid))]
    p_C_BESS_values = [p_C_BESS[h].x for h in range(len(C_grid))]
    P_grid_values = [P_grid[h].x for h in range(len(C_grid))]
    P_sol_values = [P_sol[h].x for h in range(len(C_grid))]
    
    # Print results for each hour
    for h in range(len(C_grid)):
        print(f'Hour {h}: p_D_BESS = {p_D_BESS_values[h]}, p_C_BESS = {p_C_BESS_values[h]}, P_grid = {P_grid_values[h]}, P_sol = {P_sol_values[h]}')
    print("n_BESS:",n_BESS.x,"n_solar:", n_sol.x)
    # Plot results
    hours = range(len(C_grid))
    plt.figure(figsize=(12, 6))
    
    plt.plot(hours, P_grid_values, label='Grid Power', color='green')
    plt.plot(hours, P_sol_values, label='Solar Power', color='red')
    plt.plot(hours, p_C_BESS_values, label='Charge Power (BESS)', color='orange')
    plt.plot(hours, p_D_BESS_values, label='Discharge Power (BESS)', color='blue')
    
    
    plt.xlabel('Hour')
    plt.ylabel('Power (kW)')
    plt.title('Power Distribution Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

else:
    print('No optimal solution found.')