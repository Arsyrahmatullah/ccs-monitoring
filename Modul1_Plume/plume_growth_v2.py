import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ── Data dari TA ───────────────────────────────────────────
years_ta  = np.array([2.5,  5.0,  10.0])
volume_ta = np.array([3.3,  6.7,  13.5])

# ── Model: power law V(t) = a * t^b ───────────────────────
def power_law(t, a, b):
    return a * np.power(t, b)

# Fit model ke data TA
params, _ = curve_fit(power_law, years_ta, volume_ta, p0=[2.0, 0.9])
a, b = params
if b < 1:
    print(f"b = {b:.3f} → pertumbuhan melambat (pressure-limited)")
elif b > 1:
    print(f"b = {b:.3f} → pertumbuhan mengakselerasi (belum pressure-limited)")
else:
    print(f"b = {b:.3f} → pertumbuhan linear")

# ── Simulasi ───────────────────────────────────────────────
years_sim  = np.linspace(0.1, 15, 200)
volume_linear    = 2.0 * years_sim
volume_powerlaw  = power_law(years_sim, a, b)

# ── Plot ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(years_sim, volume_linear, color='lightsteelblue', linewidth=1.5,
        linestyle='--', label='Model linear (v1)')
ax.plot(years_sim, volume_powerlaw, color='steelblue', linewidth=2.5,
        label=f'Power law model: V = {a:.2f} × t^{b:.2f} (v2)')
ax.scatter(years_ta, volume_ta, color='crimson', zorder=5, s=80,
           label='Data TA (4D Seismic Simulation)')

for yr, vol in zip(years_ta, volume_ta):
    ax.annotate(f'{vol} Mt\n({yr} yr)',
                xy=(yr, vol), xytext=(yr + 0.3, vol - 1.5),
                fontsize=9, color='crimson')

ax.set_xlabel('Waktu Injeksi (tahun)', fontsize=12)
ax.set_ylabel('Volume CO₂ Tersimpan (juta ton)', fontsize=12)
ax.set_title('CO₂ Plume Growth — Model Improvement (v2)', fontsize=13)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('plume_growth_v2.png', dpi=150)
plt.show()  # comment out ini
print("Plot tersimpan sebagai plume_growth_v2.png")