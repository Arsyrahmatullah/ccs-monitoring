import lasio
import io
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="CCS Monitoring — Matindok Field",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 CCS Monitoring & Simulation")
st.markdown("**Lapangan Matindok, Sulawesi Tengah** — Based on 4D Seismic Thesis Research")
st.divider()

# ── Sidebar ────────────────────────────────────────────────
st.sidebar.header("⚙️ Parameter Simulasi")
injection_rate = st.sidebar.slider("Laju Injeksi CO₂ (Mt/tahun)", 1.0, 5.0, 2.0, 0.1)
sim_years      = st.sidebar.slider("Durasi Simulasi (tahun)", 5, 30, 15)
vp_anomaly_pct = st.sidebar.slider("Anomali Vp di zona plume (%)", -20, -5, -10)

st.sidebar.divider()
st.sidebar.markdown("📌 Data titik dari TA:")
st.sidebar.markdown("- 2.5 yr → 3.3 Mt\n- 5.0 yr → 6.7 Mt\n- 10.0 yr → 13.5 Mt")

# ── Tab layout ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 CO₂ Plume Growth", "🔬 4D Seismic Vp Anomaly", "📂 Real Well Log"])
# ════════════════════════════════════════════════════════════
# TAB 1 — Plume Growth
# ════════════════════════════════════════════════════════════
with tab1:
    st.subheader("CO₂ Plume Growth Simulation")

    years_ta  = np.array([2.5, 5.0, 10.0])
    volume_ta = np.array([3.3, 6.7, 13.5])

    def power_law(t, a, b):
        return a * np.power(t, b)

    params, _ = curve_fit(power_law, years_ta, volume_ta, p0=[2.0, 0.9])
    a, b = params

    years_sim     = np.linspace(0.1, sim_years, 200)
    volume_linear = injection_rate * years_sim
    volume_power  = power_law(years_sim, a, b)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(years_sim, volume_linear, '--', color='lightsteelblue',
            linewidth=1.5, label='Model linear')
    ax.plot(years_sim, volume_power, color='steelblue',
            linewidth=2.5, label=f'Power law: V = {a:.2f} × t^{b:.2f}')
    ax.scatter(years_ta, volume_ta, color='crimson', zorder=5, s=80,
               label='Data TA (4D Seismic Simulation)')
    for yr, vol in zip(years_ta, volume_ta):
        ax.annotate(f'{vol} Mt', xy=(yr, vol), xytext=(yr+0.2, vol+0.3), fontsize=9, color='crimson')

    ax.set_xlabel('Waktu Injeksi (tahun)')
    ax.set_ylabel('Volume CO₂ Tersimpan (juta ton)')
    ax.set_title('CO₂ Plume Growth — Lapangan Matindok')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)

    col1, col2, col3 = st.columns(3)
    col1.metric("Volume @ 5 tahun", f"{power_law(5, a, b):.1f} Mt")
    col2.metric("Volume @ 10 tahun", f"{power_law(10, a, b):.1f} Mt")
    col3.metric("Volume @ 20 tahun", f"{power_law(20, a, b):.1f} Mt")

# ════════════════════════════════════════════════════════════
# TAB 2 — Vp Anomaly
# ════════════════════════════════════════════════════════════
with tab2:
    st.subheader("4D Seismic Vp Anomaly Visualizer")

    formations = {
        'Minahaki': (1400, 1800),
        'Matindok': (1800, 2200),
        'Tomori':   (2200, 2600),
    }
    vp_baseline = {'Minahaki': 2800, 'Matindok': 3100, 'Tomori': 3400}

    depth    = np.linspace(1000, 3000, 200)
    distance = np.linspace(0, 5000, 200)
    D, X     = np.meshgrid(depth, distance)

    vp_before = np.zeros_like(D)
    vp_after  = np.zeros_like(D)

    for name, (top, bot) in formations.items():
        mask = (D >= top) & (D < bot)
        vp_before[mask] = vp_baseline[name]
        vp_after[mask]  = vp_baseline[name]

    plume_mask = (
        ((X - 2500) / 800)**2 + ((D - 1600) / 150)**2
    ) <= 1.0
    vp_after[plume_mask] = vp_after[plume_mask] * (1 + vp_anomaly_pct / 100)

    diff = vp_after - vp_before

    fig2, axes = plt.subplots(1, 3, figsize=(14, 5))
    im1 = axes[0].pcolormesh(X/1000, D, vp_before, cmap='seismic_r', vmin=2600, vmax=3600)
    axes[0].set_title('Vp Sebelum Injeksi')
    axes[0].set_ylabel('Kedalaman (m)')
    axes[0].set_xlabel('Jarak Lateral (km)')
    axes[0].invert_yaxis()
    plt.colorbar(im1, ax=axes[0], label='Vp (m/s)')

    im2 = axes[1].pcolormesh(X/1000, D, vp_after, cmap='seismic_r', vmin=2600, vmax=3600)
    axes[1].set_title('Vp Setelah Injeksi CO₂')
    axes[1].set_xlabel('Jarak Lateral (km)')
    axes[1].invert_yaxis()
    plt.colorbar(im2, ax=axes[1], label='Vp (m/s)')

    im3 = axes[2].pcolormesh(X/1000, D, diff, cmap='RdBu', vmin=-350, vmax=350)
    axes[2].set_title('4D Difference (After − Before)')
    axes[2].set_xlabel('Jarak Lateral (km)')
    axes[2].invert_yaxis()
    plt.colorbar(im3, ax=axes[2], label='ΔVp (m/s)')

    for name, (top, bot) in formations.items():
        axes[2].axhline(top, color='k', linewidth=0.5, linestyle='--', alpha=0.5)
        axes[2].text(0.1, (top+bot)/2, name, fontsize=8, va='center')

    plt.tight_layout()
    st.pyplot(fig2)

    st.info(f"**Anomali Vp**: {vp_anomaly_pct}% di zona plume → ΔVp = {3100 * vp_anomaly_pct/100:.0f} m/s di Formasi Minahaki")
    # ════════════════════════════════════════════════════════════
