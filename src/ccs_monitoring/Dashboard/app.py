# src/ccs_monitoring/Dashboard/app.py
import os
import sys

# FORCE PATH INJECTION: Mengunci folder 'src' agar import package ccs_monitoring aman
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import lasio

# EXACT CAPS LOCK IMPORTS: Sinkron 100% dengan nama folder di sidebar VS Code kamu
from ccs_monitoring.presets import RESERVOIR_PRESETS
from ccs_monitoring.Rock_physics.gassmann import gassmann_substitution
from ccs_monitoring.Anomaly.anomaly_detection import calculate_4d_trace_nrms, compute_velocity_z_score
try:
    from ccs_monitoring.Seismic.vp_anomaly import create_ricker_wavelet, generate_seismic_trace
except ModuleNotFoundError:
    from ccs_monitoring.seismic.vp_anomaly import create_ricker_wavelet, generate_seismic_trace

# Local Thermodynamic Helper to guarantee density calculation stability
def estimate_supercritical_co2_density(pressure_mpa, temperature_c):
    """Approximates supercritical CO2 density (kg/m3) dynamically."""
    rho = 750.0 + (pressure_mpa * 12.5) - (temperature_c * 4.2)
    return np.clip(rho, 400.0, 850.0)

# ── 1. GLOBAL SIDEBAR CONFIGURATION & DRIVERS ──────────────────
st.set_page_config(page_title="Advanced CCS Monitoring Suite", layout="wide")

st.sidebar.header("🧭 Global Site Selection")
selected_preset_name = st.sidebar.selectbox(
    "Choose Target Site Preset:", 
    list(RESERVOIR_PRESETS.keys()),
    help="Select a benchmark geological field framework to supply baseline physical parameters."
)

# Load selected configuration array from central preset library
site = RESERVOIR_PRESETS[selected_preset_name]
st.sidebar.info(f"📄 **Source Citation:**\n{site['citation']}")

st.sidebar.markdown("---")
st.sidebar.header("🛠️ Local Tuning Controls")

# Seed default sliders dynamically based on literature configuration guidelines
phi_val = st.sidebar.slider("Porosity override (phi)", 0.05, 0.45, float(site["phi"]), 0.01)
s_co2 = st.sidebar.slider("CO2 Fluid Saturation (S_CO2)", 0.0, 1.0, 0.45, 0.05)
mixing_law = st.sidebar.radio("Fluid Saturation Theory:", ["wood", "brie"], index=0)
brie_exp = st.sidebar.slider("Brie Patchy Exponent (e)", 1.0, 5.0, 3.0, 0.5) if mixing_law == "brie" else 3.0

st.sidebar.subheader("Subsurface Boundary In-situ Matrix")
res_depth = st.sidebar.slider("Target Injection Depth (m)", 1000, 2500, 1600, 50)
res_thickness = st.sidebar.slider("Gross Formation Thickness H (m)", 20, 150, 80, 5)
inj_rate = st.sidebar.slider("Mass Injection Rate (Mt/year)", 0.5, 3.0, 1.355, 0.05)
years = st.sidebar.slider("Time Horizon Tracker (Years)", 1.0, 15.0, 10.0, 0.5)

st.sidebar.subheader("Time-Lapse Seismic Wavelet")
wavelet_freq = st.sidebar.slider("Ricker Peak Frequency (Hz)", 15, 60, 30, 5)
alert_threshold = st.sidebar.slider("nRMS Anomaly Alert Limit (%)", 1.0, 20.0, 8.0, 0.5)

# Convert densities from g/cm³ preset records to strict SI kg/m³ for gassmann engine safety
rho_matrix_kg = site["rho_matrix"] * 1000.0
rho_brine_kg = site["rho_brine"] * 1000.0
rho_co2_kg = site["rho_co2"] * 1000.0

# ── 2. GLOBAL SHARED UNDERGROUND CALCULATIONS ─────────────────────────
total_mass_mt = inj_rate * years
p_surf, t_surf, g_acc, geo_grad = 0.1013, 25.0, 9.81, 3.5
p_res = p_surf + (rho_brine_kg * g_acc * res_depth) * 1e-6 # Hydrostatic MPa
t_res = t_surf + (geo_grad * (res_depth / 100.0))

