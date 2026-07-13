# src/ccs_monitoring/Anomaly/anomaly_detection.py
import numpy as np

try:
    from ccs_monitoring.Seismic.vp_anomaly import create_ricker_wavelet, generate_seismic_trace
except ModuleNotFoundError:
    from ccs_monitoring.seismic.vp_anomaly import create_ricker_wavelet, generate_seismic_trace

def calculate_4d_trace_nrms(vp_base, rho_base, vp_mon, rho_mon, frequency=30, dt=0.002):
    """Computes the 4D time-lapse seismic nRMS profile using zero-mean synthetic amplitude traces."""
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

def compute_velocity_z_score(vp_base, vp_mon):
    """Computes localized statistical Z-Score from the velocity drop metrics."""
    delta_vp = ((vp_mon - vp_base) / vp_base) * 100.0
    mean_val = np.mean(delta_vp)
    std_val = np.std(delta_vp)
    if std_val < 1e-4:
        return np.zeros_like(delta_vp)
    return (delta_vp - mean_val) / std_val