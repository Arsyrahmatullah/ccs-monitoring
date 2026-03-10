import numpy as np
import matplotlib.pyplot as plt

# ── Data dari TA kamu ──────────────────────────────────────
# Laju injeksi CO₂ (juta ton/tahun) — dari Lapangan Matindok
injection_rate = 2.0  # Mt/year (rata-rata dari angka TA kamu)

# Titik data hasil simulasi TA
years_ta   = [0,   2.5,  5.0,  10.0]
volume_ta  = [0,   3.3,  6.7,  13.5]  # juta ton

# ── Simulasi pertumbuhan plume ─────────────────────────────
years_sim  = np.linspace(0, 15, 100)  # simulasi sampai 15 tahun
volume_sim = injection_rate * years_sim

# ── Plot ──────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))

# Garis simulasi
ax.plot(years_sim, volume_sim, color='steelblue', linewidth=2,
        label='Simulasi (linear model)')

# Titik data dari TA
ax.scatter(years_ta, volume_ta, color='crimson', zorder=5, s=80,
           label='Data TA (4D Seismic Simulation)')

# Anotasi tiap titik
for yr, vol in zip(years_ta[1:], volume_ta[1:]):
    ax.annotate(f'{vol} Mt\n({yr} yr)',
                xy=(yr, vol), xytext=(yr + 0.3, vol - 1.2),
                fontsize=9, color='crimson')

ax.set_xlabel('Waktu Injeksi (tahun)', fontsize=12)
ax.set_ylabel('Volume CO₂ Tersimpan (juta ton)', fontsize=12)
ax.set_title('CO₂ Plume Growth — Lapangan Matindok, Sulawesi Tengah', fontsize=13)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('plume_growth.png', dpi=150)
plt.show()
print("Plot tersimpan sebagai plume_growth.png")