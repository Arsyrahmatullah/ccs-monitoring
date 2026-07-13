# src/ccs_monitoring/seismic/vp_anomaly.py
import os
import sys

# FORCE PATH INJECTION: Memaksa Python memprioritaskan folder 'src' paling atas
# Menghilangkan error 'ModuleNotFoundError' akibat cache virtual environment secara absolut
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from ccs_monitoring.Rock_physics.gassmann import gassmann_substitution

# ── 1. Internal Functional Core Components ───────────────────────
def create_ricker_wavelet(frequency=30, dt=0.002, duration=0.08):
    """Generates a standard symmetric Ricker Wavelet for seismic convolution."""
    t = np.arange(-duration/2, duration/2, dt)
    pi_f_t = np.pi * frequency * t
    return (1.0 - 2.0 * (pi_f_t ** 2)) * np.exp(-(pi_f_t ** 2))

def generate_seismic_trace(vp_profile, rho_profile, wavelet):
    """Transforms 1D subsurface rock properties profiles into a seismic amplitude trace."""
    ai = vp_profile * rho_profile
    rc = np.zeros_like(ai)
    rc[1:] = (ai[1:] - ai[:-1]) / (ai[1:] + ai[:-1])
    return np.convolve(rc, wavelet, mode='same')

def calculate_4d_seismic_nrms(vp_base, rho_base, vp_mon, rho_mon, frequency=30, dt=0.002):
    """Computes the 4D time-lapse seismic nRMS error profile using zero-mean synthetic traces."""
    nz, nx = vp_base.shape
    wavelet = create_ricker_wavelet(frequency, dt)
    nrms_profile = np.zeros(nx)
    
    for col in range(nx):
        trace_base = generate_seismic_trace(vp_base[:, col], rho_base[:, col], wavelet)
        trace_mon = generate_seismic_trace(vp_mon[:, col], rho_mon[:, col], wavelet)
        
        diff = trace_base - trace_mon
        rms_diff = np.sqrt(np.mean(diff ** 2))
        denom = 0.5 * (np.sqrt(np.mean(trace_base ** 2)) + np.sqrt(np.mean(trace_mon ** 2)))
        nrms_profile[col] = (rms_diff / denom) * 100 if denom > 1e-6 else 0.0
    return nrms_profile

# ── 2. Isolated Execution Control Block ────────────────────────────
if __name__ == '__main__':
    output_file = os.path.join(current_dir, 'vp_anomaly.png')

    nx, nz = 200, 150
    x, z = np.linspace(0, 4000, nx), np.linspace(1000, 2500, nz)
    X, Z = np.meshgrid(x, z)

    np.random.seed(42)
    spatial_noise = gaussian_filter(np.random.randn(nz, nx), sigma=(3, 12))
    spatial_noise /= np.std(spatial_noise)

    vp_baseline = np.zeros((nz, nx))
    rho_baseline = np.zeros((nz, nx))

    for i in range(nz):
        depth = z[i]
        if depth < 1400:
            vp_baseline[i, :] = 2600 + 0.45 * (depth - 1000); rho_baseline[i, :] = 2.20
        elif depth < 1800:
            vp_baseline[i, :] = 3100 + 0.55 * (depth - 1400); rho_baseline[i, :] = 2.35
        else:
            vp_baseline[i, :] = 3600 + 0.35 * (depth - 1800); rho_baseline[i, :] = 2.50

    vp_baseline *= (1.0 + 0.04 * spatial_noise)
    rho_baseline *= (1.0 + 0.02 * spatial_noise)
    vp_monitor, vs_monitor, rho_monitor = vp_baseline.copy(), (vp_baseline / 1.74), rho_baseline.copy()

    center_x, center_z, radius_x, radius_z = 2000, 1600, 750, 85
    phi, s_co2_inject, k_m, k_brine, k_co2, rho_b, rho_c, rho_mat = 0.13, 0.45, 45.0, 2.8, 0.08, 1000.0, 700.0, 2.71

    for i in range(nz):
        for j in range(nx):
            dz = (z[i] - center_z) / radius_z
            if -1.0 <= dz <= 1.0:
                dx = (x[j] - center_x) / (radius_x * (1.0 if dz < 0 else (0.25 + 0.75 * np.exp(-4.5 * dz))))
                if (dx**2 + dz**2) <= 1.0:
                    v_m, s_m, r_m = gassmann_substitution(vp_baseline[i, j], vs_monitor[i, j], rho_baseline[i, j], phi, s_co2_inject, k_m, k_brine, k_co2, rho_b, rho_c, rho_mat)
                    vp_monitor[i, j], vs_monitor[i, j], rho_monitor[i, j] = v_m, s_m, r_m

    nrms_seismic = calculate_4d_seismic_nrms(vp_baseline, rho_baseline, vp_monitor, rho_monitor)

    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    im1 = axes[0].pcolormesh(X, Z, vp_baseline, cmap='viridis', shading='auto')
    fig.colorbar(im1, ax=axes[0], label='Vp (m/s)')
    im2 = axes[1].pcolormesh(X, Z, vp_monitor, cmap='viridis', shading='auto')
    fig.colorbar(im2, ax=axes[1], label='Vp (m/s)')
    
    axes[2].plot(x, nrms_seismic, color='crimson', linewidth=2.5)
    axes[2].set_ylabel('Detector Response (%)')
    axes[2].set_ylim(0, np.max(nrms_seismic) * 1.2)
    
    for ax in axes[:2]: ax.invert_yaxis(); ax.set_ylabel('Depth (m)')
    axes[2].set_xlabel('Horizontal Reservoir Distance (m)')
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150)
    plt.show()
    print(f"[SUCCESS] Subsurface section compiled safely at: {output_file}")