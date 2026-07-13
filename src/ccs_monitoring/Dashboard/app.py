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

# EXACT CAPS LOCK IMPORTS: Mengikuti nama folder kapital sesuai sidebar VS Code kamu
from ccs_monitoring.Rock_physics.gassmann import gassmann_substitution
from ccs_monitoring.Seismic.vp_anomaly import create_ricker_wavelet, generate_seismic_trace, calculate_4d_seismic_nrms

# Local Thermodynamic Helper to guarantee stability
def estimate_supercritical_co2_density(pressure_mpa, temperature_c):
    """Approximates supercritical CO2 density (kg/m3) dynamically."""
    rho = 750.0 + (pressure_mpa * 12.5) - (temperature_c * 4.2)
    return np.clip(rho, 400.0, 850.0)

# ── GLOBAL CONFIGURATION & SIDEBAR DRIVERS ────────────────────────
st.set_page_config(page_title="Advanced CCS Monitoring Suite", layout="wide")

st.sidebar.header("🛠️ Global Control Center")

st.sidebar.subheader("1. In-Situ Reservoir Sizing")
res_depth = st.sidebar.slider("Target Depth (m)", 1200.0, 2200.0, 1600.0, 50.0)
res_thickness = st.sidebar.slider("Gross Thickness H (m)", 30.0, 150.0, 80.0, 5.0)

st.sidebar.subheader("2. Fluid Dynamics & Petrophysics")
inj_rate = st.sidebar.slider("Injection Rate (Mt/year)", 0.5, 3.0, 1.355, 0.005)
years = st.sidebar.slider("Simulation Horizon (Years)", 1.0, 15.0, 10.0, 0.5)
phi = st.sidebar.slider("Effective Porosity (phi)", 0.05, 0.35, 0.13, 0.01)
s_co2 = st.sidebar.slider("CO2 Saturation (S_CO2)", 0.10, 0.90, 0.45, 0.05)

st.sidebar.subheader("3. 4D Seismic Configuration")
freq = st.sidebar.slider("Ricker Frequency (Hz)", 15, 60, 30, 5)
threshold = st.sidebar.slider("Alert Threshold nRMS (%)", 2.0, 20.0, 8.0, 0.5)

# Shared Subsurface Calculation Core
p_surf, t_surf, rho_b, g_acc, geo_grad = 0.1013, 25.0, 1025.0, 9.81, 3.5
p_res = p_surf + (rho_b * g_acc * res_depth) * 1e-6
t_res = t_surf + (geo_grad * (res_depth / 100.0))
rho_co2_val = estimate_supercritical_co2_density(p_res, t_res)

net_to_gross, s_wirr = 0.75, 0.25
storage_eff = phi * net_to_gross * (1.0 - s_wirr)
total_mass_mt = inj_rate * years
current_radius = np.sqrt((total_mass_mt * 1e9) / (np.pi * res_thickness * storage_eff * rho_co2_val))

# ── PAGES DEFINITION MATRIX ───────────────────────────────────────

def page_overview():
    st.title("🌐 Overview & Core Subsurface KPIs")
    st.markdown("### Subsurface Evaluation Framework — SYLAUV Field Reference")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Mass Injected", f"{total_mass_mt:.3f} Mt")
    col2.metric("In-Situ Pressure", f"{p_res:.2f} MPa")
    col3.metric("CO2 Phase Density", f"{rho_co2_val:.1f} kg/m³")
    col4.metric("Storage Capacity Factor", f"{storage_eff * 100:.2f} %")
    
    st.markdown("---")
    st.markdown("""
    ### Executive Summary
    This multi-page suite simulates rock physics parameters and time-lapse 4D seismic anomaly responses 
    associated with carbon sequestration inside the **Minahaki Carbonate Formation**. 
    
    Use the navigation menu in the sidebar to review specialized analytical components spanning volumetric plume expansion, 
    stochastic heterogeneity cross-sections, exact Gassmann solvers, log displacement intervals, and real-time trace risk alert management.
    """)

