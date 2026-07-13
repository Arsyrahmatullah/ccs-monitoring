# src/ccs_monitoring/presets.py

RESERVOIR_PRESETS = {
    "Matindok (Thesis Reference)": {
        "description": "Parameters calibrated from the Minahaki Carbonate Formation, Central Sulawesi (Undergraduate Thesis Model).",
        "k_m": 45.0,        # GPa
        "k_brine": 2.8,     # GPa
        "k_co2": 0.08,      # GPa
        "rho_matrix": 2.71, # g/cm³
        "rho_brine": 1.025, # g/cm³
        "rho_co2": 0.700,   # g/cm³
        "phi": 0.13,        
        "phi_min": 0.05,    # Thesis distribution range bounds
        "phi_max": 0.22,
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
        "phi_min": 0.28,    # Joodaki §2 Sandstone distribution scale
        "phi_max": 0.40,
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
        "phi_min": 0.12,
        "phi_max": 0.30,
        "citation": "Baltic Sea Carbon Sequestration Consortium, Regional Deep Aquifer Feasibility Study Table 2."
    }
}

NOISE_FLOOR_PRESETS = {
    "Raw Single-Shot Gather (Low Quality)": {
        "nrms_floor": 0.55,
        "source": "White et al. (2015) - Aquistore Field Baseline Data",
        "description": "Highly unrepeatable signature domain dominated by raw environmental surface waves and noise grids."
    },
    "Typical Field Repeatability (Rule of Thumb)": {
        "nrms_floor": 0.30,
        "source": "Harris et al. (2016) - Time-Lapse Performance Review",
        "description": "Standard industry expectation constraint for basic post-stack processed permanent seismic monitoring grids."
    },
    "Migrated & Stacked Data (Sleipner Quality)": {
        "nrms_floor": 0.07,
        "source": "Roach et al. (2015) - Sleipner 4D Stack Feasibility",
        "description": "Ultra-clean repeatable dataset achieved via rigorous continuous downhole processing workflows."
    }
}