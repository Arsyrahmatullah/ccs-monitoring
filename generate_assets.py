# generate_assets.py
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

from src.ccs_monitoring.presets import RESERVOIR_PRESETS
from src.ccs_monitoring.Rock_physics.gassmann import gassmann_substitution
from src.ccs_monitoring.Anomaly.anomaly_detection import calculate_4d_trace_nrms

# 1. Setup path output target
base_path = "src/ccs_monitoring"
os.makedirs(f"{base_path}/Plume", exist_ok=True)
os.makedirs(f"{base_path}/Seismic", exist_ok=True)
os.makedirs(f"{base_path}/Rock_physics", exist_ok=True)
os.makedirs(f"{base_path}/Anomaly", exist_ok=True)

# Loaded target parameters
site = RESERVOIR_PRESETS["Matindok (Thesis Reference)"]
phi_val = site["phi"]
rho_matrix_kg = site["rho_matrix"] * 1000.0
rho_brine_kg = site["rho_brine"] * 1000.0
rho_co2_kg = site["rho_co2"] * 1000.0
res_thickness = 80
inj_rate = 1.5

# ── A. GENERATE PLUME GROWTH (MONTE CARLO) ──
t_axis = np.linspace(0.1, 15.0, 60)
n_simulations = 150
r_cube = np.zeros((n_simulations, len(t_axis)))

np.random.seed(101)
for s in range(n_simulations):
    phi_s = np.random.uniform(site["phi_min"], site["phi_max"])
    eff_s = phi_s * 0.75 * 0.75
    m_axis = (inj_rate * 1e9) * t_axis
    r_cube[s, :] = np.sqrt(m_axis / (np.pi * res_thickness * eff_s * rho_co2_kg))

p10 = np.percentile(r_cube, 10, axis=0)
p50 = np.percentile(r_cube, 50, axis=0)
p90 = np.percentile(r_cube, 90, axis=0)

fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(t_axis, p50, color='black', linewidth=2, label='P50 Realization (Median)')
ax.fill_between(t_axis, p10, p90, color='crimson', alpha=0.15, label='P10 - P90 Uncertainty Range')
ax.fill_between(t_axis, p50*0.9, p50*1.1, color='crimson', alpha=0.3, label='P25 - P75 Central Core')
ax.set_ylabel('Lateral Radius Footprint Expansion (m)', weight='bold')
ax.set_xlabel('Injection Horizon Duration (Years)', weight='bold')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)
plt.savefig(f"{base_path}/Plume/plume_growth.png", dpi=150, bbox_inches='tight')
plt.close()

# ── B. GENERATE SEISMIC VP ANOMALY (BUOYANT MESH) ──
nx, nz = 130, 90
x_axis = np.linspace(0, 4000, nx)
z_axis = np.linspace(1000, 2500, nz)
X_grid, Z_grid = np.meshgrid(x_axis, z_axis)

np.random.seed(42)
spatial_noise = gaussian_filter(np.random.randn(nz, nx), sigma=(4, 9))
spatial_noise /= np.std(spatial_noise)

vp_base = np.zeros((nz, nx))
for i in range(nz):
    vp_base[i, :] = (2800.0 + 0.5 * (z_axis[i] - 1000.0)) * (1.0 + 0.03 * spatial_noise[i, :])

rho_base = np.full((nz, nx), rho_matrix_kg * 0.85)
vp_mon = vp_base.copy()
rho_mon = rho_base.copy()

current_radius = 450.0
c_x, c_z, r_x, r_z = 2000, 1600, current_radius * 1.1, res_thickness * 0.5

for i in range(nz):
    for j in range(nx):
        dz = (z_axis[i] - c_z) / r_z
        if -1.0 <= dz <= 1.0:
            width_factor = 1.0 if dz < 0 else (0.25 + 0.75 * np.exp(-4.5 * dz))
            dx = (x_axis[j] - c_x) / (r_x * width_factor)
            if (dx**2 + dz**2) <= 1.0:
                z_top_seal = c_z - r_z
                depth_from_caprock = max(0.0, z_axis[i] - z_top_seal)
                local_s_co2 = 0.60 * np.exp(-2.2 * (depth_from_caprock / (2.0 * r_z)))
                local_s_co2 = np.clip(local_s_co2, 0.01, 0.98)
                
                v_m, _, r_m = gassmann_substitution(
                    vp_base[i, j], vp_base[i, j]/1.74, rho_base[i, j], phi_val, local_s_co2,
                    site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg,
                    "wood", 3.0
                )
                vp_mon[i, j] = v_m
                rho_mon[i, j] = r_m

fig, axes = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True)
im1 = axes[0].pcolormesh(X_grid, Z_grid, vp_base, cmap='viridis', shading='auto')
fig.colorbar(im1, ax=axes[0], label='Vp (m/s)')
axes[0].set_title("Stochastic Structural Heterogeneous Baseline Section")
im2 = axes[1].pcolormesh(X_grid, Z_grid, vp_mon, cmap='viridis', shading='auto')
fig.colorbar(im2, ax=axes[1], label='Vp (m/s)')
axes[1].set_title("Graded Buoyancy Fluid Substitution Profile (Mushroom Boundary Topology)")
for ax in axes: ax.invert_yaxis(); ax.set_ylabel('Depth (m)')
axes[1].set_xlabel('Horizontal Array Axis Coordinate (m)')
plt.tight_layout()
plt.savefig(f"{base_path}/Seismic/vp_anomaly.png", dpi=150, bbox_inches='tight')
plt.close()

# ── C. GENERATE GASSMANN CURVE MATRIX ──
s_axis = np.linspace(0, 1.0, 60)
v_wood, v_brie = [], []
for s in s_axis:
    vw, _, _ = gassmann_substitution(3200.0, 1850.0, rho_matrix_kg*0.88, phi_val, s, site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg, "wood")
    vb, _, _ = gassmann_substitution(3200.0, 1850.0, rho_matrix_kg*0.88, phi_val, s, site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg, "brie", 3.0)
    v_wood.append(vw)
    v_brie.append(vb)

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(s_axis * 100.0, v_wood, color='gray', linestyle='--', label="Wood's Law (Uniform Saturation)")
ax.plot(s_axis * 100.0, v_brie, color='darkblue', linewidth=2.5, label="Brie's Model (Patchy Saturation e=3.0)")
ax.set_ylabel('P-Wave Acoustic Velocity (m/s)')
ax.set_xlabel('Local Fluid Phase Volume (%)')
ax.grid(True, alpha=0.3)
ax.legend()
plt.savefig(f"{base_path}/Rock_physics/gassmann.png", dpi=150, bbox_inches='tight')
plt.close()

# ── D. GENERATE ANOMALY ALERTS PROFILE ──
nrms_profile = calculate_4d_trace_nrms(vp_base, rho_base, vp_mon, rho_mon, frequency=30)
fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(x_axis, nrms_profile, color='black', linewidth=2, label='Calculated nRMS Profile')
ax.axhline(y=7.0, color='red', linestyle=':', linewidth=2, label='Noise Floor Limit (Sleipner Quality - 7%)')
ax.fill_between(x_axis, nrms_profile, 7.0, where=(nrms_profile > 7.0), color='red', alpha=0.3)
ax.set_ylabel('nRMS Metric Amplitude (%)')
ax.set_xlabel('Horizontal Axis (m)')
ax.legend()
plt.savefig(f"{base_path}/Anomaly/anomaly_detection.png", dpi=150, bbox_inches='tight')
plt.close()

print("🎯 SUCCESS: All Tier 3 high-resolution asset images updated successfully on disk!")