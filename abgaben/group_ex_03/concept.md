# Exercise 3 – Concept

Lumped flowerpot for the Thur at Jonschwil-Mühlau (CAMELS-CH 2303). One catchment, one temperature, daily step.

## Idea

Precipitation enters the catchment, is split into rain and snow, passes a thin interception store and a snowpack, then fills a soil store. The soil has a capacity and loses water by ET and by outflow. That outflow is the modelled discharge.

```
P, T → interception → rain/snow → snowpack → soil → Q
                         │                        │
                       melt ──────────────────────┘
```

This is a reduced form of our perceptual model: the same story (rain vs snow, canopy, pack, soil, streamflow), without groundwater, elevation bands, or a separate fast-runoff routine.

## Why this structure

We already built the pieces in earlier exercises:

- linear store with capacity and ET → soil / flowerpot
- temperature-index rain/snow split and melt → snowpack
- interception is the missing thin store before rain/snow

A lumped set-up is what the exercise asks for first. Coupling those modules is enough for a first modelled-vs-observed discharge plot. Anything more (groundwater, HRU bands, infiltration excess as its own process) would be a second model, not a clearer first one.

## What belongs in v1

| Piece | Role | Reason |
|---|---|---|
| Interception | Small canopy store; overflow = throughfall; evaporates from PET first | Present in the perceptual model; cheap to add; uses PET before the soil does |
| Rain/snow + snowpack | Threshold `TT`, melt `mf · max(T − TT, 0)` | Required by the exercise; same logic as the personal snow exercise |
| Soil store | Capacity `Smax`, linear outflow `k · S`, ET ∝ √(S/Smax), overflow joins Q | The flowerpot; same step as group exercise 2c |
| PET | CAMELS `pet_sim` | Available for the catchment; exercise allows pyet later |

## What does not (yet)

| Left out | Reason |
|---|---|
| Separate groundwater | The soil store already has a slow linear outflow; a second store needs another parameter without a clear gain for the hand-in |
| Elevation bands | Still one catchment-mean T; bands need DEM zones and lapse rates |
| Explicit overland flow | Soil overflow stands in for “too much water, leaves quickly” |
| Sublimation as its own flux | Would need an extra snow ET term; PET already acts on interception and soil |
| pyet | Optional; CAMELS PET is enough for the first runs |

## Two forcings

Same model, different input for P and T:

1. **CAMELS catchment average** — what the catchment “felt” in the dataset we use for Q and PET  
2. **MeteoSwiss stations SAE and EBK** — point precip and temperature (`rre150d0`, `tre200d0`)

Q and PET stay from CAMELS in both runs, so the comparison is fair. Station precip will not match the catchment mean; that difference is part of the exercise (slide “Station versus CAMELS precip”).

SAE is high (Säntis); EBK is lower in the region. Showing both makes the forcing effect visible without changing the model.

## Parameters

### First guess (before any Q fit)

Taken from earlier work, not tuned to discharge:

| Symbol | First value | Where it came from |
|---|---|---|
| `Imax` | 2 mm | Thin interception; little mass, kept fixed |
| `TT` | 2 °C | Mild-winter snow fit (2019/20) |
| `mf` | 1 mm °C⁻¹ d⁻¹ | Same |
| `Smax` | 80 mm | Between the 40 mm demo store and a fuller soil |
| `k` | 0.1 d⁻¹ | Linear store from exercise 2a |

The decade snow optimum (`mf = 0.6`, `TT = 0.5`) was **not** used here at first: it fits SWE over many years, not Q in one winter, and melts 2019/20 away.

### Fit to observed discharge

Grid search on CAMELS forcing against daily Q (RMSE). `Imax` left at 2 mm. Search script: `calibration/optimise_flowerpot.py` (outside the hand-in narrative).

| | `mf` | `TT` | `k` | `Smax` | RMSE |
|---|---|---|---|---|---|
| First guess, 2010–2020 | 1 | 2 °C | 0.1 | 80 | 3.70 mm/d |
| Best on 2010–2020 | **1** | **0.5 °C** | **0.2** | **80** | **2.68 mm/d** |
| Best on 2019/20 only | 2 | 2 °C | 0.1 | 80 | 2.24 mm/d |

**Choice for the plots:** the 2010–2020 optimum (`mf = 1`, `TT = 0.5`, `k = 0.2`, `Smax = 80`).  
Reason: one parameter set for the catchment, not a set that only flatters one mild winter. Over ten years the search wants a lower melt threshold (more snow held, then released) and a faster soil response (`k = 0.2`). `Smax = 80` stays; capacity was already in a good range.

The 2019/20-only optimum barely beats the first guess for that year. Using it would hide that a mild year and a long record want different snow thresholds — the same tension we saw in the snow exercise.

## What we expect to see

- **CAMELS run:** mean Q roughly in the right ballpark; peaks often too flat or mistimed; overflow events can spike too hard.  
- **Station runs:** same model, shifted water balance and timing, because P and T are not the catchment mean. SAE (high) vs EBK (lower) should look different from each other and from CAMELS.  
- **Good vs bad events:** pick windows where rain-on-snow or a clear rain peak is captured, and windows where the store empties too early or a station storm never existed in the catchment mean (or the reverse).

## Limitations (for the PDF)

- One temperature for a catchment that rises from ~550 m to >2000 m.  
- No groundwater; baseflow is only the slow end of the soil store.  
- Overflow is a crude stand-in for fast runoff.  
- Station P/T ≠ catchment P/T; neither is “wrong”, they answer different questions.  
- Parameters from a coarse grid on RMSE; not a formal calibration, not validated on a held-out period.