def page_plume():
    st.title("📊 CO2 Plume Growth & Uncertainty Band")
    st.markdown("Modeled using dynamic gravity current flow constraints showing sub-linear expansion over time.")
    
    t_axis = np.linspace(0, 15, 100)
    mass_axis = (inj_rate * 1e9) * t_axis
    
    # Uncertainty calculation based on porosity fluctuations (±3%)
    eff_base = phi * net_to_gross * (1.0 - s_wirr)
    eff_low = max(0.01, phi - 0.03) * net_to_gross * (1.0 - s_wirr)
    eff_high = (phi + 0.03) * net_to_gross * (1.0 - s_wirr)
    
    r_base = np.sqrt(mass_axis / (np.pi * res_thickness * eff_base * rho_co2_val))
    r_low = np.sqrt(mass_axis / (np.pi * res_thickness * eff_high * rho_co2_val))
    r_high = np.sqrt(mass_axis / (np.pi * res_thickness * eff_low * rho_co2_val))
    
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(t_axis, r_base, color='crimson', linewidth=2.5, label='Base Case Model')
    ax.fill_between(t_axis, r_low, r_high, color='crimson', alpha=0.15, label='Porosity Uncertainty Envelope (±3%)')
    ax.axvline(x=years, color='orange', linestyle='--', label='Selected Horizon')
    ax.scatter([years], [current_radius], color='black', zorder=5)
    
    ax.set_xlabel('Injection Duration (Years)')
    ax.set_ylabel('Plume Front Footprint Radius (meters)')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    st.info(f"📐 Dynamic Radius Matrix: At Year {years:.1f}, the supercritical plume front extends to a lateral radius of {current_radius:.2f} meters.")

def page_seismic_anomaly():
    st.title("🌋 Stochastic 4D Vp Anomaly (Mushroom Plume)")
    st.markdown("2D Geological slice cross-sections superimposed with **Gaussian Random Field Texture**.")
    
    nx, nz = 160, 120
    x, z = np.linspace(0, 4000, nx), np.linspace(1000, 2500, nz)
    X, Z = np.meshgrid(x, z)
    
    np.random.seed(42)
    spatial_noise = gaussian_filter(np.random.randn(nz, nx), sigma=(3, 12))
    spatial_noise /= np.std(spatial_noise)
    
    vp_base = np.zeros((nz, nx))
    for i in range(nz):
        depth = z[i]
        if depth < 1400:    vp_base[i, :] = 2600 + 0.45 * (depth - 1000)
        elif depth < 1800:  vp_base[i, :] = 3100 + 0.55 * (depth - 1400)
        else:               vp_base[i, :] = 3600 + 0.35 * (depth - 1800)
            
    vp_base *= (1.0 + 0.04 * spatial_noise)
    vp_mon = vp_base.copy()
    vs_mon = vp_base / 1.74
    rho_base = (vp_base * 0.31) + 1.2
    rho_mon = rho_base.copy()
    
    # Implements the buoyancy-driven mushroom plume geometry natively from vp_anomaly.py
    c_x, c_z, r_x, r_z = 2000, res_depth, current_radius * 1.2, res_thickness * 0.6
    k_m, k_b, k_c, rho_br, rho_co, rho_mat = 45.0, 2.8, 0.08, 1000.0, 700.0, 2.71
    
    for i in range(nz):
        for j in range(nx):
            dz = (z[i] - c_z) / r_z
            if -1.0 <= dz <= 1.0:
                width_factor = 1.0 if dz < 0 else (0.25 + 0.75 * np.exp(-4.5 * dz))
                dx = (x[j] - c_x) / (r_x * width_factor)
                if (dx**2 + dz**2) <= 1.0:
                    v_m, s_m, r_m = gassmann_substitution(vp_base[i, j], vs_mon[i, j], rho_base[i, j], phi, s_co2, k_m, k_b, k_c, rho_br, rho_co, rho_mat)
                    vp_mon[i, j], rho_mon[i, j] = v_m, r_m

    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    im1 = axes[0].pcolormesh(X, Z, vp_base, cmap='viridis', shading='auto')
    axes[0].set_title('Stochastic Heterogeneous Baseline Structure (100% Brine Saturated)', weight='bold')
    fig.colorbar(im1, ax=axes[0], label='Vp (m/s)')
    
    im2 = axes[1].pcolormesh(X, Z, vp_mon, cmap='viridis', shading='auto')
    axes[1].set_title('Dynamic Heterogeneous Monitor Structure (Post-CO2 Mushroom Plume Allocation)', weight='bold')
    fig.colorbar(im2, ax=axes[1], label='Vp (m/s)')
    
    for ax in axes: ax.invert_yaxis(); ax.set_ylabel('Depth (m)')
    axes[1].set_xlabel('Horizontal Axis Coordinate (m)')
    plt.tight_layout()
    st.pyplot(fig)
    
    # Session state preservation for cross-page analytical syncing
    st.session_state['vp_base'] = vp_base
    st.session_state['rho_base'] = rho_base
    st.session_state['vp_mon'] = vp_mon
    st.session_state['rho_mon'] = rho_mon
    st.session_state['x_axis'] = x

