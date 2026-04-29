# Example Result Table

| workload | kind | lowest_page_faults | lowest_page_faults_value | lowest_worst_slowdown | lowest_worst_slowdown_value | highest_jains_index | highest_jains_index_value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_locality | synthetic | FIFO + GlobalAllocation | 144.0 | NRU + ProportionalAllocation | 1.5105045169415918 | SecondChance + LocalAllocation | 0.9999743368121583 |
| mixed | synthetic | FIFO + GlobalAllocation | 202.7 | NRU + LocalAllocation | 1.5054145663457728 | FIFO + LocalAllocation | 0.999876815669362 |
| streaming | synthetic | FIFO + GlobalAllocation | 340.0 | NRU + LocalAllocation | 1.4488456926827216 | LRU + ProportionalAllocation | 0.9999084191255865 |
| thrashing | synthetic | FIFO + GlobalAllocation | 204.0 | NRU + ProportionalAllocation | 1.5056973070379605 | FIFO + LocalAllocation | 0.9998723171530541 |
| trace: report_locality_heavy | trace | FIFO + GlobalAllocation | 4.0 | FIFO + ProportionalAllocation | 1.078230664609975 | NRU + GlobalAllocation | 0.9986657435237646 |
| trace: report_mixed_heterogeneous | trace | FIFO + GlobalAllocation | 11.0 | FIFO + ProportionalAllocation | 0.963006721006721 | SecondChance + GlobalAllocation | 0.9984581996899495 |
| trace: report_streaming_sequential | trace | FIFO + GlobalAllocation | 16.0 | FIFO + ProportionalAllocation | 1.0486227173851066 | SecondChance + GlobalAllocation | 0.9996502922438892 |
| trace: report_thrashing_pressure | trace | FIFO + GlobalAllocation | 10.0 | FIFO + ProportionalAllocation | 1.0739200295778497 | WSClock + LocalAllocation | 0.9996323556628897 |
| trace: sample_trace | trace | FIFO + GlobalAllocation | 5.0 | FIFO + ProportionalAllocation | 0.934171277997365 | LRU + LocalAllocation | 0.9978053643588917 |