# Volumetric propagation sizing driven by centrally loaded presets
storage_efficiency = phi_val * 0.75 * 0.75  # NetToGross * Swirr constant proxy bounds
current_radius = np.sqrt((total_mass_mt * 1e9) / (np.pi * res_thickness * storage_efficiency * rho_co2_kg))

# ── 3. GLOBAL REAL-TIME 2D MESH PIPELINE ──────────────────────────────
nx, nz = 140, 100
x_axis = np.linspace(0, 4000, nx)
z_axis = np.linspace(1000, 2500, nz)
X_grid, Z_grid = np.meshgrid(x_axis, z_axis)

np.random.seed(42)
spatial_noise = gaussian_filter(np.random.randn(nz, nx), sigma=(4, 10))
spatial_noise /= np.std(spatial_noise)

vp_base = np.zeros((nz, nx))
for i in range(nz):
    depth = z_axis[i]
    vp_base[i, :] = (2800.0 + 0.5 * (depth - 1000.0)) * (1.0 + 0.03 * spatial_noise[i, :])
    
vs_mon = vp_base / 1.74
rho_base = np.full((nz, nx), rho_matrix_kg * 0.85)

vp_mon = vp_base.copy()
rho_mon = rho_base.copy()
c_x, c_z, r_x, r_z = 2000, res_depth, current_radius * 1.1, res_thickness * 0.5

for i in range(nz):
    for j in range(nx):
        dz = (z_axis[i] - c_z) / r_z
        if -1.0 <= dz <= 1.0:
            width_factor = 1.0 if dz < 0 else (0.25 + 0.75 * np.exp(-4.5 * dz))
            dx = (x_axis[j] - c_x) / (r_x * width_factor)
            if (dx**2 + dz**2) <= 1.0:
                v_m, _, r_m = gassmann_substitution(
                    vp_base[i, j], vs_mon[i, j], rho_base[i, j], phi_val, s_co2,
                    site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg,
                    mixing_law, brie_exp
                )
                vp_mon[i, j] = v_m
                rho_mon[i, j] = r_m

# ── 4. MULTI-PAGE NAVIGATION ROUTER FUNCTIONS ──────────────────────────

def page_overview():
    st.title("🌐 Overview & Consolidated Site Framework KPIs")
    st.markdown(f"### Current Operation Model: **{selected_preset_name}**")
    st.caption(site["description"])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dynamic Net Sequestration", f"{total_mass_mt:.3f} Mt")
    col2.metric("In-situ Subsurface Pressure", f"{p_res:.2f} MPa")
    col3.metric("Mineral Frame Modulus (Km)", f"{site['k_m']:.1f} GPa")
    col4.metric("Calculated Plume Radius", f"{current_radius:.2f} m")
    
    st.markdown("---")
    st.markdown("### Calibrated Preset Values Currently Locked In:")
    st.json({
        "Mineral Matrix Modulus (k_m)": f"{site['k_m']} GPa",
        "Brine Modulus (k_brine)": f"{site['k_brine']} GPa",
        "CO2 Compressibility Modulus (k_co2)": f"{site['k_co2']} GPa",
        "Standard Matrix Density": f"{rho_matrix_kg} kg/m³",
        "Brine Density Profile": f"{rho_brine_kg} kg/m³",
        "CO2 Fluid Phase Density": f"{rho_co2_kg} kg/m³"
    })

def page_plume():
    st.title("📊 CO2 Plume Growth & Uncertainty Envelope")
    st.markdown("Dynamic propagation model mapped with sub-linear power-law footprint expansion.")
    
    t_axis = np.linspace(0, 15, 100)
    mass_axis = (inj_rate * 1e9) * t_axis
    
    eff_low = max(0.01, phi_val - 0.03) * 0.75 * 0.75
    eff_high = (phi_val + 0.03) * 0.75 * 0.75
    
    r_base = np.sqrt(mass_axis / (np.pi * res_thickness * storage_efficiency * rho_co2_kg))
    r_envelope_low = np.sqrt(mass_axis / (np.pi * res_thickness * eff_high * rho_co2_kg))
    r_envelope_high = np.sqrt(mass_axis / (np.pi * res_thickness * eff_low * rho_co2_kg))
    
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(t_axis, r_base, color='crimson', linewidth=2.5, label=f'Base Dynamic Model ({selected_preset_name})')
    ax.fill_between(t_axis, r_envelope_low, r_envelope_high, color='crimson', alpha=0.15, label='Porosity Matrix Variance Band (±3%)')
    ax.axvline(x=years, color='orange', linestyle='--', label='Target Evaluation Horizon')
    ax.scatter([years], [current_radius], color='black', zorder=5)
    
    ax.set_xlabel('Injection Horizon Duration (Years)')
    ax.set_ylabel('Lateral Radius Frontier (meters)')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

