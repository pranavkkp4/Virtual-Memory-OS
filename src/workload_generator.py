"""
Workload Generator for Virtual Memory Experiments
=================================================

Generates synthetic memory access traces and processes real traces.
Supports various workload types:
1. High-locality workloads (stable working sets)
2. Streaming workloads (sequential access)
3. Random workloads (no locality)
4. Mixed workloads (combination of patterns)
5. Thrashing-inducing workloads

References:
- Denning (1968): The working set model for program behavior
"""

import random
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import json


class WorkloadType(Enum):
    """Types of memory access patterns."""
    HIGH_LOCALITY = "high_locality"      # Stable working set
    STREAMING = "streaming"               # Sequential access
    RANDOM = "random"                     # No locality
    MIXED = "mixed"                       # Combination
    LOOP = "loop"                         # Repeated loop pattern
    THRASHING = "thrashing"               # Causes thrashing


@dataclass
class WorkloadConfig:
    """Configuration for workload generation."""
    workload_type: WorkloadType
    num_pages: int                    # Virtual address space size
    num_accesses: int                 # Total memory accesses
    working_set_size: int = 0         # Size of working set (for locality)
    locality_probability: float = 0.9  # Probability of accessing working set
    sequential_probability: float = 0.8  # For streaming workloads
    loop_iterations: int = 10         # For loop workloads
    seed: Optional[int] = None