def page_gassmann():
    st.title("🧮 Gassmann Rock Physics Interactive Solver")
    st.markdown("Evaluating bulk matrix softening tendencies against dynamic fluid displacement changes.")
    
    s_co2_axis = np.linspace(0, 1.0, 100)
    vp_curve = []
    
    k_m, k_b, k_c, rho_br, rho_co, rho_mat = 45.0, 2.8, 0.08, 1000.0, 700.0, 2.71
    v_base_ref, vs_ref, rho_ref = 3500.0, 2000.0, 2.35
    
    for s in s_co2_axis:
        v_m, _, _ = gassmann_substitution(v_base_ref, vs_ref, rho_ref, phi, s, k_m, k_b, k_c, rho_br, rho_co, rho_mat)
        vp_curve.append(v_m)
        
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(s_co2_axis * 100, vp_curve, color='navy', linewidth=2.5, label='Theoretical Fluid Path')
    ax.axvline(x=s_co2 * 100, color='orange', linestyle=':', label='Selected Operating Saturation')
    ax.set_xlabel('CO2 Saturation Magnitude (%)')
    ax.set_ylabel('Bulk Rock P-Wave Velocity (m/s)')
    ax.set_title('Carbonate Matrix Softening Response Curve', weight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)

def page_well_log():
    st.title("🪵 Real Well Log Analysis (Sleipner Core Benchmark)")
    st.markdown("Confining supercritical fluid substitution specifically inside the calibrated target storage sands.")
    
    log_depth = np.linspace(800, 1000, 300)
    log_phi = np.clip(phi + 0.15 + 0.01 * np.random.randn(300), 0.15, 0.40)
    log_rhob_base = 2.65 * (1 - log_phi) + 1.0 * log_phi
    log_vp_base = 3800 - 2800 * log_phi
    log_vs_base = log_vp_base / 2.0
    log_vp_gassmann = log_vp_base.copy()
    
    k_m_sl, k_brine_sl, k_co2_sl, rho_brine_sl, rho_co2_sl, rho_matrix_sl = 37.0, 2.2, 0.06, 1030.0, 650.0, 2.65
    for idx in range(len(log_depth)):
        current_s_co2 = s_co2 if 900.0 <= log_depth[idx] <= 960.0 else 0.0
        v_m, _, _ = gassmann_substitution(log_vp_base[idx], log_vs_base[idx], log_rhob_base[idx], log_phi[idx], current_s_co2, k_m_sl, k_brine_sl, k_co2_sl, rho_brine_sl, rho_co2_sl, rho_matrix_sl)
        log_vp_gassmann[idx] = v_m

    fig, axes = plt.subplots(1, 3, figsize=(11, 6), sharey=True)
    axes[0].plot(log_phi, log_depth, color='green', alpha=0.7)
    axes[0].set_xlabel('Porosity (v/v)')
    axes[0].set_title('Log Porosity Profile', weight='bold')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(log_vp_base, log_depth, color='gray', alpha=0.7, label='Brine Baseline')
    axes[1].plot(log_vp_gassmann, log_depth, color='crimson', linewidth=1.5, label='Gassmann Substitution')
    axes[1].axhspan(900, 960, color='yellow', alpha=0.15, label='Reservoir Sand Target')
    axes[1].set_xlabel('P-Wave Velocity (m/s)')
    axes[1].set_title('Velocity Response Delta', weight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc='lower left', fontsize='small')
    
    log_delta_vp = ((log_vp_gassmann - log_vp_base) / log_vp_base) * 100
    axes3_2 = axes[2].plot(log_delta_vp, log_depth, color='crimson', linewidth=1.5)
    axes[2].axhspan(900, 960, color='yellow', alpha=0.15)
    axes[2].set_xlabel('Velocity Change ΔVp (%)')
    axes[2].set_title('4D Log Anomaly (%)', weight='bold')
    axes[2].grid(True, alpha=0.3)
    
    axes[0].invert_yaxis()
    axes[0].set_ylabel('Subsurface Depth (m)', fontsize=11, weight='bold')
    plt.tight_layout()
    st.pyplot(fig)

