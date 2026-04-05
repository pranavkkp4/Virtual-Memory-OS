"""
Frame Allocation Policies Implementation
========================================

Implements three frame allocation policies:
1. Global Allocation: All processes share a common pool of frames
2. Local Allocation: Each process has a fixed number of frames
3. Proportional Allocation: Frames scale with estimated process size

These policies determine how physical memory frames are distributed
among competing processes in a multiprogramming environment.

References:
- Denning (1968): The working set model for program behavior
- Arden and Boettner (1969): Measurement and performance of multiprogramming
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import copy

try:
    from .page_replacement import (
        PageReplacementAlgorithm, FIFO, LRU, NRU,
        SecondChance, WSClock, get_algorithm
    )
except ImportError:  # pragma: no cover - supports direct script execution
    from page_replacement import (
        PageReplacementAlgorithm, FIFO, LRU, NRU,
        SecondChance, WSClock, get_algorithm
    )


class FrameAllocationPolicy(ABC):
    """Abstract base class for frame allocation policies."""
    
    def __init__(self, total_frames: int, algorithm_name: str = 'LRU'):
        self.total_frames = total_frames
        self.algorithm_name = algorithm_name
        self.processes: Dict[int, object] = {}  # process_id -> algorithm instance
        self.process_stats: Dict[int, List[Dict]] = defaultdict(list)
        
    @abstractmethod
    def allocate_frames(self, process_ids: List[int]) -> Dict[int, int]:
        """
        Allocate frames to processes.
        
        Returns:
            Dictionary mapping process_id to number of frames
        """
        pass
    
    @abstractmethod
    def access_page(self, process_id: int, page_id: int, is_write: bool = False) -> bool:
        """
        Access a page for a specific process.
        
        Returns:
            True if page fault occurred
        """
        pass
    
    def add_process(self, process_id: int, num_frames: int, **kwargs):
        """Add a process with allocated frames."""
        self.processes[process_id] = get_algorithm(
            self.algorithm_name, num_frames, **kwargs
        )
    
    def remove_process(self, process_id: int):
        """Remove a process and collect its stats."""
        if process_id in self.processes:
            stats = self.processes[process_id].get_stats()
            self.process_stats[process_id].append(stats)
            del self.processes[process_id]
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all processes."""
        stats = {
            'per_process': {},
            'system_total': {
                'page_faults': 0,
                'page_replacements': 0,
                'disk_reads': 0,
                'disk_writes': 0,
                'total_disk_io': 0
            }
        }
        
        for pid, alg in self.processes.items():
            proc_stats = alg.get_stats()
            stats['per_process'][pid] = proc_stats
            
            for key in ['page_faults', 'page_replacements', 'disk_reads', 
                       'disk_writes', 'total_disk_io']:
                stats['system_total'][key] += proc_stats[key]
        
        return stats


class GlobalAllocation(FrameAllocationPolicy):
    """
    Global Frame Allocation Policy.
    
    All processes share a single pool of frames. When a process needs
    a frame, it can take from the global pool or steal from another
    process. This can lead to better overall utilization but may
    cause unfairness.
    
    Characteristics:
    - Dynamic frame distribution
    - Better utilization for processes with varying needs
    - Risk of thrashing if one process dominates
    """
    
    def __init__(self, total_frames: int, algorithm_name: str = 'LRU', 
                 min_frames_per_process: int = 2):
        super().__init__(total_frames, algorithm_name)
        self.min_frames_per_process = min_frames_per_process
        self.global_algorithm = get_algorithm(algorithm_name, total_frames)
        self.process_page_map: Dict[int, set] = defaultdict(set)  # process_id -> set of page_ids
        self.process_access_counts: Dict[int, int] = defaultdict(int)
        self.process_fault_counts: Dict[int, int] = defaultdict(int)
        
    def allocate_frames(self, process_ids: List[int]) -> Dict[int, int]:
        """
        In global allocation, frames are shared dynamically.
        Returns minimum frames per process as a baseline.
        """
        allocation = {}
        for pid in process_ids:
            allocation[pid] = self.min_frames_per_process
        return allocation
    
    def add_process(self, process_id: int, num_frames: int = None, **kwargs):
        """Add a process - in global allocation, we just track process ID."""
        self.processes[process_id] = None  # No separate algorithm instance
        self.process_page_map[process_id] = set()
    
    def access_page(self, process_id: int, page_id: int, is_write: bool = False) -> bool:
        """
        Access a page using global frame pool.
        
        The global algorithm manages all frames, but we track
        which pages belong to which process.
        """
        # Create unique page ID by combining process_id and page_id
        unique_page_id = (process_id << 32) | page_id
        self.process_access_counts[process_id] += 1
        
        is_fault = self.global_algorithm.access_page(unique_page_id, process_id, is_write)
        
        if is_fault:
            self.process_fault_counts[process_id] += 1
            self.process_page_map[process_id].add(page_id)
        
        return is_fault
    
    def get_all_stats(self) -> Dict:
        """Get statistics - in global allocation, all stats are in global_algorithm."""
        global_stats = self.global_algorithm.get_stats()
        
        # Page faults are tracked exactly per process even though the frames are shared.
        per_process = {}
        frame_distribution = self.get_frame_distribution()
        for pid in self.processes:
            accesses = self.process_access_counts[pid]
            page_faults = self.process_fault_counts[pid]
            per_process[pid] = {
                'accesses': accesses,
                'page_faults': page_faults,
                'page_fault_rate': (page_faults / accesses) if accesses else 0.0,
                'pages_in_memory': frame_distribution.get(pid, 0)
            }
        
        return {
            'per_process': per_process,
            'system_total': global_stats,
            'allocation_type': 'global'
        }
    
    def get_frame_distribution(self) -> Dict[int, int]:
        """Get current frame distribution among processes."""
        distribution = defaultdict(int)
        for unique_page_id, frame_id in self.global_algorithm.page_table.items():
            process_id = self.global_algorithm.frames[frame_id].process_id
            distribution[process_id] += 1
        return dict(distribution)


