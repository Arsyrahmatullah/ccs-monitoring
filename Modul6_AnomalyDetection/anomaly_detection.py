import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

# ── Simulasi time-series Vp monitoring ────────────────────
# 6 sensor di lokasi berbeda, monitoring selama 10 tahun
np.random.seed(42)

n_years   = 10
n_sensors = 6
years     = np.linspace(0, n_years, 120)  # monthly sampling

# Posisi sensor (x, z) dalam meter
sensor_positions = [
    (2500, 1500),  # S1 — di atas plume (zona injeksi)
    (2500, 1300),  # S2 — lebih dangkal dari plume
    (1500, 1500),  # S3 — lateral kiri
    (3500, 1500),  # S4 — lateral kanan
    (2500, 1800),  # S5 — di bawah plume
    (500,  1500),  # S6 — jauh dari plume (reference)
]

sensor_names = ['S1 (above plume)', 'S2 (shallow)', 'S3 (left)',
                'S4 (right)', 'S5 (below)', 'S6 (reference)']

# Vp baseline per sensor (m/s)
vp_baseline = [2800, 2600, 2820, 2810, 2900, 2850]

# Simulasi perubahan Vp — S1 dan S2 kena efek CO₂
def simulate_vp(baseline, max_drop, years, noise_std=15):
    """Simulasi Vp turun akibat CO₂, dengan noise"""
    # CO₂ mulai injeksi tahun ke-1, efek terasa bertahap
    signal = baseline - max_drop * (1 - np.exp(-0.3 * np.maximum(years - 1, 0)))
    noise  = np.random.normal(0, noise_std, len(years))
    return signal + noise

vp_drop = [280, 180, 40, 35, 20, 5]  # penurunan Vp maksimum per sensor (m/s)
vp_series = [simulate_vp(vp_baseline[i], vp_drop[i], years)
             for i in range(n_sensors)]

# ── Anomaly Detection ──────────────────────────────────────
def detect_anomaly(vp, years, baseline_period=1.0, threshold_sigma=2.0):
    """
    Deteksi anomali berdasarkan z-score dari periode baseline
    baseline_period: tahun pertama dianggap baseline
    threshold_sigma: ambang batas dalam satuan standar deviasi
    """
    baseline_mask = years <= baseline_period
    baseline_mean = vp[baseline_mask].mean()
    baseline_std  = vp[baseline_mask].std()

    z_scores  = (vp - baseline_mean) / baseline_std
    anomalies = np.abs(z_scores) > threshold_sigma

    return z_scores, anomalies, baseline_mean, baseline_std

# Hitung anomali untuk setiap sensor
threshold = 2.0
results = []
for i in range(n_sensors):
    z, anom, bmean, bstd = detect_anomaly(vp_series[i], years, threshold_sigma=threshold)
    results.append({'z': z, 'anomaly': anom, 'baseline_mean': bmean, 'baseline_std': bstd})

# ── Plot ───────────────────────────────────────────────────
fig, axes = plt.subplots(3, 2, figsize=(14, 12))
axes = axes.flatten()

colors = ['crimson', 'tomato', 'steelblue', 'royalblue', 'seagreen', 'gray']

for i in range(n_sensors):
    ax  = axes[i]
    vp  = vp_series[i]
    res = results[i]

    # Plot Vp time series
    ax.plot(years, vp, color=colors[i], linewidth=1.2, alpha=0.8)

    # Highlight anomali
    anom_years = years[res['anomaly']]
    anom_vp    = vp[res['anomaly']]
    ax.scatter(anom_years, anom_vp, color='red', zorder=5, s=20, label='Anomaly detected')

    # Garis baseline mean ± threshold
    ax.axhline(res['baseline_mean'], color='k', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.axhline(res['baseline_mean'] - threshold * res['baseline_std'],
               color='red', linestyle=':', linewidth=1, alpha=0.7, label=f'Threshold (±{threshold}σ)')
    ax.axhline(res['baseline_mean'] + threshold * res['baseline_std'],
               color='red', linestyle=':', linewidth=1, alpha=0.7)

    # Shading zona anomali
    ax.fill_between(years, vp,
                    res['baseline_mean'] - threshold * res['baseline_std'],
                    where=res['anomaly'], color='red', alpha=0.15)

    # Waktu pertama anomali
    if res['anomaly'].any():
        first_anom = years[res['anomaly']][0]
        ax.axvline(first_anom, color='red', linestyle='--', linewidth=1, alpha=0.6)
        ax.text(first_anom + 0.1, vp.max(), f'Alert @ {first_anom:.1f} yr',
                fontsize=8, color='red')

    n_anom = res['anomaly'].sum()
    ax.set_title(f'{sensor_names[i]}\n({n_anom} anomalous points)', fontsize=10)
    ax.set_xlabel('Time (years)')
    ax.set_ylabel('Vp (m/s)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

fig.suptitle('CO₂ Leakage Anomaly Detection — Automated Vp Monitoring\n'
             f'Z-score method | Threshold = ±{threshold}σ from baseline',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('anomaly_detection.png', dpi=150)
# plt.show()
print("Plot tersimpan ✓")

# ── Alert Summary ──────────────────────────────────────────
print("\n" + "="*50)
print("ANOMALY DETECTION SUMMARY")
print("="*50)
for i in range(n_sensors):
    res = results[i]
    n_anom = res['anomaly'].sum()
    if n_anom > 0:
        first = years[res['anomaly']][0]
        status = "⚠️  ALERT"
    else:
        status = "✅ NORMAL"
    print(f"{status} | {sensor_names[i]:25} | {n_anom:3d} anomalies | first: {first:.1f} yr" 
          if n_anom > 0 else f"{status} | {sensor_names[i]:25} | no anomalies")