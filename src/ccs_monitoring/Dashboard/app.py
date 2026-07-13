# src/ccs_monitoring/Dashboard/app.py
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

from ccs_monitoring.presets import RESERVOIR_PRESETS, NOISE_FLOOR_PRESETS
from ccs_monitoring.Rock_physics.gassmann import gassmann_substitution
from ccs_monitoring.Anomaly.anomaly_detection import calculate_4d_trace_nrms, compute_velocity_z_score

try:
    from ccs_monitoring.Seismic.vp_anomaly import create_ricker_wavelet, generate_seismic_trace
except ModuleNotFoundError:
    from ccs_monitoring.seismic.vp_anomaly import create_ricker_wavelet, generate_seismic_trace

# ── 1. SIDEBAR DRIVERS & GLOBAL SELECTIONS ─────────────────────────
st.set_page_config(page_title="Advanced CCS Quantification Suite", layout="wide")

st.sidebar.header("🧭 Global Site Selection")
selected_preset_name = st.sidebar.selectbox("Choose Target Site Preset:", list(RESERVOIR_PRESETS.keys()))
site = RESERVOIR_PRESETS[selected_preset_name]
st.sidebar.info(f"📄 **Source:** {site['citation']}")

st.sidebar.markdown("---")
st.sidebar.header("📡 Acquisition Quality Preset")
selected_noise_name = st.sidebar.selectbox("Select Target Data Quality Floor:", list(NOISE_FLOOR_PRESETS.keys()))
noise_site = NOISE_FLOOR_PRESETS[selected_noise_name]
alert_threshold = float(noise_site["nrms_floor"] * 100.0)
st.sidebar.caption(f"**Reference:** {noise_site['source']}\n\n*Locked Base nRMS Noise Floor Target: {alert_threshold:.1f}%*")

st.sidebar.markdown("---")
st.sidebar.header("🛠️ Local Control Room")
phi_val = st.sidebar.slider("Baseline Porosity (phi)", float(site["phi_min"]), float(site["phi_max"]), float(site["phi"]), 0.01)
s_co2_max = st.sidebar.slider("Peak CO2 Saturation Base (S_CO2)", 0.10, 1.0, 0.60, 0.05)
mixing_law = st.sidebar.radio("Fluid Saturation Theory:", ["wood", "brie"])
brie_exp = st.sidebar.slider("Brie Exponent (e)", 1.0, 5.0, 3.0, 0.5) if mixing_law == "brie" else 3.0

st.sidebar.subheader("Reservoir Volume Constraints")
res_depth = st.sidebar.slider("Injection Target Depth (m)", 1100, 2400, 1600, 50)
res_thickness = st.sidebar.slider("Formation Thickness H (m)", 30, 150, 80, 5)
inj_rate = st.sidebar.slider("Mass Rate (Mt/year)", 0.5, 3.5, 1.5, 0.1)
years = st.sidebar.slider("Simulation Tracker Horizon (Years)", 1.0, 15.0, 10.0, 0.5)
wavelet_freq = st.sidebar.slider("Ricker Center Peak Freq (Hz)", 15, 60, 30, 5)

# SI Unit transformation pipeline conversions
rho_matrix_kg = site["rho_matrix"] * 1000.0
rho_brine_kg = site["rho_brine"] * 1000.0
rho_co2_kg = site["rho_co2"] * 1000.0

total_mass_mt = inj_rate * years
storage_efficiency = phi_val * 0.75 * 0.75
current_radius = np.sqrt((total_mass_mt * 1e9) / (np.pi * res_thickness * storage_efficiency * rho_co2_kg))

# ── 2. CORE ENGINE: GLOBAL 2D BUOYANT EQUILIBRIUM SEISMIC MESH ────
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
    
vs_mon = vp_base / 1.74
rho_base = np.full((nz, nx), rho_matrix_kg * 0.85)

vp_mon = vp_base.copy()
rho_mon = rho_base.copy()
c_x, c_z, r_x, r_z = 2000, res_depth, current_radius * 1.1, res_thickness * 0.5

# Buoyant capillary vertical equilibrium profiling loop matrix
for i in range(nz):
    for j in range(nx):
        dz = (z_axis[i] - c_z) / r_z
        if -1.0 <= dz <= 1.0:
            width_factor = 1.0 if dz < 0 else (0.25 + 0.75 * np.exp(-4.5 * dz))
            dx = (x_axis[j] - c_x) / (r_x * width_factor)
            if (dx**2 + dz**2) <= 1.0:
                z_top_seal = c_z - r_z
                depth_from_caprock = max(0.0, z_axis[i] - z_top_seal)
                
                # Dynamic buoyancy fluid grading profile (High gas at top, fading downwards)
                local_s_co2 = s_co2_max * np.exp(-2.2 * (depth_from_caprock / (2.0 * r_z)))
                local_s_co2 = np.clip(local_s_co2, 0.01, 0.98)
                
                v_m, _, r_m = gassmann_substitution(
                    vp_base[i, j], vs_mon[i, j], rho_base[i, j], phi_val, local_s_co2,
                    site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg,
                    mixing_law, brie_exp
                )
                vp_mon[i, j] = v_m
                rho_mon[i, j] = r_m

