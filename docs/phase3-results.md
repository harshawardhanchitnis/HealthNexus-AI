# Phase 3 — measured model results

Generated from saved artifact reports after the independent evaluation/load verification. Seed 42; 540 days through 2026-09-27. These are results on calibrated simulated operations, not real-world predictive accuracy.

Models are selected by selection-period WAPE. Tables below report the untouched test period (2026-08-05 through 2026-09-27) across rolling 14-day origins. The final block overlaps its predecessor by two days. WAPE is a percentage; MAE/RMSE retain target units. Medicine pools units, so compare models within target only.

## IN

Model version: `forecast-v1-176a752efab3ae4e`. Evaluated 2026-09-27T16:19:03.228026+00:00. [Full JSON, including lead-specific scores](evaluation/IN.json).

| Target | Model | MAE | RMSE | WAPE % | Selected |
| --- | --- | ---: | ---: | ---: | --- |
| footfall | naive | 54.467133 | 94.693003 | 15.244320 |  |
| footfall | seasonal_naive | 14.091874 | 22.704103 | 3.944049 |  |
| footfall | moving_average | 38.251269 | 64.657334 | 10.705807 |  |
| footfall | hist_gradient_boosting | 10.707877 | 17.163377 | 2.996932 | yes |
| medicine | naive | 32.217892 | 69.290283 | 15.281022 |  |
| medicine | seasonal_naive | 8.431039 | 16.966618 | 3.998862 |  |
| medicine | moving_average | 22.778544 | 47.662603 | 10.803917 |  |
| medicine | hist_gradient_boosting | 6.493463 | 12.835365 | 3.079865 | yes |
| admissions | naive | 3.087302 | 5.627636 | 15.265313 |  |
| admissions | seasonal_naive | 0.793478 | 1.400976 | 3.923392 |  |
| admissions | moving_average | 2.201494 | 3.839716 | 10.885393 |  |
| admissions | hist_gradient_boosting | 0.676326 | 1.067208 | 3.344126 | yes |

| Target / resource | 80% observed coverage | 95% observed coverage | Calibration paths |
| --- | ---: | ---: | ---: |
| footfall / footfall | 81.9876% | 95.9023% | 828 |
| medicine / AMX | 80.1932% | 95.3416% | 828 |
| medicine / IFA | 81.6080% | 96.0921% | 828 |
| medicine / IVF | 85.8954% | 97.4983% | 828 |
| medicine / ORS | 83.2039% | 96.8081% | 828 |
| medicine / PCM | 88.0176% | 97.8606% | 828 |
| admissions / admissions | 82.0480% | 97.4896% | 828 |

## BR

Model version: `forecast-v1-d6457d5d28468752`. Evaluated 2026-09-27T16:19:17.655403+00:00. [Full JSON, including lead-specific scores](evaluation/BR.json).

| Target | Model | MAE | RMSE | WAPE % | Selected |
| --- | --- | ---: | ---: | ---: | --- |
| footfall | naive | 33.050595 | 57.631966 | 15.045183 |  |
| footfall | seasonal_naive | 7.360119 | 11.569022 | 3.350449 |  |
| footfall | moving_average | 23.141582 | 39.548295 | 10.534435 |  |
| footfall | hist_gradient_boosting | 6.237556 | 9.753370 | 2.839439 | yes |
| medicine | naive | 17.894643 | 36.670403 | 15.241606 |  |
| medicine | seasonal_naive | 3.982738 | 7.501547 | 3.392262 |  |
| medicine | moving_average | 12.470493 | 25.034722 | 10.621634 |  |
| medicine | hist_gradient_boosting | 3.600341 | 6.509115 | 3.066559 | yes |
| admissions | naive | 1.839286 | 3.399054 | 14.756447 |  |
| admissions | seasonal_naive | 0.375000 | 0.775365 | 3.008596 |  |
| admissions | moving_average | 1.318027 | 2.337399 | 10.574430 |  |
| admissions | hist_gradient_boosting | 0.395126 | 0.679667 | 3.170066 | yes |

**admissions:** the selected hist_gradient_boosting loses to seasonal_naive on test WAPE. Selection is deliberately not revised using the test set.


| Target / resource | 80% observed coverage | 95% observed coverage | Calibration paths |
| --- | ---: | ---: | ---: |
| footfall / footfall | 87.5000% | 97.0238% | 24 |
| medicine / AMX | 90.7738% | 97.0238% | 24 |
| medicine / IFA | 89.2857% | 96.1310% | 24 |
| medicine / IVF | 87.5000% | 97.6190% | 24 |
| medicine / ORS | 86.6071% | 97.3214% | 24 |
| medicine / PCM | 91.0714% | 98.8095% | 24 |
| admissions / admissions | 86.0119% | 94.9405% | 24 |

## RU

Model version: `forecast-v1-85e3ab1afc6775dc`. Evaluated 2026-09-27T16:19:18.474234+00:00. [Full JSON, including lead-specific scores](evaluation/RU.json).

| Target | Model | MAE | RMSE | WAPE % | Selected |
| --- | --- | ---: | ---: | ---: | --- |
| footfall | naive | 25.267857 | 45.053870 | 15.297297 |  |
| footfall | seasonal_naive | 5.886905 | 10.180514 | 3.563964 |  |
| footfall | moving_average | 18.313775 | 31.078639 | 11.087258 |  |
| footfall | hist_gradient_boosting | 5.089941 | 8.130868 | 3.081478 | yes |
| medicine | naive | 14.926190 | 33.032920 | 15.396896 |  |
| medicine | seasonal_naive | 3.496429 | 7.611395 | 3.606690 |  |
| medicine | moving_average | 10.960034 | 22.865653 | 11.305664 |  |
| medicine | hist_gradient_boosting | 3.068606 | 5.964288 | 3.165376 | yes |
| admissions | naive | 1.416667 | 2.669270 | 15.139949 |  |
| admissions | seasonal_naive | 0.321429 | 0.685739 | 3.435115 | yes |
| admissions | moving_average | 1.094388 | 1.854164 | 11.695747 |  |
| admissions | hist_gradient_boosting | 0.404541 | 0.587841 | 4.323341 |  |

