# Group exercise 4 — Parameter estimation

Lumped flowerpot (Ex03): interception + snow + soil with `Smax` overflow (= quick runoff). No HRUs.

```bash
cd abgaben/group_ex_04
python calibrate.py      # warmup / cal / val + sensitivity
python plot_events.py    # good + bad windows
```

## Periods

| | |
|---|---|
| Warmup | 1981–1982 |
| Calibration | 1983–2009 |
| Validation | 2010–2020 |

## Best set (grid, maximize ½ NSE + ½ Nash-Log on cal)

`mf=1.5`, `TT=0.5 °C`, `k=0.1`, `Smax=120 mm`, `Imax=2` (fixed)

| | NSE | Nash-Log | Bias |
|---|---|---|---|
| **Cal** | 0.436 | 0.339 | −0.076 (slightly too wet) |
| **Val** | 0.414 | 0.190 | −0.066 |

## What influences performance most?

One-at-a-time around the optimum (Δ fitness on cal):

| Parameter | Δ fitness |
|---|---|
| **k** | **1.09** |
| Smax | 0.51 |
| TT | 0.36 |
| mf | 0.04 |

**`k` dominates** — it sets how fast the soil empties (peaks vs baseflow). `Smax` controls when overflow (quick runoff) kicks in. Snow params matter less on this coarse grid once `TT` is in a sensible range.

## Event plots

Honest: overall the model is only middling (cal NSE ~0.44). Plots use `plot_style.set_title` / `figure_note`.

- **Better** (`event_better_2010-07-09_…`): summer 2010 pulse — timing and magnitude roughly in the ballpark (still not perfect).  
- **Bad** (`event_bad_2020-01-28_…`): early Feb 2020 — **rain-on-snow** (confirmed with MeteoSwiss). Obs ~31 mm/d, lumped ~⅓ of that; temp-index soil cannot catch the melt pulse.

Same windows with an extra line (`event_*_hru_bands_*`): Ex04 lumped vs `future_ideas` cover HRUs × elevation bands (+ROS). Not part of the Ex04 lumped deliverable — comparison only.