def page_seismic_anomaly():
    st.title("🌋 Stochastic 4D Vp Anomaly Grid")
    st.markdown("2D geological slice visualization tracking buoyancy-driven fluid substitution.")
    
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True)
    
    im1 = axes[0].pcolormesh(X_grid, Z_grid, vp_base, cmap='viridis', shading='auto')
    fig.colorbar(im1, ax=axes[0], label='Vp (m/s)')
    axes[0].set_title(f'Baseline Model Structural Vp ({selected_preset_name})')
    
    im2 = axes[1].pcolormesh(X_grid, Z_grid, vp_mon, cmap='viridis', shading='auto')
    fig.colorbar(im2, ax=axes[1], label='Vp (m/s)')
    axes[1].set_title('Monitor Post-Injection Mushroom Fluid Substitution Profile')
    
    for ax in axes: 
        ax.invert_yaxis()
        ax.set_ylabel('Subsurface Depth (m)')
    axes[1].set_xlabel('Horizontal Coordinates (m)')
    plt.tight_layout()
    st.pyplot(fig)

def page_gassmann():
    st.title("🧮 Gassmann Curve Solver")
    st.markdown("Simulating core elastic response boundaries inside porous matrices.")
    
    s_axis = np.linspace(0, 1.0, 50)
    vp_curve = []
    
    v_base_ref, vs_ref, rho_ref = 3200.0, 1850.0, rho_matrix_kg * 0.88
    for s in s_axis:
        v_m, _, _ = gassmann_substitution(
            v_base_ref, vs_ref, rho_ref, phi_val, s,
            site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg,
            mixing_law, brie_exp
        )
        vp_curve.append(v_m)
        
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(s_axis * 100.0, vp_curve, color='navy', linewidth=2.5, label=f'Mixing Law: {mixing_law.upper()}')
    ax.axvline(x=s_co2 * 100.0, color='orange', linestyle=':', label='Active Slider Saturation')
    ax.set_xlabel('CO2 Saturation Volume (%)')
    ax.set_ylabel('P-Wave Sonic Velocity Response (m/s)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)

def page_well_log():
    st.title("🪵 Well Section Log Analysis (LAS Core Integration)")
    st.markdown("Confining supercritical fluid substitution explicitly inside targeted petrophysical boundaries.")
    
    # ── NEW: ADVANCED LAS FILE UPLOADER ENGINE ──
    log_mode = st.radio("Select Data Log Source Matrix:", ["Use Demo Synthetic Sleipner Proxy Log", "Upload Custom Petrophysical .LAS File"])
    
    log_z, log_vp, log_phi, log_rho = None, None, None, None
    is_las_loaded = False
    
    if log_mode == "Upload Custom Petrophysical .LAS File":
        uploaded_file = st.file_uploader("Upload Reservoir Wireline ASCII Log (.las)", type=["las"])
        if uploaded_file is not None:
            try:
                # Read string buffer natively from streamlit binary memory bytes
                string_data = uploaded_file.read().decode("utf-8", errors="ignore")
                las = lasio.read(string_data)
                
                # Dynamic curve key mapping to bypass case-sensitivity constraints
                curves = {c.mnemonic.upper(): c.data for c in las.curves}
                
                # Extract Depth curve proxy
                log_z = las.depth_m if hasattr(las, 'depth_m') else curves.get('DEPTH') or curves.get('DEPT')
                
                # Extract elastic sonic velocity and density property curves
                log_vp = curves.get('VP') or (304800.0 / curves.get('DT') if curves.get('DT') is not None else None)
                log_phi = curves.get('NPHI') or curves.get('PHIE') or curves.get('POR')
                log_rho = curves.get('RHOB') or curves.get('DEN')
                
                if log_z is not None and log_vp is not None and log_phi is not None:
                    # Sanitize any data gaps/NaN constraints
                    valid_mask = ~np.isnan(log_z) & ~np.isnan(log_vp) & ~np.isnan(log_phi)
                    log_z, log_vp, log_phi = log_z[valid_mask], log_vp[valid_mask], log_phi[valid_mask]
                    log_rho = log_rho[valid_mask] if log_rho is not None else np.full(len(log_z), rho_matrix_kg * 0.86)
                    
                    # Core unit transformation checks (Convert density to SI if logged in g/cm3)
                    if np.max(log_rho) < 10.0: log_rho *= 1000.0
                    
                    is_las_loaded = True
                    st.success(f"📊 Successfully loaded custom log: parsed {len(log_z)} active log depth metrics.")
                else:
                    st.error("❌ Key curves missing: The uploaded LAS file must contain at least DEPTH, VP (or DT), and Porosity (NPHI/PHIE).")
            except Exception as e:
                st.error(f"❌ Parser Error: Failed to interpret file format architecture. Reason: {str(e)}")
                
    if not is_las_loaded:
        if log_mode == "Upload Custom Petrophysical .LAS File":
            st.info("💡 Awaiting file submission... Displaying standard fallback Sleipner proxy log configuration below.")
        
        # Solid dynamic fallback benchmark log configuration matrix
        log_z = np.linspace(800, 1100, 250)
        log_phi = np.clip(phi_val + 0.15 + 0.015 * np.random.randn(250), 0.10, 0.42)
        log_rho = 2650.0 * (1.0 - log_phi) + 1000.0 * log_phi
        log_vp = 3800.0 - 2600.0 * log_phi + 40.0 * np.random.randn(250)

    # ── COMPUTE INJECTION INTERVAL BOUNDS ──
    st.markdown("#### Injection Perforation Zone Configuration")
    min_z, max_z = float(np.min(log_z)), float(np.max(log_z))
    top_res = st.slider("Top Perforation Boundary (m)", min_z, max_z, min_z + (max_z - min_z)*0.4)
    base_res = st.slider("Base Perforation Boundary (m)", min_z, max_z, top_res + 60.0)
    
    log_vs = log_vp / 1.85 # Constant shear estimation fallback matrix
    log_vp_mon = log_vp.copy()
    
    for idx in range(len(log_z)):
        current_s = s_co2 if top_res <= log_z[idx] <= base_res else 0.0
        v_m, _, _ = gassmann_substitution(
            log_vp[idx], log_vs[idx], log_rho[idx], log_phi[idx], current_s,
            site["k_m"], site["k_brine"], site["k_co2"], rho_brine_kg, rho_co2_kg, rho_matrix_kg,
            mixing_law, brie_exp
        )
        log_vp_mon[idx] = v_m
        
    # Render Diagnostics Graphics
    fig, axes = plt.subplots(1, 3, figsize=(11, 6), sharey=True)
    
    axes[0].plot(log_phi, log_z, color='darkgreen', alpha=0.8, linewidth=1.2)
    axes[0].axhspan(top_res, base_res, color='yellow', alpha=0.15, label='Perforated Zone')
    axes[0].set_xlabel('Measured Porosity (v/v)', weight='bold')
    axes[0].set_title('Porosity Profile', weight='bold')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(log_vp, log_z, color='gray', label='Baseline (Brine)', alpha=0.7)
    axes[1].plot(log_vp_mon, log_z, color='crimson', label='Monitor (CO2)', linewidth=1.5)
    axes[1].axhspan(top_res, base_res, color='yellow', alpha=0.15)
    axes[1].set_xlabel('Velocity Vp (m/s)', weight='bold')
    axes[1].set_title('Fluid Substitution Log', weight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc='lower left')
    
    log_delta_vp = ((log_vp_mon - log_vp) / log_vp) * 100.0
    axes[2].plot(log_delta_vp, log_z, color='crimson', linewidth=1.5)
    axes[2].axhspan(top_res, base_res, color='yellow', alpha=0.15)
    axes[2].axvline(x=0.0, color='black', linestyle='--', alpha=0.5)
    axes[2].set_xlabel('Time-Lapse ΔVp Anomaly (%)', weight='bold')
    axes[2].set_title('4D Sonic Delta Anomaly', weight='bold')
    axes[2].grid(True, alpha=0.3)
    
    axes[0].invert_yaxis()
    axes[0].set_ylabel('Measured Structural Depth (m)', fontsize=11, weight='bold')
    plt.tight_layout()
    st.pyplot(fig)

def page_alerts():
    st.title("🚨 Automated Anomaly Alerts Console")
    st.markdown("### Modul 6 Analytics: Combined Time-Lapse Trace Analytics Framework")
    
    nrms_profile = calculate_4d_trace_nrms(vp_base, rho_base, vp_mon, rho_mon, frequency=wavelet_freq)
    z_score_field = compute_velocity_z_score(vp_base, vp_mon)
    max_z_profile = np.abs(np.min(z_score_field, axis=0))
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("4D Seismic nRMS Profile")
        fig_nrms, ax_nrms = plt.subplots(figsize=(6, 4))
        ax_nrms.plot(x_axis, nrms_profile, color='black', linewidth=2, label='Seismic nRMS')
        ax_nrms.axhline(y=alert_threshold, color='red', linestyle=':', linewidth=2, label='Safety Limit')
        ax_nrms.fill_between(x_axis, nrms_profile, alert_threshold, where=(nrms_profile > alert_threshold), color='red', alpha=0.3)
        ax_nrms.set_ylabel('Detector Response (%)')
        ax_nrms.set_xlabel('Horizontal Coordinate (m)')
        ax_nrms.set_ylim(0, max(20.0, np.max(nrms_profile) * 1.2))
        ax_nrms.grid(True, alpha=0.3)
        ax_nrms.legend()
        st.pyplot(fig_nrms)
        
    with col_right:
        st.subheader("Statistical Variance Deviation")
        fig_z, ax_z = plt.subplots(figsize=(6, 4))
        ax_z.plot(x_axis, max_z_profile, color='darkblue', linewidth=2, label='Local Sigma Profile')
        ax_z.axhline(y=3.0, color='purple', linestyle='--', label='Confidence Bound (3σ)')
        ax_z.set_ylabel('Absolute Z-Score (|Z|)')
        ax_z.set_xlabel('Horizontal Coordinate (m)')
        ax_z.grid(True, alpha=0.3)
        ax_z.legend()
        st.pyplot(fig_z)
        
    max_nrms = np.max(nrms_profile)
    max_z = np.max(max_z_profile)
    
    st.markdown("---")
    st.subheader("Subsurface Diagnostics Verification Matrix")
    
    if max_nrms > alert_threshold or max_z > 3.0:
        st.error(f"""
        🚨 **CRITICAL ALARM: CAPROCK RECOVERY WARNING** * Peak Localized nRMS Amplitude: **{max_nrms:.2f}%** (Safety Limit: {alert_threshold:.1f}%).  
        * Maximum Local Variance Deviation: **{max_z:.2f}σ** (Statistical Bound: 3.0σ).  
        
        **Interpretation:** High-probability trace anomaly detected. Localized variance deviation confirms fluid propagation bypassing primary reservoir seals. Action required.
        """)
    else:
        st.success(f"""
        ✅ **SUBSURFACE STORAGE INTEGRITY SYSTEM SECURE** * Peak Localized nRMS Amplitude: **{max_nrms:.2f}%** (Operating safely below the threshold).  
        * Maximum Local Variance Deviation: **{max_z:.2f}σ** (Normal geological background noise signatures).  
        
        **Interpretation:** Fluid displacement confined within expected structural frameworks under the caprock matrix.
        """)

# ── 5. ROUTING ROUTER MENU SELECTION MANAGEMENT ───────────────────────
pages_matrix = {
    "🌐 Overview / KPI Matrix": page_overview,
    "📊 Plume Growth Footprint": page_plume,
    "🌋 4D Vp Anomaly Grid": page_seismic_anomaly,
    "🧮 Gassmann Curve Solver": page_gassmann,
    "🪵 Well Section Log Analysis": page_well_log,
    "🚨 Anomaly Alerts Console": page_alerts
}

selected_page_name = st.sidebar.radio("🧭 Execution Navigation Menu", list(pages_matrix.keys()))
pages_matrix[selected_page_name]()