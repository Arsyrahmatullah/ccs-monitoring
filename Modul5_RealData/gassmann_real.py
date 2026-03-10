import numpy as np
import matplotlib.pyplot as plt
import lasio
import warnings
warnings.filterwarnings('ignore')

# ── Load Well Log ──────────────────────────────────────────
# Ganti path sesuai lokasi file kamu
las = lasio.read(r"C:\Users\Arsy Nuur\ccs-monitoring\ccs-monitoring\well_data\data\Wells_released_2011\Well 159_13\159-13 Logs.las")

print("Curves available:")
for curve in las.curves:
    print(f"  {curve.mnemonic:10} | {curve.unit:15} | {curve.descr}")

# ── Ambil data ─────────────────────────────────────────────
depth = las['DEPTH']
DT    = las['DT']      # sonic log (us/ft)
RHOB  = las['RHOB']    # bulk density (g/cm³)
NPHI  = las['NPHI']    # neutron porosity
SW    = las['SW']      # water saturation

# ── Clean data ─────────────────────────────────────────────
null = -999.25
mask = (DT > 0) & (DT != null) & \
       (RHOB > 0) & (RHOB != null) & \
       (NPHI > 0) & (NPHI != null)

depth = depth[mask]
DT    = DT[mask]
RHOB  = RHOB[mask]
NPHI  = NPHI[mask]
SW    = SW[mask]

# ── Konversi DT → Vp ───────────────────────────────────────
Vp_baseline = 304800 / DT  # konversi us/ft → m/s

# ── Gassmann Fluid Substitution ────────────────────────────
def gassmann_substitution(Vp, RHOB, phi, Sw_ini, Sw_fin,
                           K_mineral=36.0, K_brine=2.8, K_co2=0.08,
                           rho_brine=1.05, rho_co2=0.70):
    """
    Gassmann fluid substitution dari brine → CO₂
    Input Vp dalam m/s, RHOB dalam g/cm³
    """
    # Modulus saturasi awal
    rho = RHOB * 1000  # ke kg/m³
    M   = rho * Vp**2 / 1e9  # GPa

    # Estimasi G dan K_dry dari M dan Vp
    # Asumsi Vp/Vs ratio = 1.9 untuk sandstone (Sleipner = Utsira Sand)
    Vs  = Vp / 1.9
    G   = rho * Vs**2 / 1e9
    K_sat_ini = M - 4/3 * G

    # Fluid awal (brine)
    K_fl_ini = K_brine

    # K_dry dari Gassmann inverse
    A = K_sat_ini - (K_mineral * (1 - K_sat_ini/K_mineral))**2 / \
        (phi * K_mineral/K_fl_ini + (1-phi) - K_sat_ini/K_mineral)

    # Fluid akhir (CO₂) — Wood's law
    Sco2_fin = 1 - Sw_fin
    K_fl_fin = 1 / (Sco2_fin / K_co2 + Sw_fin / K_brine)
    rho_fl_fin = Sco2_fin * rho_co2 + Sw_fin * rho_brine

    # K_sat baru
    delta_K = (1 - A/K_mineral)**2 / \
              (phi/K_fl_fin + (1-phi)/K_mineral - A/K_mineral**2)
    K_sat_fin = A + delta_K

    # Densitas baru
    rho_new = ((1 - phi) * (RHOB - phi * rho_brine) + phi * rho_fl_fin)

    # Vp baru
    Vp_new = np.sqrt((K_sat_fin + 4/3 * G) * 1e9 / (rho_new * 1000))
    return Vp_new

# Hitung Vp setelah CO₂ injeksi (Sw turun dari 1.0 → 0.2)
phi = np.clip(NPHI, 0.01, 0.45)
Vp_co2 = gassmann_substitution(Vp_baseline, RHOB, phi, Sw_ini=1.0, Sw_fin=0.2)
delta_Vp_pct = (Vp_co2 - Vp_baseline) / Vp_baseline * 100

# ── Plot ───────────────────────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(15, 10), sharey=True)

axes[0].plot(Vp_baseline, depth, color='steelblue', linewidth=0.8)
axes[0].set_xlabel('Vp Baseline (m/s)')
axes[0].set_ylabel('Depth (m)')
axes[0].set_title('Vp\nBaseline')
axes[0].invert_yaxis()
axes[0].grid(True, alpha=0.3)

axes[1].plot(Vp_co2, depth, color='tomato', linewidth=0.8)
axes[1].set_xlabel('Vp CO₂ (m/s)')
axes[1].set_title('Vp after\nCO₂ injection')
axes[1].grid(True, alpha=0.3)

axes[2].plot(delta_Vp_pct, depth, color='seagreen', linewidth=0.8)
axes[2].axvline(0, color='k', linewidth=0.5, linestyle='--')
axes[2].axvline(-10, color='red', linewidth=1, linestyle='--', alpha=0.7,
                label='TA anomaly (-10%)')
axes[2].set_xlabel('ΔVp (%)')
axes[2].set_title('ΔVp\n(After − Before)')
axes[2].legend(fontsize=8)
axes[2].grid(True, alpha=0.3)

axes[3].plot(RHOB, depth, color='purple', linewidth=0.8)
axes[3].set_xlabel('RHOB (g/cm³)')
axes[3].set_title('Bulk\nDensity')
axes[3].grid(True, alpha=0.3)

fig.suptitle('Gassmann Fluid Substitution — Well 15/9-13\nSleipner Field (Real Well Log Data)',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('gassmann_real.png', dpi=150)
# plt.show()
print("\nPlot tersimpan sebagai gassmann_real.png ✓")
print(f"Rata-rata ΔVp: {delta_Vp_pct.mean():.1f}%")
print(f"Min ΔVp: {delta_Vp_pct.min():.1f}%")