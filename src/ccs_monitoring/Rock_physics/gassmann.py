# src/ccs_monitoring/Rock_physics/gassmann.py
import numpy as np

def wood_fluid_mixing(s_co2, k_brine, k_co2):
    """Computes effective fluid bulk modulus using Wood's Law (Reuss Bound)."""
    if s_co2 <= 0.0: return k_brine
    if s_co2 >= 1.0: return k_co2
    return 1.0 / (((1.0 - s_co2) / k_brine) + (s_co2 / k_co2))

def brie_fluid_mixing(s_co2, k_brine, k_co2, e=3.0):
    """Computes effective fluid bulk modulus using Brie's Patchy Saturation empirical law."""
    return (k_brine - k_co2) * ((1.0 - s_co2) ** e) + k_co2

def invert_k_dry(k_sat, k_m, k_brine, phi):
    """
    Exact symbolic solution derived via SymPy to extract Dry Rock Bulk Modulus (K_dry).
    Perfectly eliminates approximation errors for highly compressible fluids like CO2.
    """
    alpha = (phi * k_m / k_brine) + 1.0 - phi
    num = k_sat * alpha - k_m
    den = (phi * k_m / k_brine) + (k_sat / k_m) - 1.0 - phi
    k_dry = num / den
    return np.clip(k_dry, 1e-4, k_m - 1e-4)

def gassmann_substitution(vp_baseline, vs_baseline, rho_baseline_kg, phi, s_co2, 
                          k_m, k_brine, k_co2, rho_brine_kg, rho_co2_kg, rho_matrix_kg,
                          mixing_law="wood", brie_exponent=3.0):
    """
    Advanced Gassmann Fluid Substitution Engine.
    Inputs: Velocities in m/s, Densities in kg/m³, Moduli in GPa.
    Internal math operates purely in GPa via 1e-9 scale transformation factor.
    """
    # 1. Convert dynamic seismic profiles to GPa Moduli
    mu_baseline = rho_baseline_kg * (vs_baseline ** 2) * 1e-9
    k_sat_baseline = (rho_baseline_kg * (vp_baseline ** 2) * 1e-9) - (4.0 / 3.0) * mu_baseline
    
    # 2. Extract Exact Dry Modulus Framework
    k_dry = invert_k_dry(k_sat_baseline, k_m, k_brine, phi)
    
    # 3. Apply Selectable Fluid Mixing Law (Wood vs Patchy Brie)
    if mixing_law == "brie":
        k_fluid_eff = brie_fluid_mixing(s_co2, k_brine, k_co2, brie_exponent)
    else:
        k_fluid_eff = wood_fluid_mixing(s_co2, k_brine, k_co2)
        
    # 4. Forward Gassmann Formulation
    num_sat = (1.0 - (k_dry / k_m)) ** 2
    den_sat = (phi / k_fluid_eff) + ((1.0 - phi) / k_m) - (k_dry / (k_m ** 2))
    k_sat_monitor = k_dry + (num_sat / den_sat)
    
    # 5. Volumetric Density Substitution
    rho_fluid_eff = (s_co2 * rho_co2_kg) + ((1.0 - s_co2) * rho_brine_kg)
    rho_monitor_kg = (phi * rho_fluid_eff) + ((1.0 - phi) * rho_matrix_kg)
    
    # 6. Reconstruct Seismic Velocities back to m/s
    vp_monitor = np.sqrt(((k_sat_monitor + (4.0 / 3.0) * mu_baseline) * 1e9) / rho_monitor_kg)
    vs_monitor = np.sqrt((mu_baseline * 1e9) / rho_monitor_kg)
    
    return vp_monitor, vs_monitor, rho_monitor_kg