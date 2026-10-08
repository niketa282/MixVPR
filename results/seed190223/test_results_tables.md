# Effect of geometric augmentation on test recall

MixVPR (ResNet-50), trained on GSV-Cities for 50 epochs, single seed (190223); best checkpoint chosen on Pitts30k-val R@1.
Values are Recall@K (%). The number in brackets is the change from the no-augmentation baseline (`none`), in percentage points. Bold marks the best value in each column.

## Pitts30k-test

10,000 database images, 6,816 queries.

| Condition | Dataset | R@1 | R@5 | R@10 |
|---|---|---:|---:|---:|
| none | Pitts30k-test | 90.38 | 95.44 | 96.30 |
| crop | Pitts30k-test | 90.23 (-0.15) | 95.26 (-0.18) | 96.45 (+0.15) |
| perspective | Pitts30k-test | **90.93 (+0.55)** | **95.80 (+0.36)** | **96.80 (+0.50)** |
| rotate | Pitts30k-test | 90.83 (+0.45) | 95.44 (+0.00) | 96.73 (+0.43) |
| translate | Pitts30k-test | 90.57 (+0.19) | 95.13 (-0.31) | 96.17 (-0.13) |
| shear | Pitts30k-test | 90.70 (+0.32) | 95.60 (+0.16) | 96.52 (+0.22) |

## Nordland (summer database, winter queries)

27,592 database images, 27,592 queries.

| Condition | Dataset | R@1 | R@5 | R@10 |
|---|---|---:|---:|---:|
| none | Nordland | 69.55 | 82.21 | 86.36 |
| crop | Nordland | 74.16 (+4.61) | 85.04 (+2.83) | 88.75 (+2.39) |
| perspective | Nordland | **77.34 (+7.79)** | **87.28 (+5.07)** | **90.47 (+4.11)** |
| rotate | Nordland | 70.46 (+0.91) | 82.03 (-0.18) | 86.28 (-0.08) |
| translate | Nordland | 73.07 (+3.52) | 84.60 (+2.39) | 88.39 (+2.03) |
| shear | Nordland | 72.23 (+2.68) | 83.60 (+1.39) | 87.46 (+1.10) |

## SVOX (all queries)

17,166 database images, 14,278 queries.

| Condition | Dataset | R@1 | R@5 | R@10 |
|---|---|---:|---:|---:|
| none | SVOX | 97.44 | 98.66 | 98.90 |
| crop | SVOX | 97.42 (-0.02) | 98.73 (+0.07) | 99.07 (+0.17) |
| perspective | SVOX | 97.26 (-0.18) | 98.59 (-0.07) | 98.91 (+0.01) |
| rotate | SVOX | 97.34 (-0.10) | 98.67 (+0.01) | 98.92 (+0.02) |
| translate | SVOX | **97.46 (+0.02)** | 98.74 (+0.08) | 98.99 (+0.09) |
| shear | SVOX | 97.32 (-0.12) | **98.78 (+0.12)** | **99.09 (+0.19)** |

## SVOX Night

17,166 database images, 823 queries.

| Condition | Dataset | R@1 | R@5 | R@10 |
|---|---|---:|---:|---:|
| none | SVOX Night | 13.12 | 26.73 | 34.39 |
| crop | SVOX Night | 15.19 (+2.07) | 27.70 (+0.97) | 32.93 (-1.46) |
| perspective | SVOX Night | 19.56 (+6.44) | 30.62 (+3.89) | 36.45 (+2.06) |
| rotate | SVOX Night | **22.72 (+9.60)** | **37.18 (+10.45)** | **46.90 (+12.51)** |
| translate | SVOX Night | 17.13 (+4.01) | 29.53 (+2.80) | 38.27 (+3.88) |
| shear | SVOX Night | 19.81 (+6.69) | 31.59 (+4.86) | 40.83 (+6.44) |

## SVOX Overcast

17,166 database images, 872 queries.

| Condition | Dataset | R@1 | R@5 | R@10 |
|---|---|---:|---:|---:|
| none | SVOX Overcast | 95.18 | 98.17 | **98.62** |
| crop | SVOX Overcast | 95.64 (+0.46) | 98.05 (-0.12) | 98.17 (-0.45) |
| perspective | SVOX Overcast | 94.61 (-0.57) | 97.94 (-0.23) | 98.05 (-0.57) |
| rotate | SVOX Overcast | 95.18 (+0.00) | 97.59 (-0.58) | 98.05 (-0.57) |
| translate | SVOX Overcast | 95.53 (+0.35) | **98.39 (+0.22)** | **98.62 (+0.00)** |
| shear | SVOX Overcast | **96.10 (+0.92)** | **98.39 (+0.22)** | 98.51 (-0.11) |

## SVOX Rain

17,166 database images, 937 queries.

| Condition | Dataset | R@1 | R@5 | R@10 |
|---|---|---:|---:|---:|
| none | SVOX Rain | 88.69 | 95.09 | 96.58 |
| crop | SVOX Rain | 87.73 (-0.96) | 94.34 (-0.75) | 95.84 (-0.74) |
| perspective | SVOX Rain | 87.83 (-0.86) | 94.34 (-0.75) | 95.84 (-0.74) |
| rotate | SVOX Rain | 87.09 (-1.60) | 94.45 (-0.64) | 95.62 (-0.96) |
| translate | SVOX Rain | **89.11 (+0.42)** | **95.73 (+0.64)** | **96.69 (+0.11)** |
| shear | SVOX Rain | 88.26 (-0.43) | 95.09 (+0.00) | 96.48 (-0.10) |

## SVOX Snow

17,166 database images, 870 queries.

| Condition | Dataset | R@1 | R@5 | R@10 |
|---|---|---:|---:|---:|
| none | SVOX Snow | 94.48 | 98.05 | 98.39 |
| crop | SVOX Snow | 94.94 (+0.46) | 98.39 (+0.34) | 98.62 (+0.23) |
| perspective | SVOX Snow | 94.48 (+0.00) | 98.05 (+0.00) | 98.51 (+0.12) |
| rotate | SVOX Snow | 94.83 (+0.35) | 98.39 (+0.34) | 98.51 (+0.12) |
| translate | SVOX Snow | 95.17 (+0.69) | 98.16 (+0.11) | 98.28 (-0.11) |
| shear | SVOX Snow | **95.86 (+1.38)** | **98.51 (+0.46)** | **98.97 (+0.58)** |

## SVOX Sun

17,166 database images, 854 queries.

| Condition | Dataset | R@1 | R@5 | R@10 |
|---|---|---:|---:|---:|
| none | SVOX Sun | 79.27 | 87.12 | 90.16 |
| crop | SVOX Sun | 77.05 (-2.22) | 88.64 (+1.52) | 91.57 (+1.41) |
| perspective | SVOX Sun | 79.86 (+0.59) | 88.99 (+1.87) | 90.98 (+0.82) |
| rotate | SVOX Sun | 78.92 (-0.35) | 87.82 (+0.70) | 90.75 (+0.59) |
| translate | SVOX Sun | **80.44 (+1.17)** | **90.52 (+3.40)** | **93.21 (+3.05)** |
| shear | SVOX Sun | 78.22 (-1.05) | 89.11 (+1.99) | 91.57 (+1.41) |
