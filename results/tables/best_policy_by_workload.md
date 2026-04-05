| workload | kind | lowest_page_faults | lowest_page_faults_value | lowest_worst_slowdown | lowest_worst_slowdown_value | highest_jains_index | highest_jains_index_value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_locality | synthetic | FIFO + GlobalAllocation | 144 | NRU + ProportionalAllocation | 1.511 | SecondChance + LocalAllocation | 1 |
| mixed | synthetic | FIFO + GlobalAllocation | 202.7 | NRU + LocalAllocation | 1.505 | FIFO + LocalAllocation | 0.9999 |
| streaming | synthetic | FIFO + GlobalAllocation | 340 | NRU + LocalAllocation | 1.449 | LRU + ProportionalAllocation | 0.9999 |
| thrashing | synthetic | FIFO + GlobalAllocation | 204 | NRU + ProportionalAllocation | 1.506 | FIFO + LocalAllocation | 0.9999 |
| trace: report_locality_heavy | trace | FIFO + GlobalAllocation | 4 | FIFO + ProportionalAllocation | 1.078 | NRU + GlobalAllocation | 0.9987 |
| trace: report_mixed_heterogeneous | trace | FIFO + GlobalAllocation | 11 | FIFO + ProportionalAllocation | 0.963 | SecondChance + GlobalAllocation | 0.9985 |
| trace: report_streaming_sequential | trace | FIFO + GlobalAllocation | 16 | FIFO + ProportionalAllocation | 1.049 | SecondChance + GlobalAllocation | 0.9997 |
| trace: report_thrashing_pressure | trace | FIFO + GlobalAllocation | 10 | FIFO + ProportionalAllocation | 1.074 | WSClock + LocalAllocation | 0.9996 |
| trace: sample_trace | trace | FIFO + GlobalAllocation | 5 | FIFO + ProportionalAllocation | 0.9342 | LRU + LocalAllocation | 0.9978 |
