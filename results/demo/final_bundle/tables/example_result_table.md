# Example Result Table

| workload | kind | lowest_page_faults | lowest_page_faults_value | lowest_worst_slowdown | lowest_worst_slowdown_value | highest_jains_index | highest_jains_index_value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_locality | synthetic | FIFO + GlobalAllocation | 144.0 | LRU + LocalAllocation | 1.264754004443954 | SecondChance + LocalAllocation | 0.9999743368121583 |
| trace: sample_trace | trace | FIFO + GlobalAllocation | 5.0 | FIFO + LocalAllocation | 0.8571428571428572 | SecondChance + GlobalAllocation | 0.9999360815520008 |
| mixed | synthetic | FIFO + GlobalAllocation | 340.5 | LRU + ProportionalAllocation | 1.6548332137733142 | LRU + ProportionalAllocation | 0.999226757176557 |
