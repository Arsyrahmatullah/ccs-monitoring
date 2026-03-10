import numpy as np
import matplotlib.pyplot as plt

# ── Fungsi Gassmann ────────────────────────────────────────
def gassmann(K_dry, G_dry, K_mineral, K_fluid, phi):
    """
    Gassmann fluid substitution
    Semua modulus dalam GPa, porositas dalam fraksi
    Returns: K_sat, Vp, Vs (dalam m/s)
    """
    # Biot coefficient
    delta_K = (1 - K_dry / K_mineral)**2
    denom   = (phi / K_fluid) + ((1 - phi) / K_mineral) - (K_dry / K_mineral**2)
    K_sat   = K_dry + delta_K / denom
    return K_sat

def compute_vp_vs(K_sat, G, rho):
    """Hitung Vp dan Vs dari moduli dan densitas"""
    Vp = np.sqrt((K_sat + 4/3 * G) / rho) * 1000  # km/s → m/s
    Vs = np.sqrt(G / rho) * 1000
    return Vp, Vs

def fluid_mix_density(rho_mineral, rho_fluid, phi):
    """Densitas batuan jenuh fluida"""
    return (1 - phi) * rho_mineral + phi * rho_fluid

# ── Parameter Batuan — estimasi Minahaki Formation ─────────
# Semua modulus dalam GPa, densitas dalam g/cm³

# Mineral (limestone/carbonate — dominan di Matindok)
K_mineral = 76.8   # GPa — calcite
G_mineral  = 32.0  # GPa — calcite (G tidak berubah dengan Gassmann)
rho_mineral = 2.71  # g/cm³

# Dry frame (dari empirical relation, phi=18%)
phi = 0.18
K_dry = 20.0   # GPa — estimated dry frame
G_dry = 15.0   # GPa — sama dengan G_sat (Gassmann: G tidak berubah)

# ── Properti Fluida ────────────────────────────────────────
# Brine (kondisi reservoir ~150 bar, 80°C)
K_brine  = 2.8    # GPa
rho_brine = 1.05  # g/cm³

# CO₂ superkritis (kondisi reservoir ~150 bar, 80°C)
K_co2    = 0.08   # GPa — jauh lebih kompresibel dari brine
rho_co2  = 0.70   # g/cm³

# ── Simulasi: variasi saturasi CO₂ ────────────────────────
S_co2 = np.linspace(0, 1, 100)   # 0% sampai 100% saturasi CO₂
S_brine = 1 - S_co2

# Wood's law — bulk modulus campuran fluida
K_fluid_mix = 1 / (S_co2 / K_co2 + S_brine / K_brine)
rho_fluid_mix = S_co2 * rho_co2 + S_brine * rho_brine

# Hitung K_sat dan Vp untuk setiap saturasi
Vp_list = []
Vs_list = []

for Kf, rhof in zip(K_fluid_mix, rho_fluid_mix):
    K_sat = gassmann(K_dry, G_dry, K_mineral, Kf, phi)
    rho_sat = fluid_mix_density(rho_mineral, rhof, phi)
    # konversi ke kg/m³ dan GPa → Pa
    Vp, Vs = compute_vp_vs(K_sat * 1e9, G_dry * 1e9, rho_sat * 1000)
    Vp_list.append(Vp)
    Vs_list.append(Vs)

Vp_arr = np.array(Vp_list)
Vs_arr = np.array(Vs_list)

# ── Plot ───────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(13, 5))

# Panel 1: Vp vs saturasi CO₂
axes[0].plot(S_co2 * 100, Vp_arr, color='steelblue', linewidth=2)
axes[0].axvline(0,   color='navy',   linestyle='--', alpha=0.5, label='100% Brine')
axes[0].axvline(100, color='crimson', linestyle='--', alpha=0.5, label='100% CO₂')
axes[0].set_xlabel('Saturasi CO₂ (%)')
axes[0].set_ylabel('Vp (m/s)')
axes[0].set_title('Vp vs Saturasi CO₂\n(Gassmann Fluid Substitution)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Panel 2: Vs vs saturasi CO₂
axes[1].plot(S_co2 * 100, Vs_arr, color='tomato', linewidth=2)
axes[1].set_xlabel('Saturasi CO₂ (%)')
axes[1].set_ylabel('Vs (m/s)')
axes[1].set_title('Vs vs Saturasi CO₂\n(Vs tidak berubah — Gassmann prediction)')
axes[1].grid(True, alpha=0.3)

# Panel 3: ΔVp dari baseline (100% brine)
delta_Vp = (Vp_arr - Vp_arr[0]) / Vp_arr[0] * 100
axes[2].plot(S_co2 * 100, delta_Vp, color='seagreen', linewidth=2)
axes[2].axhline(-10, color='red', linestyle='--', alpha=0.7, label='Anomali TA kamu (-10%)')
axes[2].set_xlabel('Saturasi CO₂ (%)')
axes[2].set_ylabel('ΔVp (%)')
axes[2].set_title('Perubahan Vp relatif\nvs saturasi CO₂')
axes[2].legend()
axes[2].grid(True, alpha=0.3)

fig.suptitle('Gassmann Fluid Substitution — Formasi Minahaki (Carbonate)\n'
             'Efek penggantian brine → CO₂ terhadap kecepatan seismik',
             fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('gassmann.png', dpi=150)
# plt.show()
print("Plot tersimpan sebagai gassmann.png ✓")
print(f"\nVp 100% brine : {Vp_arr[0]:.0f} m/s")
print(f"Vp 100% CO₂  : {Vp_arr[-1]:.0f} m/s")
print(f"ΔVp maksimum  : {delta_Vp[-1]:.1f}%")