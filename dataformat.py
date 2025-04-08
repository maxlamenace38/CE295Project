import pandas as pd
import gurobipy as gp

# Create data for storage_cost.csv
storage_cost_data = {
    "cost_per_kWh": [100] * 8760,  # Example cost per kWh
    "marginal_cost_per_kW": [10] * 8760,  # Example marginal cost per kW
    "max_power_per_kWh": [50] * 8760  # Example max power per kWh
}
pd.DataFrame(storage_cost_data).to_csv("storage_cost.csv", index=False)

# Create data for solar_cost.csv
solar_cost_data = {
    "cost_per_sqm": [200] * 8760,  # Example cost per square meter
    "marginal_cost_per_kW": [15] * 8760,  # Example marginal cost per kW
    "max_power_per_sqm": [100] * 8760  # Example max power per square meter
}
pd.DataFrame(solar_cost_data).to_csv("solar_cost.csv", index=False)

# Create data for grid_cost.csv
grid_cost_data = {
    "cost_per_kWh": [0.1, 0.12, 0.15, 0.2] * (8760 // 4)  # Example cost per kWh for each hour
}
pd.DataFrame(grid_cost_data).to_csv("grid_cost.csv", index=False)

# Create data for efficiency.csv
efficiency_data = {
    "charging_efficiency": [0.9],  # Example charging efficiency
    "discharging_efficiency": [0.85]  # Example discharging efficiency
}
pd.DataFrame(efficiency_data).to_csv("efficiency.csv", index=False)

# Create data for demand.csv
demand_data = {
    "demand": [30, 40, 50, 60] * (8760 // 4)  # Example demand for each hour
}
pd.DataFrame(demand_data).to_csv("demand.csv", index=False)

print("All CSV files have been created with 8760 rows.")