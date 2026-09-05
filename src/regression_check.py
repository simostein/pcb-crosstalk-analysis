import sys
sys.path.insert(0, 'src')
import numpy as np
from crosstalk_model import BASELINE, simulate
t, vs, Vf, Va, mp = simulate(BASELINE)
mask = (t >= 0.5e-9) & (t <= 4.0e-9)
old = np.genfromtxt('data/baseline_results.csv', delimiter=',',
                    skip_header=1, usecols=1)
print("max abs diff vs v1 CSV (mV):",
      float(np.max(np.abs(Vf[mask] * 1e3 - old))))
print("Zgm:", mp["Z_geometric_mean_ohm"])
from tune_width import tune_width
w, z = tune_width(8.0, 3.0, mp["Z_geometric_mean_ohm"], tol=0.5)
print(f"tune S=8,h=3 -> W={w:.3f} mil, Zgm={z:.3f} ohm")
