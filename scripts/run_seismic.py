# scripts/run_seismic.py
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "../src")))

from ccs_monitoring.Seismic.vp_anomaly import execute_seismic_visualization

if __name__ == "__main__":
    print("[CLI] Starting standalone 2D Stochastic Seismic Mesh simulation...")
    execute_seismic_visualization()