| Target / resource | 80% observed coverage | 95% observed coverage | Calibration paths |
| --- | ---: | ---: | ---: |
| footfall / footfall | 84.2262% | 96.4286% | 24 |
| medicine / AMX | 83.9286% | 96.7262% | 24 |
| medicine / IFA | 90.1786% | 97.6190% | 24 |
| medicine / IVF | 84.8214% | 95.2381% | 24 |
| medicine / ORS | 86.9048% | 96.7262% | 24 |
| medicine / PCM | 89.8810% | 97.0238% | 24 |
| admissions / admissions | 90.7738% | 98.8095% | 24 |

## CN

Model version: `forecast-v1-40bd39b1f0f71bf1`. Evaluated 2026-09-27T16:19:19.239665+00:00. [Full JSON, including lead-specific scores](evaluation/CN.json).

| Target | Model | MAE | RMSE | WAPE % | Selected |
| --- | --- | ---: | ---: | ---: | --- |
| footfall | naive | 30.312500 | 53.156132 | 15.625719 |  |
| footfall | seasonal_naive | 7.425595 | 12.315181 | 3.827803 |  |
| footfall | moving_average | 21.200255 | 36.657039 | 10.928469 |  |
| footfall | hist_gradient_boosting | 5.665924 | 8.900525 | 2.920714 | yes |
| medicine | naive | 17.867857 | 38.796892 | 15.668323 |  |
| medicine | seasonal_naive | 4.441667 | 9.309813 | 3.894897 |  |
| medicine | moving_average | 12.672109 | 27.048445 | 11.112172 |  |
| medicine | hist_gradient_boosting | 3.997815 | 7.649987 | 3.505684 | yes |
| admissions | naive | 1.693452 | 3.202956 | 15.390857 |  |
| admissions | seasonal_naive | 0.419643 | 0.814672 | 3.813903 |  |
| admissions | moving_average | 1.250425 | 2.198968 | 11.364426 |  |
| admissions | hist_gradient_boosting | 0.478307 | 0.676341 | 4.347071 | yes |

**admissions:** the selected hist_gradient_boosting loses to seasonal_naive on test WAPE. Selection is deliberately not revised using the test set.


| Target / resource | 80% observed coverage | 95% observed coverage | Calibration paths |
| --- | ---: | ---: | ---: |
| footfall / footfall | 87.2024% | 96.4286% | 24 |
| medicine / AMX | 79.4643% | 95.5357% | 24 |
| medicine / IFA | 89.2857% | 97.9167% | 24 |
| medicine / IVF | 85.7143% | 94.9405% | 24 |
| medicine / ORS | 75.2976% | 97.6190% | 24 |
| medicine / PCM | 87.2024% | 97.6190% | 24 |
| admissions / admissions | 76.4881% | 92.5595% | 24 |

## ZA

Model version: `forecast-v1-862d8eb0168f5774`. Evaluated 2026-09-27T16:19:19.978941+00:00. [Full JSON, including lead-specific scores](evaluation/ZA.json).

| Target | Model | MAE | RMSE | WAPE % | Selected |
| --- | --- | ---: | ---: | ---: | --- |
| footfall | naive | 36.943452 | 64.176306 | 15.367379 |  |
| footfall | seasonal_naive | 9.318452 | 14.080234 | 3.876199 |  |
| footfall | moving_average | 25.294642 | 42.585483 | 10.521820 |  |
| footfall | hist_gradient_boosting | 6.865613 | 10.626664 | 2.855891 | yes |
| medicine | naive | 19.988095 | 40.794943 | 15.543274 |  |
| medicine | seasonal_naive | 5.084524 | 9.147534 | 3.953861 |  |
| medicine | moving_average | 13.618197 | 26.920710 | 10.589872 |  |
| medicine | hist_gradient_boosting | 3.908288 | 6.836623 | 3.039189 | yes |
| admissions | naive | 2.065476 | 3.806323 | 15.133014 |  |
| admissions | seasonal_naive | 0.494048 | 0.883041 | 3.619712 |  |
| admissions | moving_average | 1.446429 | 2.535798 | 10.597470 |  |
| admissions | hist_gradient_boosting | 0.419906 | 0.676044 | 3.076504 | yes |

| Target / resource | 80% observed coverage | 95% observed coverage | Calibration paths |
| --- | ---: | ---: | ---: |
| footfall / footfall | 83.3333% | 96.1310% | 24 |
| medicine / AMX | 86.9048% | 97.0238% | 24 |
| medicine / IFA | 85.1190% | 95.2381% | 24 |
| medicine / IVF | 78.2738% | 94.6429% | 24 |
| medicine / ORS | 87.2024% | 95.5357% | 24 |
| medicine / PCM | 86.6071% | 97.3214% | 24 |
| admissions / admissions | 84.8214% | 97.0238% | 24 |

## Interpretation

Daily interval coverage is measured; nominal 80%/95% levels are not guarantees. Foreign nodes have small residual pools, correlated errors and several under-covered resources. Stock-out probabilities and cumulative interval calibration have not been validated against real-world outcomes. No poor comparison or coverage result is hidden. Read the [model card](model-card.md) for censoring, source vintage, chronology and assumptions.