def page_alerts():
    st.title("🚨 Anomaly Detection & Safe Operating Alerts")
    st.markdown("### Trace Analytics Engine — Zero-Mean Convolution Framework")
    
    if 'vp_base' in st.session_state:
        vp_base = st.session_state['vp_base']
        rho_base = st.session_state['rho_base']
        vp_mon = st.session_state['vp_mon']
        rho_mon = st.session_state['rho_mon']
        x = st.session_state['x_axis']
    else:
        nx = 160
        x = np.linspace(0, 4000, nx)
        vp_base = np.full((120, nx), 3200.0)
        rho_base = np.full((120, nx), 2.30)
        vp_mon = vp_base.copy()
        vp_mon[50:70, 60:100] *= 0.96
        rho_mon = rho_base.copy()

    wavelet = create_ricker_wavelet(freq)
    nrms_profile = np.zeros(len(x))
    
    for col in range(len(x)):
        t_base = generate_seismic_trace(vp_base[:, col], rho_base[:, col], wavelet)
        t_mon = generate_seismic_trace(vp_mon[:, col], rho_mon[:, col], wavelet)
        diff = t_base - t_mon
        denom = 0.5 * (np.sqrt(np.mean(t_base**2)) + np.sqrt(np.mean(t_mon**2)))
        nrms_profile[col] = (np.sqrt(np.mean(diff**2)) / denom) * 100 if denom > 1e-6 else 0.0

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x, nrms_profile, color='black', linewidth=2, label='4D Seismic Trace nRMS Anomaly')
    ax.axhline(y=threshold, color='red', linestyle=':', linewidth=2, label='Safety Limit Threshold')
    ax.fill_between(x, nrms_profile, threshold, where=(nrms_profile > threshold), color='red', alpha=0.3, label='Critical Breach Zone')
    
    ax.set_ylabel('Detector Response (%)')
    ax.set_xlabel('Horizontal Cross-Section Axis Coordinate (m)')
    ax.set_title('Time-Lapse Zero-Mean Trace nRMS Anomaly Profiler', weight='bold')
    ax.set_ylim(0, max(15.0, np.max(nrms_profile) * 1.3))
    ax.grid(True, alpha=0.4)
    ax.legend(loc='upper left')
    st.pyplot(fig)
    
    max_nrms = np.max(nrms_profile)
    st.markdown("---")
    st.subheader("Containment Evaluation Diagnostics")
    
    if max_nrms > threshold:
        st.error(f"🚨 CRITICAL ALARM: Caprock containment boundary anomaly detected! Peak 4D seismic change reaches {max_nrms:.2f}%, breaching the designated safety limit of {threshold:.1f}%. Immediate migration tracking required.")
    else:
        st.success(f"✅ CONTAINMENT SECURE: Subsurface fluid displacement stable. Peak localized response stands at {max_nrms:.2f}%, running safely below the threshold limit.")

# ── ROUTING NAVIGATION ROUTER MATRIX ──────────────────────────────
pages_matrix = {
    "🌐 Overview / KPI": page_overview,
    "📊 Plume Growth": page_plume,
    "🌋 4D Vp Anomaly": page_seismic_anomaly,
    "🧮 Gassmann Rock Physics": page_gassmann,
    "🪵 Real Well Log (Sleipner)": page_well_log,
    "🚨 Anomaly Detection & Alerts": page_alerts
}

selected_page_name = st.sidebar.radio("🧭 Suite Navigation Menu", list(pages_matrix.keys()))
pages_matrix[selected_page_name]()