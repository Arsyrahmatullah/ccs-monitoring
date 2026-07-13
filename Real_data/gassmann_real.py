# Modul5_RealData/gassmann_real.py
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import lasio

# Robust path injection to import the calibrated Gassmann engine from Modul4
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Modul4_Gassmann.gassmann import gassmann_substitution

# ── 1. Smart Path Resolution for Data Loading ────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
possible_paths = [
    os.path.abspath(os.path.join(script_dir, '..', 'well_data')),
    os.path.abspath(os.path.join(script_dir, 'well_data'))
]

las_file_path = None
for p in possible_paths:
    if os.path.exists(p):
        las_files = [f for f in os.listdir(p) if f.endswith('.las')]
        if las_files:
            las_file_path = os.path.join(p, las_files[0])
            break

# ── 2. Well Log Data Processing Block ─────────────────────────────
if las_file_path is None:
    print("[WARNING] Real LAS well log file not found in 'well_data/' directory.")
    print("[INFO] Generating synthetic well log baseline to maintain repository workflow functionality.")
    
    # Generate representative synthetic log data mimicking Utsira Sand reservoir interval
    depth = np.linspace(800, 1000, 500)
    nphi = 0.32 + 0.02 * np.random.randn(500)  # High porosity sand (~32%)
    nphi = np.clip(nphi, 0.20, 0.40)
    
    rhob = 2.65 * (1 - nphi) + 1.0 * nphi
    vp = 3900 - 2900 * nphi + 120 * np.random.randn(500)
    vs = vp / 2.0  
else:
    print(f"[SUCCESS] Loading real Sleipner benchmark dataset from: {las_file_path}")
    las = lasio.read(las_file_path)
    df = las.df().dropna(subset=['DT', 'RHOB', 'NPHI'])
    
    depth = df.index.values
    nphi = df['NPHI'].values / 100.0 if np.max(df['NPHI'].values) > 1.0 else df['NPHI'].values
    rhob = df['RHOB'].values
    vp = (1.0e6 / df['DT'].values) * 0.3048  
    vs = vp / 2.0  

# ── 3. Confined Fluid Substitution Framework (Targeted Reservoir) ──
k_m = 37.0            # Quartz dominated sandstone matrix bulk modulus (GPa)
k_brine = 2.2         # Saline formation water bulk modulus (GPa)
k_co2 = 0.06          # Supercritical CO2 bulk modulus (GPa)
rho_brine = 1030.0    # Saline brine density (kg/m3)
rho_co2 = 650.0       # Supercritical CO2 density (kg/m3)
rho_matrix = 2.65     # Sand matrix grain density (g/cm3)
s_co2_target = 0.60   # 60% CO2 saturation scenario

vp_gassmann = vp.copy()
rho_gassmann = rhob.copy()

# Apply fluid substitution ONLY inside the specified reservoir interval
for idx in range(len(depth)):
    # 💡 CRITICAL FIX: Restrict CO2 plume placement between 900m and 960m depths
    if 900.0 <= depth[idx] <= 960.0:
        current_s_co2 = s_co2_target
    else:
        current_s_co2 = 0.0  # Outside the reservoir, fluid remains 100% baseline brine
        
    current_phi = nphi[idx] if nphi[idx] > 0.01 else 0.01
    
    v_mon, _, r_mon = gassmann_substitution(
        vp[idx], vs[idx], rhob[idx], current_phi, current_s_co2,
        k_m, k_brine, k_co2, rho_brine, rho_co2, rho_matrix
    )
    vp_gassmann[idx] = v_mon
    rho_gassmann[idx] = r_mon

# Evaluate physical discrepancies against the static native -10% assumption model
vp_static_assumption = vp.copy()
for idx in range(len(depth)):
    if 900.0 <= depth[idx] <= 960.0:
        vp_static_assumption[idx] = vp[idx] * 0.90

# ── 4. Cross-Plot & Depth-Log Visualization ──────────────────────
fig, axes = plt.subplots(1, 3, figsize=(12, 7), sharey=True)

# Panel 1: Porosity and Density Core Profiles
axes[0].plot(nphi, depth, color='darkgreen', label='Porosity (NPHI)', alpha=0.8)
ax0_twin = axes[0].twiny()
ax0_twin.plot(rhob, depth, color='black', label='Density (RHOB)', linestyle='--', alpha=0.7)
axes[0].set_xlabel('Porosity (v/v)', color='darkgreen')
ax0_twin.set_xlabel('Density (g/cm³)', color='black')
axes[0].set_title('Petrophysical Inputs', weight='bold', pad=20)
axes[0].grid(True, alpha=0.3)

# Panel 2: Velocity Substitution Fluid Response Comparison
axes[1].plot(vp, depth, color='gray', label='Baseline (100% Brine)', alpha=0.7)
axes[1].plot(vp_static_assumption, depth, color='darkorange', label='Naive Assumption (-10%)', linestyle=':')
axes[1].plot(vp_gassmann, depth, color='crimson', label=f'Exact Gassmann ({s_co2_target*100:.0f}% CO2)', linewidth=1.8)
# Highlight target reservoir interval visually
axes[1].axhspan(900, 960, color='yellow', alpha=0.15, label='Target Reservoir Zone')
axes[1].set_xlabel('P-Wave Velocity (m/s)')
axes[1].set_title('Fluid Substitution Output', weight='bold', pad=20)
axes[1].grid(True, alpha=0.3)
axes[1].legend(loc='lower left', fontsize='small')

# Panel 3: Velocity Reduction Quantified Residual Delta (%)
delta_static = np.zeros_like(depth)
delta_gassmann = ((vp_gassmann - vp) / vp) * 100
for idx in range(len(depth)):
    if 900.0 <= depth[idx] <= 960.0:
        delta_static[idx] = -10.0

axes[2].plot(delta_static, depth, color='darkorange', linestyle=':', label='Static Model (-10%)')
axes[2].plot(delta_gassmann, depth, color='crimson', label='Gassmann Dynamic Model', linewidth=1.5)
axes[2].axhspan(900, 960, color='yellow', alpha=0.15)
axes[2].axvline(x=0, color='black', linestyle='--', alpha=0.5)
axes[2].set_xlabel('Velocity Change ΔVp (%)')
axes[2].set_title('Calculated 4D Log Anomaly (%)', weight='bold', pad=20)
axes[2].grid(True, alpha=0.3)
axes[2].legend(loc='lower left', fontsize='small')

# Format structural depth framework (increasing depth downwards)
axes[0].invert_yaxis()
axes[0].set_ylabel('Depth (m)', fontsize=11, weight='bold')

plt.tight_layout()
output_img = os.path.join(script_dir, 'gassmann_real.png')
plt.savefig(output_img, dpi=150)
plt.show()

print(f"[SUCCESS] Modul 5: Sleipner dataset fluid substitution compiled. Plot saved to: {output_img}")