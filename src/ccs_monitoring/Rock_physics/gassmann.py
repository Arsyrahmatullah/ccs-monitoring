# Modul4_Gassmann/gassmann.py
import numpy as np

def wood_fluid_mixing(s_co2, k_brine, k_co2):
    """
    Calculate the effective bulk modulus of the fluid mixture using Wood's Law (Reuss Bound).
    """
    s_brine = 1.0 - s_co2
    if s_co2 <= 0.0: return k_brine
    if s_co2 >= 1.0: return k_co2
    return 1.0 / ((s_brine / k_brine) + (s_co2 / k_co2))

def invert_k_dry(k_sat_baseline, k_m, k_brine, phi):
    """
    Invert the Dry Rock Bulk Modulus (K_dry) exactly from baseline conditions.
    This formulation ensures mathematical stability under supercritical CO2 substitution.
    """
    num = k_sat_baseline * ((phi * k_m / k_brine) + 1.0 - phi) - k_m
    den = (phi * k_m / k_brine) + (k_sat_baseline / k_m) - 1.0 - phi
    k_dry = num / den
    return np.clip(k_dry, 1e-3, k_m - 1e-3)

def gassmann_substitution(vp_baseline, vs_baseline, rho_baseline, phi, s_co2, 
                          k_m, k_brine, k_co2, rho_brine, rho_co2, rho_matrix):
    """
    Core Gassmann Fluid Substitution Engine.
    Computes post-injection Vp, Vs, and Bulk Density changes with exact round-trip capability.
    """
    # 1. Compute baseline elastic moduli (100% brine saturated)
    mu_baseline = rho_baseline * (vs_baseline ** 2)
    k_sat_baseline = rho_baseline * (vp_baseline ** 2) - (4.0 / 3.0) * mu_baseline
    
    # 2. Invert for K_dry using baseline brine fluid properties
    k_dry = invert_k_dry(k_sat_baseline, k_m, k_brine, phi)
    
    # 3. Compute monitor fluid mixture properties
    k_f2 = wood_fluid_mixing(s_co2, k_brine, k_co2)
    rho_f2 = (s_co2 * rho_co2) + ((1.0 - s_co2) * rho_brine)
    
    # 4. Compute new saturated rock bulk modulus (Gassmann Forward)
    num_sat = (1.0 - (k_dry / k_m)) ** 2
    den_sat = (phi / k_f2) + ((1.0 - phi) / k_m) - (k_dry / (k_m ** 2))
    k_sat_monitor = k_dry + (num_sat / den_sat)
    
    # 5. Update saturated rock bulk density (g/cm3 for velocity calculation consistency)
    rho_monitor = (phi * (rho_f2 / 1000.0)) + ((1.0 - phi) * rho_matrix)
    
    # Shear modulus remains constant during fluid substitution (mu_monitor = mu_baseline)
    vp_monitor = np.sqrt((k_sat_monitor + (4.0 / 3.0) * mu_baseline) / rho_monitor)
    vs_monitor = np.sqrt(mu_baseline / rho_monitor)
    
    return vp_monitor, vs_monitor, rho_monitor