class WorkloadGenerator:
    """Generator for synthetic memory access traces."""
    
    def __init__(self, config: WorkloadConfig):
        if config.num_pages <= 0:
            raise ValueError("num_pages must be greater than zero")
        if config.num_accesses < 0:
            raise ValueError("num_accesses must be non-negative")
        self.config = config
        self.rng = random.Random(config.seed)
    
    def generate(self) -> List[Tuple[int, int, bool]]:
        """
        Generate memory access trace.
        
        Returns:
            List of (page_id, process_id, is_write) tuples
        """
        generators = {
            WorkloadType.HIGH_LOCALITY: self._generate_high_locality,
            WorkloadType.STREAMING: self._generate_streaming,
            WorkloadType.RANDOM: self._generate_random,
            WorkloadType.MIXED: self._generate_mixed,
            WorkloadType.LOOP: self._generate_loop,
            WorkloadType.THRASHING: self._generate_thrashing
        }
        
        generator = generators.get(self.config.workload_type)
        if generator is None:
            raise ValueError(f"Unknown workload type: {self.config.workload_type}")
        
        return generator()
    
    def _generate_high_locality(self) -> List[Tuple[int, int, bool]]:
        """
        Generate workload with high temporal locality.
        
        Most accesses are to a small working set of pages.
        """
        accesses = []
        wss = self.config.working_set_size or max(10, self.config.num_pages // 10)
        wss = max(1, min(wss, self.config.num_pages))
        
        # Define working set
        working_set = list(range(wss))
        other_pages = list(range(wss, self.config.num_pages))
        
        for _ in range(self.config.num_accesses):
            if self.rng.random() < self.config.locality_probability:
                # Access working set
                page_id = self.rng.choice(working_set)
            else:
                # Access outside working set
                page_id = self.rng.choice(other_pages) if other_pages else self.rng.choice(working_set)
            
            is_write = self.rng.random() < 0.3  # 30% writes
            accesses.append((page_id, 0, is_write))
        
        return accesses
    
    def _generate_streaming(self) -> List[Tuple[int, int, bool]]:
        """
        Generate streaming workload with sequential access pattern.
        
        Simulates processing large arrays or files sequentially.
        """
        accesses = []
        current_page = 0
        
        for _ in range(self.config.num_accesses):
            if self.rng.random() < self.config.sequential_probability:
                # Sequential access
                current_page = (current_page + 1) % self.config.num_pages
            else:
                # Random jump
                current_page = self.rng.randint(0, self.config.num_pages - 1)
            
            is_write = self.rng.random() < 0.2  # 20% writes
            accesses.append((current_page, 0, is_write))
        
        return accesses
    
    def _generate_random(self) -> List[Tuple[int, int, bool]]:
        """
        Generate random workload with no locality.
        
        Every page has equal probability of being accessed.
        """
        accesses = []
        
        for _ in range(self.config.num_accesses):
            page_id = self.rng.randint(0, self.config.num_pages - 1)
            is_write = self.rng.random() < 0.3
            accesses.append((page_id, 0, is_write))
        
        return accesses
    
    def _generate_mixed(self) -> List[Tuple[int, int, bool]]:
        """
        Generate mixed workload combining multiple patterns.
        
        Alternates between different access patterns.
        """
        accesses = []
        phase_lengths = [self.config.num_accesses // 4] * 4
        for index in range(self.config.num_accesses % 4):
            phase_lengths[index] += 1
        
        # Phase 1: High locality
        self.config.workload_type = WorkloadType.HIGH_LOCALITY
        accesses.extend(self._generate_high_locality()[:phase_lengths[0]])
        
        # Phase 2: Streaming
        self.config.workload_type = WorkloadType.STREAMING
        accesses.extend(self._generate_streaming()[:phase_lengths[1]])
        
        # Phase 3: Random
        self.config.workload_type = WorkloadType.RANDOM
        accesses.extend(self._generate_random()[:phase_lengths[2]])
        
        # Phase 4: Loop
        self.config.workload_type = WorkloadType.LOOP
        accesses.extend(self._generate_loop()[:phase_lengths[3]])
        
        # Restore original type
        self.config.workload_type = WorkloadType.MIXED
        
        return accesses
    
    def _generate_loop(self) -> List[Tuple[int, int, bool]]:
        """
        Generate loop workload with repeated iteration.
        
        Simulates program loops accessing same pages repeatedly.
        """
        accesses = []
        loop_size = min(self.config.num_pages, 
                       max(5, self.config.num_pages // self.config.loop_iterations))
        
        for _ in range(self.config.num_accesses // loop_size):
            for page_id in range(loop_size):
                is_write = self.rng.random() < 0.3
                accesses.append((page_id, 0, is_write))
        
        # Pad to reach num_accesses
        while len(accesses) < self.config.num_accesses:
            accesses.append((self.rng.randint(0, loop_size - 1), 0, False))
        
        return accesses[:self.config.num_accesses]
    
    def _generate_thrashing(self) -> List[Tuple[int, int, bool]]:
        """
        Generate thrashing-inducing workload.
        
        Creates access pattern that causes excessive page faults
        when memory is limited.
        """
        accesses = []
        # Access more unique pages than typical memory can hold
        active_pages = min(self.config.num_pages, 
                          int(self.config.num_pages * 0.8))
        
        for i in range(self.config.num_accesses):
            # Rapidly switch between large number of pages
            page_id = (i * 7) % active_pages  # Stride pattern
            is_write = self.rng.random() < 0.3
            accesses.append((page_id, 0, is_write))
        
        return accesses
    
    def estimate_working_set_size(self, window_size: int = 1000) -> int:
        """
        Estimate working set size using a sliding window.
        
        Args:
            window_size: Window size for WSS calculation
        
        Returns:
            Estimated working set size
        """
        accesses = self.generate()
        
        if len(accesses) <= window_size:
            return len(set(a[0] for a in accesses))
        
        max_wss = 0
        for i in range(len(accesses) - window_size):
            window = accesses[i:i + window_size]
            unique_pages = len(set(a[0] for a in window))
            max_wss = max(max_wss, unique_pages)
        
        return max_wss


class MultiProcessWorkloadGenerator:
    """Generator for multi-process workloads."""
    
    def __init__(self, process_configs: Dict[int, WorkloadConfig]):
        """
        Args:
            process_configs: Dictionary mapping process_id to WorkloadConfig
        """
        self.process_configs = process_configs
        self.generators = {
            pid: WorkloadGenerator(config) 
            for pid, config in process_configs.items()
        }
        seed_material = tuple(
            (pid, config.seed)
            for pid, config in sorted(process_configs.items())
            if config.seed is not None
        )
        self.rng = random.Random(repr(seed_material)) if seed_material else random.Random()
        self.last_process_traces: Dict[int, List[Tuple[int, int, bool]]] = {}
        self.last_trace: List[Tuple[int, int, bool]] = []
    
    def generate(self, interleave: str = 'random') -> List[Tuple[int, int, bool]]:
        """
        Generate interleaved multi-process trace.
        
        Args:
            interleave: 'random', 'round_robin', or 'batch'
        
        Returns:
            List of (page_id, process_id, is_write) tuples
        """
        # Generate traces for each process
        process_traces = {
            pid: gen.generate() 
            for pid, gen in self.generators.items()
        }
        
        # Update process IDs in traces
        for pid, trace in process_traces.items():
            process_traces[pid] = [(page_id, pid, is_write) 
                                   for page_id, _, is_write in trace]
        self.last_process_traces = {
            pid: list(trace) for pid, trace in process_traces.items()
        }
        
        if interleave == 'random':
            trace = self._interleave_random(process_traces)
        elif interleave == 'round_robin':
            trace = self._interleave_round_robin(process_traces)
        elif interleave == 'batch':
            trace = self._interleave_batch(process_traces)
        else:
            raise ValueError(f"Unknown interleave type: {interleave}")
        
        self.last_trace = list(trace)
        return trace
    
    def _interleave_random(self, process_traces: Dict[int, List]) -> List[Tuple[int, int, bool]]:
        """Randomly interleave accesses from different processes."""
        all_accesses = []
        indices = {pid: 0 for pid in process_traces}
        active_processes = list(process_traces.keys())
        
        while active_processes:
            # Choose random active process
            pid = self.rng.choice(active_processes)
            
            if indices[pid] < len(process_traces[pid]):
                all_accesses.append(process_traces[pid][indices[pid]])
                indices[pid] += 1
            else:
                active_processes.remove(pid)
        
        return all_accesses
    
    def _interleave_round_robin(self, process_traces: Dict[int, List]) -> List[Tuple[int, int, bool]]:
        """Round-robin interleaving of process accesses."""
        all_accesses = []
        indices = {pid: 0 for pid in process_traces}
        pids = list(process_traces.keys())
        
        while any(indices[pid] < len(process_traces[pid]) for pid in pids):
            for pid in pids:
                if indices[pid] < len(process_traces[pid]):
                    all_accesses.append(process_traces[pid][indices[pid]])
                    indices[pid] += 1
        
        return all_accesses
    
    def _interleave_batch(self, process_traces: Dict[int, List]) -> List[Tuple[int, int, bool]]:
        """Batch interleaving - each process runs for a while before switching."""
        all_accesses = []
        batch_size = 100
        
        for pid in sorted(process_traces.keys()):
            trace = process_traces[pid]
            for i in range(0, len(trace), batch_size):
                all_accesses.extend(trace[i:i + batch_size])
        
        return all_accesses
    
    def estimate_aggregate_wss(self, window_size: int = 1000) -> Dict[int, int]:
        """Estimate working set size for each process."""
        return {
            pid: gen.estimate_working_set_size(window_size)
            for pid, gen in self.generators.items()
        }


def save_trace(trace: List[Tuple[int, int, bool]], filename: str):
    """Save trace to file."""
    with open(filename, 'w') as f:
        for page_id, process_id, is_write in trace:
            f.write(f"{page_id},{process_id},{int(is_write)}\n")


def load_trace(filename: str) -> List[Tuple[int, int, bool]]:
    """Load trace from file."""
    trace = []
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            trace.append((int(parts[0]), int(parts[1]), bool(int(parts[2]))))
    return trace


# Predefined workload configurations for experiments
PREDEFINED_WORKLOADS = {
    'small_locality': WorkloadConfig(
        workload_type=WorkloadType.HIGH_LOCALITY,
        num_pages=100,
        num_accesses=10000,
        working_set_size=20,
        locality_probability=0.95
    ),
    'large_streaming': WorkloadConfig(
        workload_type=WorkloadType.STREAMING,
        num_pages=1000,
        num_accesses=50000,
        sequential_probability=0.9
    ),
    'mixed_heterogeneous': WorkloadConfig(
        workload_type=WorkloadType.MIXED,
        num_pages=500,
        num_accesses=20000
    ),
    'thrashing_test': WorkloadConfig(
        workload_type=WorkloadType.THRASHING,
        num_pages=200,
        num_accesses=30000
    )
}