class LocalAllocation(FrameAllocationPolicy):
    """
    Local Frame Allocation Policy.
    
    Each process has a fixed number of frames allocated to it.
    Page replacement happens only within the process's own frames.
    This provides isolation but may lead to underutilization.
    
    Characteristics:
    - Fixed frame allocation per process
    - Process isolation (no interference)
    - May waste frames if process doesn't use them
    - Better fairness guarantees
    """
    
    def __init__(self, total_frames: int, algorithm_name: str = 'LRU'):
        super().__init__(total_frames, algorithm_name)
        self.frames_per_process: Dict[int, int] = {}
        
    def allocate_frames(self, process_ids: List[int], 
                       equal_allocation: bool = True,
                       frames_per_process: Dict[int, int] = None) -> Dict[int, int]:
        """
        Allocate frames to processes.
        
        Args:
            process_ids: List of process IDs
            equal_allocation: If True, divide frames equally
            frames_per_process: If equal_allocation is False, use this mapping
        
        Returns:
            Dictionary mapping process_id to number of frames
        """
        n = len(process_ids)
        
        if equal_allocation:
            base_frames = self.total_frames // n
            remainder = self.total_frames % n
            
            allocation = {}
            for i, pid in enumerate(process_ids):
                # Distribute remainder to first processes
                allocation[pid] = base_frames + (1 if i < remainder else 0)
        else:
            allocation = frames_per_process or {}
        
        self.frames_per_process = allocation
        return allocation
    
    def add_process(self, process_id: int, num_frames: int = None, **kwargs):
        """Add a process with its own frame pool."""
        if num_frames is None:
            num_frames = self.frames_per_process.get(process_id, 4)
        
        self.processes[process_id] = get_algorithm(
            self.algorithm_name, num_frames, **kwargs
        )
    
    def access_page(self, process_id: int, page_id: int, is_write: bool = False) -> bool:
        """
        Access a page using process's local frame pool.
        """
        if process_id not in self.processes:
            raise ValueError(f"Process {process_id} not found")
        
        return self.processes[process_id].access_page(page_id, process_id, is_write)
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all processes."""
        stats = {
            'per_process': {},
            'system_total': {
                'page_faults': 0,
                'page_replacements': 0,
                'disk_reads': 0,
                'disk_writes': 0,
                'total_disk_io': 0
            },
            'allocation_type': 'local'
        }
        
        for pid, alg in self.processes.items():
            proc_stats = alg.get_stats()
            stats['per_process'][pid] = proc_stats
            
            for key in ['page_faults', 'page_replacements', 'disk_reads', 
                       'disk_writes', 'total_disk_io']:
                stats['system_total'][key] += proc_stats[key]
        
        return stats
    
    def get_frame_distribution(self) -> Dict[int, int]:
        """Get frame distribution - in local allocation, this is fixed."""
        return self.frames_per_process.copy()


class ProportionalAllocation(LocalAllocation):
    """
    Proportional Frame Allocation.
    
    Allocates frames proportionally based on process size (working set)
    or priority. A middle ground between equal allocation and pure local.
    """
    
    def __init__(self, total_frames: int, algorithm_name: str = 'LRU'):
        super().__init__(total_frames, algorithm_name)
        self.process_sizes: Dict[int, int] = {}
        
    def allocate_frames_proportional(self, process_sizes: Dict[int, int]) -> Dict[int, int]:
        """
        Allocate frames proportional to process sizes.
        
        Args:
            process_sizes: Dictionary mapping process_id to estimated size (WSS)
        
        Returns:
            Dictionary mapping process_id to number of frames
        """
        self.process_sizes = process_sizes
        total_size = sum(process_sizes.values())
        
        allocation = {}
        allocated = 0
        
        # First pass: proportional allocation
        for pid, size in process_sizes.items():
            proportion = size / total_size
            allocation[pid] = max(2, int(self.total_frames * proportion))
            allocated += allocation[pid]
        
        # Distribute remaining frames
        remainder = self.total_frames - allocated
        if remainder > 0:
            # Give extra frames to largest processes
            sorted_pids = sorted(process_sizes.keys(), 
                               key=lambda p: process_sizes[p], 
                               reverse=True)
            for i in range(remainder):
                allocation[sorted_pids[i % len(sorted_pids)]] += 1
        
        self.frames_per_process = allocation
        return allocation


def get_allocation_policy(policy_name: str, total_frames: int, 
                         algorithm_name: str = 'LRU', **kwargs) -> FrameAllocationPolicy:
    """
    Factory function to create allocation policy instances.
    
    Args:
        policy_name: Policy name (GlobalAllocation, LocalAllocation, ProportionalAllocation)
        total_frames: Total number of frames
        algorithm_name: Page replacement algorithm to use
        **kwargs: Additional policy-specific parameters
    
    Returns:
        FrameAllocationPolicy instance
    """
    policies = {
        'GlobalAllocation': GlobalAllocation,
        'LocalAllocation': LocalAllocation,
        'ProportionalAllocation': ProportionalAllocation
    }
    
    if policy_name not in policies:
        raise ValueError(f"Unknown policy: {policy_name}. Available: {list(policies.keys())}")
    
    return policies[policy_name](total_frames, algorithm_name, **kwargs)
