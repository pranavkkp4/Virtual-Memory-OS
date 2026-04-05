# Isolation Stability Baseline

Generated from `C:\Users\Pranav\Desktop\CU Denver\Operating Systems\Virtual Memory\results\baselines_20260404` with `8` repetitions per configuration.

Reproduce with:

```powershell
python scripts\run_isolation_baselines.py
```

## Run Recipe

- `pressure_pinned` via `pinned` cores=[2]: `--experiment pressure --repetitions 8`
- `trace_quiet` via `quiet`: `--experiment trace --trace-file workloads\traces\sample_trace.csv --repetitions 8`

## Stability Verdict

- Group count: `264`
- Stable groups (`cv` <= 0.05): `81`
- Review groups (`0.05` < `cv` <= 0.10): `39`
- Unstable groups (`cv` > 0.10): `144`
- Median `cv`: `0.128607`
- Mean `cv`: `0.1902`
- Max `cv`: `2.60219`

Verdict: The isolated baselines are noisy enough that slowdown should be treated cautiously.

## Profile Breakdown

| profile | groups | stable | review | unstable | median cv | mean cv | max cv |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pressure_pinned | 144 | 59 | 7 | 78 | 0.255621 | 0.222317 | 2.60219 |
| trace_quiet | 120 | 22 | 32 | 66 | 0.112416 | 0.151659 | 1.13884 |

## Sampled Groups