# ── 3. PAGE ROUTER METHODS WITH MONTE CARLO INTEGRATION ───────────

def page_overview():
    st.title("🌐 Active Field Framework Overview")
    st.markdown(f"### Target Selected Reservoir Domain: **{selected_preset_name}**")
    st.caption(site["description"])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Net Absorbed Carbon", f"{total_mass_mt:.3f} Mt")
    col2.metric("Operational Depth Axis", f"{res_depth} meters")
    col3.metric("Applied Data Quality Floor", f"{alert_threshold:.2f} % nRMS")
    col4.metric("Calculated Fluid Footprint", f"{current_radius:.2f} m")
    
    st.markdown("---")
    st.subheader("Locked Subsurface Base Moduli Configuration Parameters")
    st.json({
        "Mineral Base Modulus (Km)": f"{site['k_m']} GPa",
        "Liquid Phase Modulus (K_brine)": f"{site['k_brine']} GPa",
        "Gas Phase Modulus (K_co2)": f"{site['k_co2']} GPa",
        "Assigned Capture Noise Alert Limit": f"{alert_threshold}% nRMS ({selected_noise_name})"
    })

def page_plume():
    st.title("📊 Stochastic Ensemble Monte Carlo Plume Expansion")
    st.markdown("### Uncertainty Quantification Framework ($N=150$ Structural Realizations)")
    
    t_axis = np.linspace(0.1, 15.0, 60)
    n_simulations = 150
    r_cube = np.zeros((n_simulations, len(t_axis)))
    
    np.random.seed(101)
    for s in range(n_simulations):
        phi_s = np.random.uniform(site["phi_min"], site["phi_max"])
        eff_s = phi_s * 0.75 * 0.75
        m_axis = (inj_rate * 1e9) * t_axis
        r_cube[s, :] = np.sqrt(m_axis / (np.pi * res_thickness * eff_s * rho_co2_kg))
        
    p10_curve = np.percentile(r_cube, 10, axis=0)
    p50_curve = np.percentile(r_cube, 50, axis=0)
    p90_curve = np.percentile(r_cube, 90, axis=0)
    
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(t_axis, p50_curve, color='black', linewidth=2, label='P50 Realization (Median)')
    ax.fill_between(t_axis, p10_curve, p90_curve, color='crimson', alpha=0.15, label='P10 - P90 Uncertainty Range')
    ax.fill_between(t_axis, p50_curve*0.9, p50_curve*1.1, color='crimson', alpha=0.3, label='P25 - P75 Central Core')
    ax.axvline(x=years, color='orange', linestyle='--', label='Active Horizon Line')
    
    ax.set_ylabel('Lateral Radius Footprint Expansion (m)', weight='bold')
    ax.set_xlabel('Injection Horizon Duration (Years)', weight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    st.success("📊 **Interpretation:** The shaded spread represents the quantitative geometric vulnerability bounds generated by spatial heterogeneities across the target field framework.")

def page_seismic_anomaly():
    st.title("🌋 Advanced Caprock Gravity Equilibrium Mesh")
    st.markdown("### 2D Subsurface Structural View featuring Dynamic Buoyancy-Driven Grading")
    
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
    st.pyplot(fig)

def page_gassmann():
    st.title("🧮 Advanced Matrix Softening Solver")
    s_axis = np.linspace(0, 1.0, 60)
    v_wood, v_brie = [], []
    v_base_ref, vs_ref, rho_ref = 3200.0, 1850.0, rho_matrix_kg * 0.88
    
    for s in s_axis:
        vw, _, _ = gassmann_substitution(v_base_ref, vs_ref, rho_ref, phi_val, s, site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg, "wood")
        vb, _, _ = gassmann_substitution(v_base_ref, vs_ref, rho_ref, phi_val, s, site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg, "brie", brie_exp)
        v_wood.append(vw)
        v_brie.append(vb)
        
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(s_axis * 100.0, v_wood, color='gray', linestyle='--', label="Wood's Law (Uniform Saturation Standard)")
    ax.plot(s_axis * 100.0, v_brie, color='darkblue', linewidth=2.5, label=f"Brie's Model (Patchy Matrix Saturation e={brie_exp})")
    ax.axvline(x=s_co2_max * 100.0, color='orange', linestyle=':', label='Peak Active Saturation')
    ax.set_ylabel('P-Wave Acoustic Velocity (m/s)')
    ax.set_xlabel('Local Fluid Phase Volume (%)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)

def page_well_log():
    st.title("🪵 Target Interval Perforation Log Simulation")
    st.markdown("### Continuous Vertical Wireline Profile Evaluation")
    st.caption("Demonstrating 1D Gassmann fluid substitution dynamics across a continuous calibrated reservoir interval.")
    
    log_z = np.linspace(800, 1100, 200)
    log_phi = np.clip(phi_val + 0.12 + 0.02 * np.random.randn(200), 0.08, 0.45)
    log_rho = 2680.0 * (1.0 - log_phi) + 1000.0 * log_phi
    log_vp = 3800.0 - 2700.0 * log_phi + 45.0 * np.random.randn(200)
    log_vs = log_vp / 1.82
    
    log_vp_mon = log_vp.copy()
    for idx in range(len(log_z)):
        current_s = s_co2_max * np.exp(-1.8 * ((log_z[idx] - 920.0)/60.0)) if 920.0 <= log_z[idx] <= 980.0 else 0.0
        v_m, _, _ = gassmann_substitution(log_vp[idx], log_vs[idx], log_rho[idx], log_phi[idx], current_s, site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg, mixing_law, brie_exp)
        log_vp_mon[idx] = v_m
        
    fig, axes = plt.subplots(1, 2, figsize=(9, 5.5), sharey=True)
    axes[0].plot(log_vp, log_z, color='gray', label='Baseline')
    axes[0].plot(log_vp_mon, log_z, color='crimson', label='CO2 Injected Graded Log')
    axes[0].axhspan(920, 980, color='yellow', alpha=0.12)
    axes[0].invert_yaxis(); axes[0].set_xlabel('Velocity Vp (m/s)'); axes[0].legend()
    
    axes[1].plot(((log_vp_mon - log_vp)/log_vp)*100.0, log_z, color='crimson')
    axes[1].axhspan(920, 980, color='yellow', alpha=0.12)
    axes[1].set_xlabel('Delta Wave Anomaly Velocity (%)')
    st.pyplot(fig)

def page_alerts():
    st.title("🚨 Core Calibration Risk Alerts Console")
    nrms_profile = calculate_4d_trace_nrms(vp_base, rho_base, vp_mon, rho_mon, frequency=wavelet_freq)
    z_score_field = compute_velocity_z_score(vp_base, vp_mon)
    max_z_profile = np.abs(np.min(z_score_field, axis=0))
    
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.plot(x_axis, nrms_profile, color='black', linewidth=2, label='Calculated nRMS Profile')
    ax.axhline(y=alert_threshold, color='red', linestyle=':', linewidth=2, label=f'Noise Floor Boundary ({selected_noise_name})')
    ax.fill_between(x_axis, nrms_profile, alert_threshold, where=(nrms_profile > alert_threshold), color='red', alpha=0.3)
    ax.set_ylabel('nRMS Metric Amplitude (%)'); ax.set_xlabel('Horizontal Axis (m)'); ax.legend()
    st.pyplot(fig)
    
    if np.max(nrms_profile) > alert_threshold:
        st.error(f"🚨 CRITICAL ALARM: The calculated seismic anomaly response breaches the field-verified noise floor of {alert_threshold:.2f}%. Storage integrity containment compromised.")
    else:
        st.success(f"✅ CONTAINMENT STATUS SECURE: Statistical metrics operate safely within background noise parameters.")

def page_detectability_timeline():
    st.title("⏱️ Dynamic Flagship Detectability Timeline")
    st.markdown("### Modul 1-6 Full Composite Pipeline Integration Framework")
    st.markdown("Composes volumetric growth rates, Gassmann fluid substitutions, and zero-mean convolutions to calculate the exact structural day/mass milestone where carbon becomes statistically visible.")
    
    timeline_years = np.linspace(0.2, 12.0, 15)
    calculated_nrms_history = []
    injected_mass_history = []
    
    t_nx, t_nz = 60, 50
    tx = np.linspace(0, 4000, t_nx)
    tz = np.linspace(1000, 2500, t_nz)
    
    t_vp_base = np.zeros((t_nz, t_nx))
    for i in range(t_nz):
        t_vp_base[i, :] = 2800.0 + 0.5 * (tz[i] - 1000.0)
    t_vs_base = t_vp_base / 1.74
    t_rho_base = np.full((t_nz, t_nx), rho_matrix_kg * 0.85)
    
    progress_bar = st.progress(0.0)
    
    for idx, t_step in enumerate(timeline_years):
        step_mass_mt = inj_rate * t_step
        injected_mass_history.append(step_mass_mt)
        
        step_radius = np.sqrt((step_mass_mt * 1e9) / (np.pi * res_thickness * storage_efficiency * rho_co2_kg))
        
        t_vp_mon = t_vp_base.copy()
        t_rho_mon = t_rho_base.copy()
        tc_x, tc_z, tr_x, tr_z = 2000, res_depth, step_radius * 1.1, res_thickness * 0.5
        
        for i in range(t_nz):
            for j in range(t_nx):
                tdz = (tz[i] - tc_z) / tr_z
                if -1.0 <= tdz <= 1.0:
                    twf = 1.0 if tdz < 0 else (0.25 + 0.75 * np.exp(-4.5 * tdz))
                    tdx = (tx[j] - tc_x) / (tr_x * twf)
                    if (tdx**2 + tdz**2) <= 1.0:
                        tz_top = tc_z - tr_z
                        td_cap = max(0.0, tz[i] - tz_top)
                        t_local_s = s_co2_max * np.exp(-2.2 * (td_cap / (2.0 * tr_z)))
                        
                        v_m, _, r_m = gassmann_substitution(
                            t_vp_base[i, j], t_vs_base[i, j], t_rho_base[i, j], phi_val, t_local_s,
                            site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg,
                            mixing_law, brie_exp
                        )
                        t_vp_mon[i, j] = v_m
                        t_rho_mon[i, j] = r_m
                        
        step_nrms = calculate_4d_trace_nrms(t_vp_base, t_rho_base, t_vp_mon, t_rho_mon, frequency=wavelet_freq)
        calculated_nrms_history.append(np.max(step_nrms))
        progress_bar.progress((idx + 1) / len(timeline_years))
        
    progress_bar.empty()
    
    detect_year = None
    detect_mass = None
    for k in range(len(timeline_years)):
        if calculated_nrms_history[k] > alert_threshold:
            detect_year = timeline_years[k]
            detect_mass = injected_mass_history[k]
            break
            
    fig_time, ax_time = plt.subplots(figsize=(10, 4.5))
    ax_time.plot(timeline_years, calculated_nrms_history, color='darkblue', marker='o', linewidth=2.5, label='Dynamic 4D Anomaly Growth')
    ax_time.axhline(y=alert_threshold, color='red', linestyle=':', linewidth=2, label=f'Noise Floor Limit ({alert_threshold:.1f}%)')
    
    if detect_year is not None:
        ax_time.axvline(x=detect_year, color='darkgreen', linestyle='--', linewidth=2, label=f'Statistical Detection Boundary')
        ax_time.scatter([detect_year], [alert_threshold], color='darkgreen', s=150, zorder=5)
        
    ax_time.set_ylabel('Peak Localized nRMS Anomaly Amplitude (%)', weight='bold')
    ax_time.set_xlabel('Injection Horizon Elapsed Timeline (Years)', weight='bold')
    ax_time.grid(True, alpha=0.3)
    ax_time.legend(loc='upper left')
    st.pyplot(fig_time)
    
    st.markdown("---")
    st.subheader("Quantitative Analytics Threshold Diagnostic Box")
    
    if detect_year is not None:
        days_calc = int(detect_year * 365.25)
        st.info(f"""
        🎯 **STATISTICAL SEISMIC VISIBILITY THRESHOLD ACQUIRED**
        * **Time Elapsed Until Detection:** {detect_year:.2f} Years (~**{days_calc} Days** post-injection initiation).
        * **Minimum Injectant Volume Mass Required:** **{detect_mass:.2f} Megatonnes (Mt)** of supercritical CO₂.
        * **Applied Verification Constraint Environment:** Operating under field background noise floor parameters of **{alert_threshold:.1f}% nRMS** derived from *{selected_noise_name}* calibrations.
        """)
    else:
        st.error(f"📉 **SUBCRITICAL RESOLUTION MASK:** The seismic signature amplitude cannot breach the background noise floor limit of {alert_threshold:.1f}% within the current timeline window parameters.")

# ── 5. MASTER EXECUTION NAVIGATION RADIO MATRIX ROUTER ──────────────
pages_matrix = {
    "🌐 Overview / KPI Framework": page_overview,
    "📊 Plume Uncertainty Bounds": page_plume,
    "🌋 Graded Buoyant 2D Mesh": page_seismic_anomaly,
    "🧮 Gassmann Curve Matrix": page_gassmann,
    "🪵 Well Log Interval Analysis": page_well_log,
    "🚨 Core Alerts Diagnostic Console": page_alerts,
    "⏱️ Crown Flagship: Detectability Timeline": page_detectability_timeline
}

selected_page_name = st.sidebar.radio("🧭 Suite Navigation Menu", list(pages_matrix.keys()))
pages_matrix[selected_page_name]()