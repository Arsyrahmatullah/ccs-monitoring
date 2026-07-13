# Modul1_Plume/plume_growth.py
import os
import numpy as np
import matplotlib.pyplot as plt

def estimate_supercritical_co2_density(pressure_mpa, temperature_c):
    """
    Approximates supercritical CO2 density (kg/m3) based on standard 
    hydrocarbon reservoir pressure and temperature empirical relationships.
    """
    rho = 750.0 + (pressure_mpa * 12.5) - (temperature_c * 4.2)
    return np.clip(rho, 400.0, 850.0)

# ── 1. Smart Path Resolution for Clean Image Saving ────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
# FIXED: Modified filename to match the standard 'plume_growth.png' setup
output_file = os.path.join(script_dir, 'plume_growth.png')

# ── 2. In-Situ Subsurface Thermodynamic Profile ────────────────────
reservoir_depth = 1600.0      # Target depth in meters (Minahaki Fm)
reservoir_thickness = 80.0    # Gross reservoir thickness H (meters)
p_surface = 0.1013            # Atmospheric pressure (MPa)
t_surface = 25.0              # Ambient surface temperature (°C)
rho_brine = 1025.0            # Saline water/brine density (kg/m3)
g_acceleration = 9.81         # Acceleration of gravity (m/s2)
geothermal_gradient = 3.5     # Temperature increase (°C per 100 meters)

# Hydrostatic pressure and geothermal temperature calculations
p_reservoir = p_surface + (rho_brine * g_acceleration * reservoir_depth) * 1e-6
t_reservoir = t_surface + (geothermal_gradient * (reservoir_depth / 100.0))
rho_co2_insitu = estimate_supercritical_co2_density(p_reservoir, t_reservoir)

# ── 3. Calibrated Rock Properties Matrix ───────────────────────────
phi_effective = 0.13          # Effective rock matrix porosity (13%)
net_to_gross = 0.75           # NTG ratio (75% net porous carbonate layers)
s_wirr = 0.25                 # Irreducible water saturation (25% pore space locked)
s_co2_max = 1.0 - s_wirr      # Maximum displaceable CO2 saturation limit

# Calculate net effective storage volume capacity factor per cubic meter of rock
storage_efficiency_factor = phi_effective * net_to_gross * s_co2_max

# ── 4. Dynamic Time-Lapse Plume Expansion Simulation ──────────────
injection_rate_tons_day = 3715.0
yearly_mass_injected_kg = injection_rate_tons_day * 365.25 * 1000.0 # kg/year

simulation_years = np.linspace(0, 10, 100)
cumulative_mass_kg = yearly_mass_injected_kg * simulation_years

# Physics-driven volumetric tracking equation (Cylindrical Gravity Footprint Radius)
plume_radius_m = np.sqrt(
    cumulative_mass_kg / (np.pi * reservoir_thickness * storage_efficiency_factor * rho_co2_insitu)
)

# ── 5. Analytical Visualization ───────────────────────────────────
fig, ax1 = plt.subplots(figsize=(10, 6))

# Primary Axis: Subsurface Lateral Plume Front Propagation Radius
color_radius = '#d9383a'
ax1.plot(simulation_years, plume_radius_m, color=color_radius, linewidth=2.5, 
         label='Dynamic Footprint Radius (Physics-Driven)')
ax1.set_xlabel('Injection Duration (Years)', fontsize=11, weight='bold')
ax1.set_ylabel('Calculated Plume Front Radius (meters)', color=color_radius, fontsize=11, weight='bold')
ax1.tick_params(axis='y', labelcolor=color_radius)
ax1.grid(True, linestyle='--', alpha=0.4)

# Secondary Axis: Cumulative Storage Mass Trajectory
ax2 = ax1.twinx()
color_mass = '#2b5c8f'
cumulative_mass_mt = cumulative_mass_kg / 1e9 # Convert to Million Tons
ax2.plot(simulation_years, cumulative_mass_mt, color=color_mass, linewidth=2, linestyle='--',
         label='Cumulative Mass Stored (Mt)')
ax2.set_ylabel('Total Sequestrated CO2 Mass (Million Tons / Mt)', color=color_mass, fontsize=11, weight='bold')
ax2.tick_params(axis='y', labelcolor=color_mass)

# Information annotation box for formal technical review
info_text = (
    f"Reservoir Depth: {reservoir_depth:.0f} m\n"
    f"Fluid Pressure: {p_reservoir:.2f} MPa\n"
    f"Temperature: {t_reservoir:.1f} °C\n"
    f"In-Situ CO2 Density: {rho_co2_insitu:.1f} kg/m³\n"
    f"Rock Capacity Factor: {storage_efficiency_factor*100:.2f}%"
)
props = dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray')
ax1.text(0.05, 0.95, info_text, transform=ax1.transAxes, fontsize=9.5,
         verticalalignment='top', bbox=props)

plt.title('Advanced Dynamic CO2 Plume Front Propagation Model\nIntegrating Subsurface Thermodynamics & Rock Properties Matrix', 
          fontsize=12, weight='bold', pad=15)
fig.tight_layout()

# Save image profile natively as plume_growth.png
plt.savefig(output_file, dpi=150)
plt.show()

print(f"\n=== IN-SITU ROCK PHYSICS MODEL COMPILED ===")
print(f"[SUCCESS] Graphical output saved dynamically to: {output_file}")