# TAB 3 — Real Well Log
# ════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Gassmann Fluid Substitution — Real Well Log")
    st.markdown("Upload file `.las` dari well log kamu untuk jalankan Gassmann fluid substitution.")

    uploaded_file = st.file_uploader("Upload LAS file", type=["las", "LAS"])

    if uploaded_file is not None:
        try:
            # Baca LAS dari upload
            las = lasio.read(io.StringIO(uploaded_file.read().decode('utf-8', errors='ignore')))

            # Cek curves yang tersedia
            curve_names = [c.mnemonic for c in las.curves]
            st.success(f"File berhasil dibaca! Curves: {', '.join(curve_names)}")

            # Ambil data
            depth = las['DEPTH']
            DT    = las['DT']
            RHOB  = las['RHOB']
            NPHI  = las['NPHI']

            # Clean
            mask = (DT > 0) & (DT != -999.25) & \
                   (RHOB > 0) & (RHOB != -999.25) & \
                   (NPHI > 0) & (NPHI != -999.25)

            depth = depth[mask]
            DT    = DT[mask]
            RHOB  = RHOB[mask]
            NPHI  = NPHI[mask]

            st.info(f"Data points: {len(depth)} | Depth: {depth.min():.0f} – {depth.max():.0f} m")

            # Konversi dan Gassmann
            Vp_baseline = 304800 / DT
            phi = np.clip(NPHI, 0.01, 0.45)

            K_mineral, K_brine, K_co2 = 36.0, 2.8, 0.08
            rho_brine, rho_co2 = 1.05, 0.70
            Sw_fin = st.sidebar.slider("Sw setelah injeksi CO₂", 0.0, 1.0, 0.2, 0.05)

            # Gassmann
            Vp_list = []
            for vp, rho, p in zip(Vp_baseline, RHOB, phi):
                rho_kg = rho * 1000
                Vs = vp / 1.9
                G  = rho_kg * Vs**2 / 1e9
                M  = rho_kg * vp**2 / 1e9
                K_sat_ini = M - 4/3 * G
                A = K_sat_ini - (K_mineral * (1 - K_sat_ini/K_mineral))**2 / \
                    (p * K_mineral/K_brine + (1-p) - K_sat_ini/K_mineral)
                Sco2 = 1 - Sw_fin
                K_fl = 1 / (Sco2/K_co2 + Sw_fin/K_brine)
                rho_fl = Sco2 * rho_co2 + Sw_fin * rho_brine
                dK = (1 - A/K_mineral)**2 / (p/K_fl + (1-p)/K_mineral - A/K_mineral**2)
                K_sat_fin = A + dK
                rho_new = (1-p) * (rho - p*rho_brine) + p*rho_fl
                vp_new = np.sqrt((K_sat_fin + 4/3*G) * 1e9 / (rho_new * 1000))
                Vp_list.append(vp_new)

            Vp_co2 = np.array(Vp_list)
            delta_Vp = (Vp_co2 - Vp_baseline) / Vp_baseline * 100

            # Plot
            fig, axes = plt.subplots(1, 3, figsize=(12, 6), sharey=True)

            axes[0].plot(Vp_baseline, depth, color='steelblue', linewidth=0.8)
            axes[0].set_xlabel('Vp Baseline (m/s)')
            axes[0].set_ylabel('Depth (m)')
            axes[0].set_title('Vp Baseline')
            axes[0].invert_yaxis()
            axes[0].grid(True, alpha=0.3)

            axes[1].plot(Vp_co2, depth, color='tomato', linewidth=0.8)
            axes[1].set_xlabel('Vp CO₂ (m/s)')
            axes[1].set_title('Vp after CO₂')
            axes[1].grid(True, alpha=0.3)

            axes[2].plot(delta_Vp, depth, color='seagreen', linewidth=0.8)
            axes[2].axvline(-10, color='red', linestyle='--', alpha=0.7, label='TA anomaly (-10%)')
            axes[2].axvline(0, color='k', linestyle='--', linewidth=0.5)
            axes[2].set_xlabel('ΔVp (%)')
            axes[2].set_title('ΔVp (After − Before)')
            axes[2].legend(fontsize=8)
            axes[2].grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)

            col1, col2 = st.columns(2)
            col1.metric("Rata-rata ΔVp", f"{delta_Vp.mean():.1f}%")
            col2.metric("Min ΔVp", f"{delta_Vp.min():.1f}%")

        except Exception as e:
            st.error(f"Error membaca file: {e}")
    else:
        st.info("Upload file LAS untuk memulai analisis.")