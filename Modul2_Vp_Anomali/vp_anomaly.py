import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Parameter dari TA kamu ─────────────────────────────────
# Kedalaman formasi (meter)
formations = {
    'Minahaki':  (1400, 1800),   # top, bottom
    'Matindok':  (1800, 2200),
    'Tomori':    (2200, 2600),
}

# Vp baseline (m/s) — sebelum injeksi
vp_baseline = {
    'Minahaki': 2800,
    'Matindok': 3100,
    'Tomori':   3400,
}

# Anomali Vp di zona plume akibat CO₂ (-10% dari TA kamu)
vp_anomaly_pct = -0.10  # -10%

# ── Buat grid cross-section ────────────────────────────────
depth    = np.linspace(1000, 3000, 300)   # kedalaman (m)
distance = np.linspace(0, 5000, 300)      # jarak lateral (m)
D, X     = np.meshgrid(depth, distance)

# ── Inisialisasi grid Vp dengan gradien vertikal ──────────
vp_before = np.zeros_like(D)
vp_after  = np.zeros_like(D)

# Gradient dalam setiap formasi (Vp naik ~100 m/s per 100m kedalaman)
vp_gradient = 0.8  # m/s per meter kedalaman

for name, (top, bot) in formations.items():
    mask = (D >= top) & (D < bot)
    # Vp baseline di top formasi + gradien ke bawah
    vp_top = vp_baseline[name]
    vp_before[mask] = vp_top + vp_gradient * (D[mask] - top)
    vp_after[mask]  = vp_top + vp_gradient * (D[mask] - top)

# ── Bentuk plume mushroom (buoyancy-driven) ───────────────
# Terdiri dari dua bagian: stem (bawah) + cap (atas/melebar)

# Stem — zona injeksi langsung, sempit vertikal
stem_mask = (
    (np.abs(X - 2500) <= 150) &
    (D >= 1500) & (D <= 1650)
)

# Cap — zona akumulasi di atas, melebar karena buoyancy
cap_mask = (
    ((X - 2500) / 600)**2 +
    ((D - 1430) / 100)**2
) <= 1.0

# Tambahan — lateral spread di tengah (transisi stem ke cap)
mid_mask = (
    ((X - 2500) / 300)**2 +
    ((D - 1530) / 80)**2
) <= 1.0

plume_mask = stem_mask | cap_mask | mid_mask

vp_after[plume_mask] = vp_after[plume_mask] * (1 + vp_anomaly_pct)

# ── Plot ───────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 6))

# Panel 1: Vp sebelum injeksi
im1 = axes[0].pcolormesh(X/1000, D, vp_before,
                          cmap='seismic_r', vmin=2600, vmax=3600)
axes[0].set_title('Vp Sebelum Injeksi\n(Baseline)', fontsize=11)
axes[0].set_xlabel('Jarak Lateral (km)')
axes[0].set_ylabel('Kedalaman (m)')
axes[0].invert_yaxis()
plt.colorbar(im1, ax=axes[0], label='Vp (m/s)')

# Panel 2: Vp setelah injeksi
im2 = axes[1].pcolormesh(X/1000, D, vp_after,
                          cmap='seismic_r', vmin=2600, vmax=3600)
axes[1].set_title('Vp Setelah Injeksi CO₂\n(dengan plume)', fontsize=11)
axes[1].set_xlabel('Jarak Lateral (km)')
axes[1].invert_yaxis()
plt.colorbar(im2, ax=axes[1], label='Vp (m/s)')

# Panel 3: Time-lapse difference (After - Before)
diff = vp_after - vp_before
im3 = axes[2].pcolormesh(X/1000, D, diff,
                          cmap='RdBu', vmin=-350, vmax=350)
axes[2].set_title('4D Seismic Difference\n(After − Before)', fontsize=11)
axes[2].set_xlabel('Jarak Lateral (km)')
axes[2].invert_yaxis()
plt.colorbar(im3, ax=axes[2], label='ΔVp (m/s)')

# Label formasi di panel 3
for name, (top, bot) in formations.items():
    axes[2].axhline(top, color='k', linewidth=0.5, linestyle='--', alpha=0.5)
    axes[2].text(0.1, (top + bot)/2, name, fontsize=8, va='center', color='k')

fig.suptitle('4D Seismic Vp Monitoring — CO₂ Injection\nLapangan Matindok, Sulawesi Tengah',
             fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig('vp_anomaly.png', dpi=150)
plt.show()
print("Plot tersimpan sebagai vp_anomaly.png ✓")