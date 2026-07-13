# scripts/run_plume.py
import os
import sys

# Pintu darurat untuk mengunci path folder src lokal
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "../src")))

from ccs_monitoring.Plume.growth import simulate_plume_growth

if __name__ == "__main__":
    print("[CLI] Starting standalone Volumetric Plume Expansion calculation...")
    simulate_plume_growth()