| profile | workload | algorithm | allocation | frames | pid | trials | mean ns | std ns | cv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 105 | 0 | 8 | 182037.5 | 2659.72 | 0.014611 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 105 | 1 | 8 | 186775.0 | 7283.2 | 0.038995 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 131 | 0 | 8 | 203512.5 | 61668.97 | 0.303023 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 131 | 1 | 8 | 208425.0 | 65865.42 | 0.316015 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 157 | 0 | 8 | 229525.0 | 65965.48 | 0.2874 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 157 | 1 | 8 | 226750.0 | 66397.1 | 0.292821 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 196 | 0 | 8 | 196962.5 | 44576.35 | 0.226319 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 196 | 1 | 8 | 183600.0 | 2651.15 | 0.01444 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 241 | 0 | 8 | 209900.0 | 69626.6 | 0.331713 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 241 | 1 | 8 | 212512.5 | 73421.92 | 0.345495 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 241 | 2 | 8 | 217425.0 | 72760.7 | 0.334647 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 241 | 3 | 8 | 215887.5 | 76405.77 | 0.353915 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 301 | 0 | 8 | 182475.0 | 1083.32 | 0.005937 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 301 | 1 | 8 | 182525.0 | 1827.37 | 0.010012 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 301 | 2 | 8 | 186312.5 | 2785.39 | 0.01495 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 301 | 3 | 8 | 188850.0 | 2127.37 | 0.011265 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 361 | 0 | 8 | 224962.5 | 86685.46 | 0.385333 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 361 | 1 | 8 | 225650.0 | 75424.61 | 0.334255 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 361 | 2 | 8 | 226962.5 | 77580.67 | 0.341822 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 361 | 3 | 8 | 233250.0 | 82727.0 | 0.354671 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 452 | 0 | 8 | 224937.5 | 77432.66 | 0.344241 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 452 | 1 | 8 | 228387.5 | 78747.94 | 0.3448 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 452 | 2 | 8 | 235400.0 | 88056.07 | 0.37407 |
| pressure_pinned | high_locality | FIFO | GlobalAllocation | 452 | 3 | 8 | 211850.0 | 62549.52 | 0.295254 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 105 | 0 | 8 | 197700.0 | 49011.95 | 0.247911 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 105 | 1 | 8 | 207462.5 | 67648.76 | 0.326077 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 131 | 0 | 8 | 181312.5 | 2433.36 | 0.013421 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 131 | 1 | 8 | 183925.0 | 1610.46 | 0.008756 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 157 | 0 | 8 | 185037.5 | 7359.72 | 0.039774 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 157 | 1 | 8 | 185000.0 | 2107.81 | 0.011394 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 196 | 0 | 8 | 181687.5 | 1984.54 | 0.010923 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 196 | 1 | 8 | 184537.5 | 1595.47 | 0.008646 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 241 | 0 | 8 | 214587.5 | 69561.72 | 0.324165 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 241 | 1 | 8 | 202200.0 | 52020.82 | 0.257274 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 241 | 2 | 8 | 209687.5 | 53253.69 | 0.253967 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 241 | 3 | 8 | 216137.5 | 52176.7 | 0.241405 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 301 | 0 | 8 | 180550.0 | 1405.09 | 0.007782 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 301 | 1 | 8 | 183062.5 | 1372.11 | 0.007495 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 301 | 2 | 8 | 187137.5 | 4860.32 | 0.025972 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 301 | 3 | 8 | 189337.5 | 3442.56 | 0.018182 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 361 | 0 | 8 | 265962.5 | 89039.52 | 0.334782 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 361 | 1 | 8 | 284387.5 | 82415.68 | 0.289801 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 361 | 2 | 8 | 289800.0 | 85539.95 | 0.295169 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 361 | 3 | 8 | 306187.5 | 83428.28 | 0.272474 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 452 | 0 | 8 | 259525.0 | 107200.46 | 0.413064 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 452 | 1 | 8 | 235225.0 | 79699.74 | 0.338823 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 452 | 2 | 8 | 234425.0 | 69974.01 | 0.298492 |
| pressure_pinned | high_locality | FIFO | LocalAllocation | 452 | 3 | 8 | 213300.0 | 62716.14 | 0.294028 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 105 | 0 | 8 | 299025.0 | 2686.34 | 0.008984 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 105 | 1 | 8 | 300262.5 | 1775.18 | 0.005912 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 131 | 0 | 8 | 300825.0 | 4011.32 | 0.013334 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 131 | 1 | 8 | 333312.5 | 86927.55 | 0.260799 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 157 | 0 | 8 | 297687.5 | 1983.82 | 0.006664 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 157 | 1 | 8 | 338675.0 | 108400.76 | 0.320073 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 196 | 0 | 8 | 341325.0 | 124005.78 | 0.363307 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 196 | 1 | 8 | 349637.5 | 132383.21 | 0.37863 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 241 | 0 | 8 | 306887.5 | 12799.6 | 0.041708 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 241 | 1 | 8 | 306112.5 | 16496.36 | 0.05389 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 241 | 2 | 8 | 308850.0 | 16806.97 | 0.054418 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 241 | 3 | 8 | 311200.0 | 5488.95 | 0.017638 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 301 | 0 | 8 | 308712.5 | 27607.37 | 0.089427 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 301 | 1 | 8 | 300125.0 | 2965.88 | 0.009882 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 301 | 2 | 8 | 305537.5 | 4028.8 | 0.013186 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 301 | 3 | 8 | 309637.5 | 2184.32 | 0.007054 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 361 | 0 | 8 | 358312.5 | 110807.55 | 0.309248 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 361 | 1 | 8 | 340537.5 | 105099.67 | 0.308629 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 361 | 2 | 8 | 389650.0 | 121460.72 | 0.311717 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 361 | 3 | 8 | 4414100.0 | 11486325.88 | 2.60219 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 452 | 0 | 8 | 311862.5 | 14047.26 | 0.045043 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 452 | 1 | 8 | 308062.5 | 7974.41 | 0.025886 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 452 | 2 | 8 | 312737.5 | 10071.02 | 0.032203 |
| pressure_pinned | high_locality | LRU | GlobalAllocation | 452 | 3 | 8 | 313650.0 | 5735.85 | 0.018287 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 105 | 0 | 8 | 308387.5 | 27278.32 | 0.088455 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 105 | 1 | 8 | 302225.0 | 3421.67 | 0.011322 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 131 | 0 | 8 | 299312.5 | 3737.62 | 0.012487 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 131 | 1 | 8 | 308175.0 | 23099.95 | 0.074957 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 157 | 0 | 8 | 298412.5 | 3437.79 | 0.01152 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 157 | 1 | 8 | 298600.0 | 2243.08 | 0.007512 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 196 | 0 | 8 | 345475.0 | 134110.4 | 0.388191 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 196 | 1 | 8 | 373700.0 | 131480.54 | 0.351834 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 241 | 0 | 8 | 369812.5 | 114566.46 | 0.309796 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 241 | 1 | 8 | 349200.0 | 98358.5 | 0.281668 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 241 | 2 | 8 | 412275.0 | 248443.28 | 0.602615 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 241 | 3 | 8 | 358650.0 | 101826.81 | 0.283917 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 301 | 0 | 8 | 317075.0 | 33786.76 | 0.106558 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 301 | 1 | 8 | 300262.5 | 2827.89 | 0.009418 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 301 | 2 | 8 | 305525.0 | 3640.94 | 0.011917 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 301 | 3 | 8 | 310825.0 | 5481.85 | 0.017636 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 361 | 0 | 8 | 409887.5 | 130754.9 | 0.319002 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 361 | 1 | 8 | 414100.0 | 140016.26 | 0.338122 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 361 | 2 | 8 | 439625.0 | 160292.85 | 0.364613 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 361 | 3 | 8 | 393562.5 | 125058.35 | 0.31776 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 452 | 0 | 8 | 348250.0 | 114328.67 | 0.328295 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 452 | 1 | 8 | 367800.0 | 127116.25 | 0.345612 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 452 | 2 | 8 | 349125.0 | 118016.46 | 0.338035 |
| pressure_pinned | high_locality | LRU | LocalAllocation | 452 | 3 | 8 | 351712.5 | 117852.02 | 0.335081 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 105 | 0 | 8 | 333362.5 | 119090.48 | 0.35724 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 105 | 1 | 8 | 350375.0 | 145751.55 | 0.415987 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 131 | 0 | 8 | 267350.0 | 6843.14 | 0.025596 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 131 | 1 | 8 | 272650.0 | 7928.43 | 0.029079 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 157 | 0 | 8 | 268225.0 | 4686.38 | 0.017472 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 157 | 1 | 8 | 286050.0 | 40974.17 | 0.143241 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 196 | 0 | 8 | 538300.0 | 175228.54 | 0.325522 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 196 | 1 | 8 | 825787.5 | 935302.94 | 1.132619 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 241 | 0 | 8 | 309712.5 | 110448.74 | 0.356617 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 241 | 1 | 8 | 307362.5 | 105058.89 | 0.341808 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 241 | 2 | 8 | 278100.0 | 4711.08 | 0.01694 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 241 | 3 | 8 | 295187.5 | 21549.37 | 0.073002 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 301 | 0 | 8 | 266537.5 | 3635.51 | 0.01364 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 301 | 1 | 8 | 274037.5 | 4207.46 | 0.015354 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 301 | 2 | 8 | 283525.0 | 7628.47 | 0.026906 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 301 | 3 | 8 | 288950.0 | 7721.58 | 0.026723 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 361 | 0 | 8 | 306875.0 | 102072.24 | 0.332618 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 361 | 1 | 8 | 305187.5 | 83980.18 | 0.275176 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 361 | 2 | 8 | 317387.5 | 103162.42 | 0.325036 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 361 | 3 | 8 | 324075.0 | 107391.83 | 0.33138 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 452 | 0 | 8 | 333875.0 | 126825.39 | 0.379859 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 452 | 1 | 8 | 349100.0 | 127012.61 | 0.363829 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 452 | 2 | 8 | 376187.5 | 124855.97 | 0.331898 |
| pressure_pinned | high_locality | WSClock | GlobalAllocation | 452 | 3 | 8 | 392462.5 | 148337.63 | 0.377966 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 105 | 0 | 8 | 266312.5 | 5146.83 | 0.019326 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 105 | 1 | 8 | 278387.5 | 19061.66 | 0.068472 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 131 | 0 | 8 | 313912.5 | 86516.84 | 0.275608 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 131 | 1 | 8 | 306875.0 | 96388.73 | 0.314098 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 157 | 0 | 8 | 269625.0 | 8000.13 | 0.029671 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 157 | 1 | 8 | 275487.5 | 8604.06 | 0.031232 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 196 | 0 | 8 | 339625.0 | 124715.41 | 0.367215 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 196 | 1 | 8 | 429012.5 | 243829.29 | 0.56835 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 241 | 0 | 8 | 263937.5 | 2921.32 | 0.011068 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 241 | 1 | 8 | 270200.0 | 2982.81 | 0.011039 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 241 | 2 | 8 | 277500.0 | 3392.01 | 0.012223 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 241 | 3 | 8 | 282262.5 | 3187.45 | 0.011292 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 301 | 0 | 8 | 266087.5 | 5167.6 | 0.019421 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 301 | 1 | 8 | 270075.0 | 3422.93 | 0.012674 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 301 | 2 | 8 | 276225.0 | 5404.69 | 0.019566 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 301 | 3 | 8 | 1637937.5 | 3821722.68 | 2.333253 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 361 | 0 | 8 | 267887.5 | 5438.34 | 0.020301 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 361 | 1 | 8 | 273700.0 | 9076.66 | 0.033163 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 361 | 2 | 8 | 281012.5 | 4944.68 | 0.017596 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 361 | 3 | 8 | 288500.0 | 7469.17 | 0.02589 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 452 | 0 | 8 | 323312.5 | 102816.78 | 0.318011 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 452 | 1 | 8 | 322012.5 | 91514.75 | 0.284196 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 452 | 2 | 8 | 313037.5 | 92774.72 | 0.296369 |
| pressure_pinned | high_locality | WSClock | LocalAllocation | 452 | 3 | 8 | 320312.5 | 98637.99 | 0.307943 |
| trace_quiet | sample_trace | FIFO | GlobalAllocation | 4 | 0 | 8 | 2562.5 | 512.52 | 0.200008 |
| trace_quiet | sample_trace | FIFO | GlobalAllocation | 4 | 1 | 8 | 2937.5 | 192.26 | 0.065451 |
| trace_quiet | sample_trace | FIFO | GlobalAllocation | 5 | 0 | 8 | 2987.5 | 633.44 | 0.212031 |
| trace_quiet | sample_trace | FIFO | GlobalAllocation | 5 | 1 | 8 | 3112.5 | 279.99 | 0.089956 |
| trace_quiet | sample_trace | FIFO | GlobalAllocation | 6 | 0 | 8 | 4887.5 | 5566.08 | 1.13884 |
| trace_quiet | sample_trace | FIFO | GlobalAllocation | 6 | 1 | 8 | 3300.0 | 991.39 | 0.300422 |
| trace_quiet | sample_trace | FIFO | GlobalAllocation | 8 | 0 | 8 | 3112.5 | 624.36 | 0.200597 |
| trace_quiet | sample_trace | FIFO | GlobalAllocation | 8 | 1 | 8 | 3125.0 | 243.49 | 0.077916 |
| trace_quiet | sample_trace | FIFO | LocalAllocation | 4 | 0 | 8 | 2425.0 | 128.17 | 0.052855 |
| trace_quiet | sample_trace | FIFO | LocalAllocation | 4 | 1 | 8 | 2750.0 | 92.58 | 0.033666 |
| trace_quiet | sample_trace | FIFO | LocalAllocation | 5 | 0 | 8 | 2412.5 | 294.9 | 0.122237 |
| trace_quiet | sample_trace | FIFO | LocalAllocation | 5 | 1 | 8 | 2700.0 | 75.59 | 0.027997 |
| trace_quiet | sample_trace | FIFO | LocalAllocation | 6 | 0 | 8 | 2325.0 | 175.25 | 0.075378 |
| trace_quiet | sample_trace | FIFO | LocalAllocation | 6 | 1 | 8 | 2775.0 | 148.8 | 0.053623 |
| trace_quiet | sample_trace | FIFO | LocalAllocation | 8 | 0 | 8 | 2387.5 | 241.65 | 0.101213 |
| trace_quiet | sample_trace | FIFO | LocalAllocation | 8 | 1 | 8 | 2725.0 | 138.87 | 0.050963 |
| trace_quiet | sample_trace | FIFO | ProportionalAllocation | 4 | 0 | 8 | 2900.0 | 858.57 | 0.296059 |
| trace_quiet | sample_trace | FIFO | ProportionalAllocation | 4 | 1 | 8 | 2900.0 | 232.99 | 0.080342 |
| trace_quiet | sample_trace | FIFO | ProportionalAllocation | 5 | 0 | 8 | 2725.0 | 690.24 | 0.253298 |
| trace_quiet | sample_trace | FIFO | ProportionalAllocation | 5 | 1 | 8 | 2887.5 | 470.37 | 0.162899 |
| trace_quiet | sample_trace | FIFO | ProportionalAllocation | 6 | 0 | 8 | 2425.0 | 249.28 | 0.102798 |
| trace_quiet | sample_trace | FIFO | ProportionalAllocation | 6 | 1 | 8 | 2687.5 | 64.09 | 0.023846 |
| trace_quiet | sample_trace | FIFO | ProportionalAllocation | 8 | 0 | 8 | 2450.0 | 333.81 | 0.136249 |
| trace_quiet | sample_trace | FIFO | ProportionalAllocation | 8 | 1 | 8 | 2887.5 | 335.68 | 0.116252 |
| trace_quiet | sample_trace | LRU | GlobalAllocation | 4 | 0 | 8 | 3662.5 | 1060.91 | 0.289669 |
| trace_quiet | sample_trace | LRU | GlobalAllocation | 4 | 1 | 8 | 3212.5 | 299.7 | 0.093293 |
| trace_quiet | sample_trace | LRU | GlobalAllocation | 5 | 0 | 8 | 3187.5 | 637.94 | 0.200137 |
| trace_quiet | sample_trace | LRU | GlobalAllocation | 5 | 1 | 8 | 3075.0 | 212.13 | 0.068986 |
| trace_quiet | sample_trace | LRU | GlobalAllocation | 6 | 0 | 8 | 3075.0 | 638.64 | 0.207687 |
| trace_quiet | sample_trace | LRU | GlobalAllocation | 6 | 1 | 8 | 3262.5 | 453.36 | 0.138961 |
| trace_quiet | sample_trace | LRU | GlobalAllocation | 8 | 0 | 8 | 3112.5 | 653.43 | 0.209936 |
| trace_quiet | sample_trace | LRU | GlobalAllocation | 8 | 1 | 8 | 3225.0 | 416.62 | 0.129184 |
| trace_quiet | sample_trace | LRU | LocalAllocation | 4 | 0 | 8 | 3337.5 | 910.16 | 0.272707 |
| trace_quiet | sample_trace | LRU | LocalAllocation | 4 | 1 | 8 | 3362.5 | 694.75 | 0.206617 |
| trace_quiet | sample_trace | LRU | LocalAllocation | 5 | 0 | 8 | 2537.5 | 130.25 | 0.051329 |
| trace_quiet | sample_trace | LRU | LocalAllocation | 5 | 1 | 8 | 2850.0 | 389.14 | 0.13654 |
| trace_quiet | sample_trace | LRU | LocalAllocation | 6 | 0 | 8 | 2487.5 | 180.77 | 0.072672 |
| trace_quiet | sample_trace | LRU | LocalAllocation | 6 | 1 | 8 | 2725.0 | 70.71 | 0.025949 |
| trace_quiet | sample_trace | LRU | LocalAllocation | 8 | 0 | 8 | 2562.5 | 168.5 | 0.065757 |
| trace_quiet | sample_trace | LRU | LocalAllocation | 8 | 1 | 8 | 2737.5 | 118.77 | 0.043388 |
| trace_quiet | sample_trace | LRU | ProportionalAllocation | 4 | 0 | 8 | 4400.0 | 200.0 | 0.045455 |
| trace_quiet | sample_trace | LRU | ProportionalAllocation | 4 | 1 | 8 | 4950.0 | 92.58 | 0.018703 |
| trace_quiet | sample_trace | LRU | ProportionalAllocation | 5 | 0 | 8 | 2650.0 | 437.53 | 0.165104 |
| trace_quiet | sample_trace | LRU | ProportionalAllocation | 5 | 1 | 8 | 2725.0 | 46.29 | 0.016988 |
| trace_quiet | sample_trace | LRU | ProportionalAllocation | 6 | 0 | 8 | 2587.5 | 164.21 | 0.063462 |
| trace_quiet | sample_trace | LRU | ProportionalAllocation | 6 | 1 | 8 | 2725.0 | 138.87 | 0.050963 |
| trace_quiet | sample_trace | LRU | ProportionalAllocation | 8 | 0 | 8 | 3200.0 | 965.11 | 0.301595 |
| trace_quiet | sample_trace | LRU | ProportionalAllocation | 8 | 1 | 8 | 3512.5 | 1037.08 | 0.295254 |
| trace_quiet | sample_trace | NRU | GlobalAllocation | 4 | 0 | 8 | 5237.5 | 757.7 | 0.144668 |
| trace_quiet | sample_trace | NRU | GlobalAllocation | 4 | 1 | 8 | 5437.5 | 495.52 | 0.091129 |
| trace_quiet | sample_trace | NRU | GlobalAllocation | 5 | 0 | 8 | 3312.5 | 791.81 | 0.239037 |
| trace_quiet | sample_trace | NRU | GlobalAllocation | 5 | 1 | 8 | 2950.0 | 261.86 | 0.088767 |
| trace_quiet | sample_trace | NRU | GlobalAllocation | 6 | 0 | 8 | 3062.5 | 573.06 | 0.18712 |
| trace_quiet | sample_trace | NRU | GlobalAllocation | 6 | 1 | 8 | 3150.0 | 609.45 | 0.193476 |
| trace_quiet | sample_trace | NRU | GlobalAllocation | 8 | 0 | 8 | 3750.0 | 1356.47 | 0.361724 |
| trace_quiet | sample_trace | NRU | GlobalAllocation | 8 | 1 | 8 | 3725.0 | 1237.22 | 0.33214 |
| trace_quiet | sample_trace | NRU | LocalAllocation | 4 | 0 | 8 | 2500.0 | 169.03 | 0.067612 |
| trace_quiet | sample_trace | NRU | LocalAllocation | 4 | 1 | 8 | 2687.5 | 344.08 | 0.128031 |
| trace_quiet | sample_trace | NRU | LocalAllocation | 5 | 0 | 8 | 3825.0 | 433.42 | 0.113314 |
| trace_quiet | sample_trace | NRU | LocalAllocation | 5 | 1 | 8 | 4500.0 | 481.07 | 0.106904 |
| trace_quiet | sample_trace | NRU | LocalAllocation | 6 | 0 | 8 | 2400.0 | 130.93 | 0.054554 |
| trace_quiet | sample_trace | NRU | LocalAllocation | 6 | 1 | 8 | 2625.0 | 103.51 | 0.039432 |
| trace_quiet | sample_trace | NRU | LocalAllocation | 8 | 0 | 8 | 2412.5 | 180.77 | 0.074931 |
| trace_quiet | sample_trace | NRU | LocalAllocation | 8 | 1 | 8 | 2562.5 | 74.4 | 0.029035 |
| trace_quiet | sample_trace | NRU | ProportionalAllocation | 4 | 0 | 8 | 2625.0 | 762.98 | 0.29066 |
| trace_quiet | sample_trace | NRU | ProportionalAllocation | 4 | 1 | 8 | 2825.0 | 645.31 | 0.228429 |
| trace_quiet | sample_trace | NRU | ProportionalAllocation | 5 | 0 | 8 | 2400.0 | 261.86 | 0.109109 |
| trace_quiet | sample_trace | NRU | ProportionalAllocation | 5 | 1 | 8 | 2725.0 | 446.41 | 0.163822 |
| trace_quiet | sample_trace | NRU | ProportionalAllocation | 6 | 0 | 8 | 2387.5 | 112.6 | 0.047162 |
| trace_quiet | sample_trace | NRU | ProportionalAllocation | 6 | 1 | 8 | 2612.5 | 83.45 | 0.031943 |
| trace_quiet | sample_trace | NRU | ProportionalAllocation | 8 | 0 | 8 | 2412.5 | 83.45 | 0.034592 |
| trace_quiet | sample_trace | NRU | ProportionalAllocation | 8 | 1 | 8 | 2587.5 | 64.09 | 0.024768 |
| trace_quiet | sample_trace | SecondChance | GlobalAllocation | 4 | 0 | 8 | 5425.0 | 839.64 | 0.154773 |
| trace_quiet | sample_trace | SecondChance | GlobalAllocation | 4 | 1 | 8 | 5475.0 | 430.12 | 0.07856 |
| trace_quiet | sample_trace | SecondChance | GlobalAllocation | 5 | 0 | 8 | 3275.0 | 846.42 | 0.258449 |
| trace_quiet | sample_trace | SecondChance | GlobalAllocation | 5 | 1 | 8 | 2987.5 | 279.99 | 0.09372 |
| trace_quiet | sample_trace | SecondChance | GlobalAllocation | 6 | 0 | 8 | 3000.0 | 573.21 | 0.191071 |
| trace_quiet | sample_trace | SecondChance | GlobalAllocation | 6 | 1 | 8 | 2950.0 | 256.35 | 0.086898 |
| trace_quiet | sample_trace | SecondChance | GlobalAllocation | 8 | 0 | 8 | 3237.5 | 750.12 | 0.231697 |
| trace_quiet | sample_trace | SecondChance | GlobalAllocation | 8 | 1 | 8 | 3200.0 | 690.76 | 0.215861 |
| trace_quiet | sample_trace | SecondChance | LocalAllocation | 4 | 0 | 8 | 4412.5 | 348.21 | 0.078914 |
| trace_quiet | sample_trace | SecondChance | LocalAllocation | 4 | 1 | 8 | 4875.0 | 103.51 | 0.021233 |
| trace_quiet | sample_trace | SecondChance | LocalAllocation | 5 | 0 | 8 | 3525.0 | 1149.84 | 0.326197 |
| trace_quiet | sample_trace | SecondChance | LocalAllocation | 5 | 1 | 8 | 3562.5 | 989.86 | 0.277855 |
| trace_quiet | sample_trace | SecondChance | LocalAllocation | 6 | 0 | 8 | 2425.0 | 249.28 | 0.102798 |
| trace_quiet | sample_trace | SecondChance | LocalAllocation | 6 | 1 | 8 | 2650.0 | 75.59 | 0.028526 |
| trace_quiet | sample_trace | SecondChance | LocalAllocation | 8 | 0 | 8 | 2575.0 | 459.04 | 0.178267 |
| trace_quiet | sample_trace | SecondChance | LocalAllocation | 8 | 1 | 8 | 2600.0 | 53.45 | 0.020559 |
| trace_quiet | sample_trace | SecondChance | ProportionalAllocation | 4 | 0 | 8 | 2787.5 | 1026.0 | 0.368072 |
| trace_quiet | sample_trace | SecondChance | ProportionalAllocation | 4 | 1 | 8 | 3187.5 | 1165.5 | 0.365647 |
| trace_quiet | sample_trace | SecondChance | ProportionalAllocation | 5 | 0 | 8 | 2412.5 | 180.77 | 0.074931 |
| trace_quiet | sample_trace | SecondChance | ProportionalAllocation | 5 | 1 | 8 | 2687.5 | 299.7 | 0.111517 |
| trace_quiet | sample_trace | SecondChance | ProportionalAllocation | 6 | 0 | 8 | 2775.0 | 786.95 | 0.283585 |
| trace_quiet | sample_trace | SecondChance | ProportionalAllocation | 6 | 1 | 8 | 2937.5 | 757.7 | 0.25794 |
| trace_quiet | sample_trace | SecondChance | ProportionalAllocation | 8 | 0 | 8 | 2450.0 | 141.42 | 0.057723 |
| trace_quiet | sample_trace | SecondChance | ProportionalAllocation | 8 | 1 | 8 | 2725.0 | 328.42 | 0.12052 |
| trace_quiet | sample_trace | WSClock | GlobalAllocation | 4 | 0 | 8 | 4075.0 | 1902.44 | 0.466857 |
| trace_quiet | sample_trace | WSClock | GlobalAllocation | 4 | 1 | 8 | 3975.0 | 1696.85 | 0.426879 |
| trace_quiet | sample_trace | WSClock | GlobalAllocation | 5 | 0 | 8 | 3037.5 | 627.78 | 0.206676 |
| trace_quiet | sample_trace | WSClock | GlobalAllocation | 5 | 1 | 8 | 2950.0 | 256.35 | 0.086898 |
| trace_quiet | sample_trace | WSClock | GlobalAllocation | 6 | 0 | 8 | 5337.5 | 1313.6 | 0.246107 |
| trace_quiet | sample_trace | WSClock | GlobalAllocation | 6 | 1 | 8 | 5200.0 | 801.78 | 0.154189 |
| trace_quiet | sample_trace | WSClock | GlobalAllocation | 8 | 0 | 8 | 3025.0 | 611.2 | 0.202051 |
| trace_quiet | sample_trace | WSClock | GlobalAllocation | 8 | 1 | 8 | 3100.0 | 440.78 | 0.142187 |
| trace_quiet | sample_trace | WSClock | LocalAllocation | 4 | 0 | 8 | 3700.0 | 701.02 | 0.189465 |
| trace_quiet | sample_trace | WSClock | LocalAllocation | 4 | 1 | 8 | 4112.5 | 883.88 | 0.214926 |
| trace_quiet | sample_trace | WSClock | LocalAllocation | 5 | 0 | 8 | 2425.0 | 198.21 | 0.081735 |
| trace_quiet | sample_trace | WSClock | LocalAllocation | 5 | 1 | 8 | 2625.0 | 128.17 | 0.048828 |
| trace_quiet | sample_trace | WSClock | LocalAllocation | 6 | 0 | 8 | 2725.0 | 658.46 | 0.241637 |
| trace_quiet | sample_trace | WSClock | LocalAllocation | 6 | 1 | 8 | 2937.5 | 641.29 | 0.218311 |
| trace_quiet | sample_trace | WSClock | LocalAllocation | 8 | 0 | 8 | 2462.5 | 184.68 | 0.074997 |
| trace_quiet | sample_trace | WSClock | LocalAllocation | 8 | 1 | 8 | 2650.0 | 75.59 | 0.028526 |
| trace_quiet | sample_trace | WSClock | ProportionalAllocation | 4 | 0 | 8 | 2412.5 | 83.45 | 0.034592 |
| trace_quiet | sample_trace | WSClock | ProportionalAllocation | 4 | 1 | 8 | 2662.5 | 118.77 | 0.04461 |
| trace_quiet | sample_trace | WSClock | ProportionalAllocation | 5 | 0 | 8 | 2437.5 | 106.07 | 0.043514 |
| trace_quiet | sample_trace | WSClock | ProportionalAllocation | 5 | 1 | 8 | 3112.5 | 1220.58 | 0.392155 |
| trace_quiet | sample_trace | WSClock | ProportionalAllocation | 6 | 0 | 8 | 2450.0 | 169.03 | 0.068992 |
| trace_quiet | sample_trace | WSClock | ProportionalAllocation | 6 | 1 | 8 | 2650.0 | 192.72 | 0.072726 |
| trace_quiet | sample_trace | WSClock | ProportionalAllocation | 8 | 0 | 8 | 2537.5 | 373.93 | 0.14736 |
| trace_quiet | sample_trace | WSClock | ProportionalAllocation | 8 | 1 | 8 | 2612.5 | 135.62 | 0.051912 |
