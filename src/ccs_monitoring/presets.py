# src/ccs_monitoring/presets.py

RESERVOIR_PRESETS = {
    "Matindok (Thesis Reference)": {
        "description": "Parameters calibrated from the Minahaki Carbonate Formation, Central Sulawesi (Undergraduate Thesis Model).",
        "k_m": 45.0,        # Mineral Matrix Bulk Modulus (GPa)
        "k_brine": 2.8,     # Brine Bulk Modulus (GPa)
        "k_co2": 0.08,      # Supercritical CO2 Bulk Modulus (GPa)
        "rho_matrix": 2.71, # Grain Density (g/cm³) -> Converted dynamically to kg/m³
        "rho_brine": 1.025, # Brine Density (g/cm³)
        "rho_co2": 0.700,   # In-situ CO2 Density (g/cm³)
        "phi": 0.13,        # Target Baseline Porosity (fraction)
        "citation": "Rahmatullah (2025), Subsurface Monitoring Evaluation Framework for Matindok Carbonate Build-up."
    },
    "Sleipner Utsira (North Sea)": {
        "description": "Standard benchmark parameters from the Utsira Sandstone reservoir saline aquifer, North Sea.",
        "k_m": 37.0,
        "k_brine": 2.2,
        "k_co2": 0.06,
        "rho_matrix": 2.65,
        "rho_brine": 1.030,
        "rho_co2": 0.650,
        "phi": 0.35,
        "citation": "Joodaki et al. (2022) / Chadwick et al. (2005) - Sleipner 4D Benchmark Data Table 3."
    },
    "Baltic Sea Yoldia (Aquifer)": {
        "description": "Calibrated parameters for patchy saturation assessment within regional clean sandstone beds.",
        "k_m": 40.0,
        "k_brine": 2.5,
        "k_co2": 0.07,
        "rho_matrix": 2.68,
        "rho_brine": 1.015,
        "rho_co2": 0.680,
        "phi": 0.22,
        "citation": "Baltic Sea Carbon Sequestration Consortium, Regional Deep Aquifer Feasibility Study Table 2."
    }
}