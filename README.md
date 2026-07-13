# CCS Monitoring & Simulation
**Carbon Capture and Storage (CCS) monitoring tools built in Python** Based on 4D seismic simulation research — Matindok Gas Field, Central Sulawesi

---

## 📌 Background
This project digitizes and extends results from an undergraduate thesis on  
**CO₂ storage feasibility using 4D seismic monitoring** at the Matindok–Donggi–Senoro  
gas field complex, Central Sulawesi, Indonesia.

The study used Petrel to simulate compressional wave velocity (Vp) changes due to CO₂ injection into the Minahaki Carbonate Formation, now fully refactored into a modern, automated Python package layout.

---

## 🗂️ Modules & Package Structure

Proyek ini telah disusun ulang ke dalam struktur paket `src/` modular untuk memisahkan mesin perhitungan sains dengan halaman visualisasi:

### 1. Central Site Presets (`src/ccs_monitoring/presets.py`)
Menyediakan dropdown pilihan parameter reservoir terkalibrasi langsung dari literatur dunia nyata secara terpusat:
- **Matindok (Thesis Reference)**: Formasi Karbonat Minahaki, Sulawesi Tengah.
- **Sleipner Utsira (North Sea)**: Benchmark sand aquifer standar industri.
- **Baltic Sea Yoldia (Aquifer)**: Model batuan pasir untuk *patchy saturation*.

---

### 2. CO₂ Plume Growth Simulation (`src/ccs_monitoring/Plume/`)
Visualisasi perluasan volume *plume* karbon secara radial dari sumur injeksi.
- Model aliran *power-law* ($t^{0.5}$) dynamic gravity current.
- Ditambah **Porosity Uncertainty Band (±3%)** untuk melihat batas ketidakpastian volume reservoir.

**Output Manual (CLI):** `src/ccs_monitoring/Plume/plume_growth.png`

---

### 3. 4D Seismic Vp Anomaly Visualizer (`src/ccs_monitoring/Seismic/`)
Visualisasi penampang bumi 2D yang heterogen alami akibat injeksi gas.
- Menggunakan **Gaussian Random Field Texture** untuk menghasilkan efek variasi noise geologi asli.
- Pemodelan geometri **Mushroom-shaped CO₂ plume** akibat gaya apung fluida (*buoyancy-driven*).

**Output Manual (CLI):** `src/ccs_monitoring/Seismic/vp_anomaly.png`

---

### 4. Gassmann Fluid Substitution (`src/ccs_monitoring/Rock_physics/`)
Pemodelan fisika batuan (*rock physics*) untuk menghitung perubahan kecepatan gelombang seismik.
- Menggunakan rumus **Inversi Simbolik Eksak** (`sympy`) untuk menghitung modulus kering batuan tanpa eror aproksimasi fluida.
- **Toggle Theory**: Pilihan pencampuran fluida antara Wood's Law (Uniform Saturation) dan Brie's Empirical Law (Patchy Saturation).

---

### 5. Well Log Integration & Multi-Page Dashboard (`src/ccs_monitoring/Dashboard/`)
Aplikasi web interaktif multi-halaman yang menyatukan semua modul di atas dengan navigasi sidebar radio button yang reaktif.
- **LAS File Uploader**: Mendukung unggah file sumur bor asli format `.las` menggunakan parser `lasio`.
- Menyediakan *Demo Proxy Log* otomatis jika dijalankan tanpa file eksternal.

---

### 6. Anomaly Detection & Alerts (`src/ccs_monitoring/Anomaly/`)
Integrasi Modul 6 untuk mengevaluasi tingkat risiko dan keamanan batas penyimpanan bawah tanah.
- **Zero-Mean Trace nRMS Profile**: Kalkulasi perubahan amplitudo seismik sintetik agar sensitivitas metrik tidak kolaps.
- **Statistical Z-Score Deviation Field**: Mengisolasi sinyal migrasi fluida liar dari *background noise* geologi sekitarnya.

---

## 📥 Data Setup

Halaman *Well Log Analysis* mendukung file `.las` kustom Anda sendiri. Jika Anda ingin menguji menggunakan data benchmark sumur Sleipner dari Equinor:

1. Unduh data secara gratis di: **https://co2datashare.org/dataset/sleipner-2019-benchmark-model**
2. Pilih bagian **"Well data (2.1.2 - Well logs)"**
3. Ekstrak dan gunakan tombol **Upload** pada halaman dashboard untuk memasukkan file `.las` tersebut ke aplikasi.

---

## 🛠️ Tech Stack
| Tool | Purpose |
|---|---|
| Python 3.10+ | Core language framework |
| NumPy, SciPy | Numerical grid computing |
| Matplotlib | Subsurface section visualization |
| Streamlit | Interactive multi-page dashboard |
| lasio | LAS well log file reader engine |
| PyTest | Automated physics validation tests |

---

## 🚀 How to Run

### 1. Install Paket Lokal (Editable Mode)
```bash
git clone [https://github.com/Arsyrahmatullah/ccs-monitoring.git](https://github.com/Arsyrahmatullah/ccs-monitoring.git)
cd ccs-monitoring/ccs-monitoring
pip install -e .