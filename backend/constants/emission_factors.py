"""India-specific CO2 emission factors — single source of truth for all calculations.

All values are research-based for Indian conditions. No functions, no side effects on import.
Frontend receives this dict via GET /api/constants — never duplicate these numbers elsewhere.
"""

EMISSION_FACTORS = {
    "transport": {
        # kg CO2 per km — all values are per-passenger for shared modes
        "petrol_car": 0.17,           # kg CO2 per km
        "diesel_car": 0.15,           # kg CO2 per km
        "petrol_two_wheeler": 0.05,   # kg CO2 per km
        "electric_vehicle": 0.02,     # kg CO2 per km — Indian grid factor applied
        "auto_rickshaw": 0.07,        # kg CO2 per km — per passenger
        "bus": 0.02,                  # kg CO2 per km — per passenger
        "metro": 0.01,                # kg CO2 per km — per passenger
        "walking": 0.0,               # kg CO2 per km — zero emissions
        "cycling": 0.0,               # kg CO2 per km — zero emissions
    },
    "diet": {
        # kg CO2 per day — based on average Indian meal patterns
        "non_vegetarian": 5.0,        # kg CO2 per day
        "vegetarian": 2.5,            # kg CO2 per day
        "eggetarian": 3.0,            # kg CO2 per day — between veg and non-veg
        "vegan": 1.5,                 # kg CO2 per day — lowest footprint
    },
    "electricity": {
        "grid_factor": 0.82,          # kg CO2 per kWh — India CEA average (2023)
        "ac_kwh_per_hour": 1.5,       # kWh per hour — typical 1.5-ton split AC
        "fan_kwh_per_hour": 0.075,    # kWh per hour — standard ceiling fan
        "led_kwh_per_hour": 0.01,     # kWh per hour — 10W LED bulb
    },
    "lpg": {
        "kg_co2_per_cylinder": 12.0,  # kg CO2 per cylinder — standard 14.2 kg LPG cylinder
    },
}
