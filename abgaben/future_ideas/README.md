# Future ideas

Separate from Exercise 3. Ex03 stays the **simple lumped flowerpot** from the last pull. Everything below lives only here.

## What moved out of Ex03

| Idea | Modules |
|---|---|
| Fast path + groundwater | `soil_pathways.py`, `routing.py`, `pathways.py` |
| Peak-focused calibration | `metrics.py`, `optimise_peaks.py`, `run_peaks.py` |
| Land-cover HRUs | `landcover.py`, `hru_model.py`, `run_hru.py` |
| Cover × elevation | `elevation.py`, `run_hru.py --bands` |

Still reused from Ex03 (unchanged): `interception`, `snow` (via wrapper), `load`, `plot_runoff` / style.

## Rain-on-snow (SOLID extension)

Ex03 `snow_step` is not rewritten. `snow_ros.py` calls it, then adds optional melt:

`melt_ros = min(SWE, k_ros · P_rain · max(T − TT, 0))` with default `k_ros ≈ 0.0125` (°C⁻¹, ≈ c_w/L_f).

Pass `k_ros=0` to turn it off. Threaded through `pathways.simulate` and the HRU runners.

## Pathways model

```
P, T → interception → snow → soil
                              ├─ overflow ──► Q (direct or routed k_fast)
                              ├─ interflow ─► Q
                              └─ f_gw · drainage → GW → Q
```

## Peaks without wrecking low flows

- `direct_overflow=True` (overflow same day).  
- Calibrate: maximize `½ NSE + ½ NSE_high`, keep `Nash-Log ≥ baseline − 0.05`.  
- Pick: `mf=1`, `TT=0.5`, `k=0.3`, `Smax=80`, `k_gw=0.02`, `f_gw=0.25`.

## Land cover → 3 HRUs

All 12 CORINE columns mapped to forest / grass / quick (weights fixed). Optional `--bands`: 4 equal-area elev bands, T lapsed (−6.5 °C/km).

```bash
cd abgaben/future_ideas
python optimise_peaks.py
python run_peaks.py
python run_hru.py --gauge 2303 --bands --compare-lumped
python run_validation.py
```

## Validation quality plots

Split-sample validation window **2015-10-01 → 2020-09-30** (1 year spin-up before).

`run_validation.py` writes for each model (`pathways`, `hru_bands`):

- `val_*_scatter.png` — obs vs mod (linear + log), NSE / Nash-Log / bias / …
- `val_*_residuals.png` — mod−obs over time and vs Q_obs  
- `val_*_fdc.png` — flow-duration curves  

Bias in metrics: `(sum(obs) − sum(mod)) / sum(obs)` → **positive = model too dry**.

Hydrograph / validation scripts use a **running series**: one `simulate()` from the
first CAMELS day through `end` (stores never reset at the plot start). The figure
is only a cut of that run. Optional `--spin-years N` shortens the warm-up for tests.

Figures in `figures/`.
