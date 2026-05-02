"""
Page Replacement Algorithms Implementation
==========================================

Implements five page replacement algorithms:
1. FIFO (First-In-First-Out)
2. LRU (Least Recently Used)
3. NRU (Not Recently Used)
4. Second Chance (Clock)
5. WSClock (Working Set Clock)

References:
- Belady (1966): A study of replacement algorithms
- Denning (1968): The working set model for program behavior
"""

from abc import ABC, abstractmethod
from collections import deque, OrderedDict
from typing import List, Dict, Set, Tuple, Optional
import time


class Page:
    """Represents a memory page."""
    
    def __init__(self, page_id: int, process_id: int = 0):
        self.page_id = page_id
        self.process_id = process_id
        self.referenced = False
        self.modified = False
        self.last_reference_time = 0
        self.load_time = 0
        
    def __repr__(self):
        return f"Page({self.page_id}, proc={self.process_id})"


class PageReplacementAlgorithm(ABC):
    """Abstract base class for page replacement algorithms."""
    
    def __init__(self, num_frames: int):
        if not isinstance(num_frames, int):
            raise ValueError("num_frames must be an integer")
        if num_frames <= 0:
            raise ValueError("num_frames must be greater than zero")
        self.num_frames = num_frames
        self.frames: Dict[int, Page] = {}  # frame_id -> Page
        self.page_table: Dict[int, int] = {}  # page_id -> frame_id
        self.page_faults = 0
        self.page_replacements = 0
        self.disk_reads = 0
        self.disk_writes = 0
        self.current_time = 0
        
    @abstractmethod
    def access_page(self, page_id: int, process_id: int = 0, is_write: bool = False) -> bool:
        """
        Access a page. Returns True if page fault occurred.
        """
        pass
    
    @abstractmethod
    def select_victim(self) -> int:
        """
        Select a victim page to replace. Returns page_id.
        """
        pass
    
    def is_page_in_memory(self, page_id: int) -> bool:
        """Check if page is in memory."""
        return page_id in self.page_table
    
    def load_page(self, page_id: int, process_id: int = 0, is_write: bool = False):
        """Load a page into memory."""
        page = Page(page_id, process_id)
        page.referenced = True
        page.modified = is_write
        page.last_reference_time = self.current_time
        page.load_time = self.current_time
        
        # Find free frame or replace
        if len(self.frames) < self.num_frames:
            frame_id = len(self.frames)
        else:
            # Need to replace
            victim_id = self.select_victim()
            victim_frame = self.page_table[victim_id]
            victim_page = self.frames[victim_frame]
            
            if victim_page.modified:
                self.disk_writes += 1
            
            del self.frames[victim_frame]
            del self.page_table[victim_id]
            frame_id = victim_frame
            self.page_replacements += 1
        
        self.frames[frame_id] = page
        self.page_table[page_id] = frame_id
        self.disk_reads += 1
        self.page_faults += 1
        
    def get_stats(self) -> Dict:
        """Get algorithm statistics."""
        return {
            'page_faults': self.page_faults,
            'page_replacements': self.page_replacements,
            'disk_reads': self.disk_reads,
            'disk_writes': self.disk_writes,
            'total_disk_io': self.disk_reads + self.disk_writes
        }


class FIFO(PageReplacementAlgorithm):
    """
    First-In-First-Out Page Replacement Algorithm.
    
    Replaces the oldest page in memory (the one that was loaded first).
    Simple but can suffer from Belady's anomaly.
    """
    
    def __init__(self, num_frames: int):
        super().__init__(num_frames)
        self.load_order: deque = deque()  # Track load order
        
    def access_page(self, page_id: int, process_id: int = 0, is_write: bool = False) -> bool:
        self.current_time += 1
        
        if self.is_page_in_memory(page_id):
            # Page hit - update modified bit if write
            if is_write:
                frame_id = self.page_table[page_id]
                self.frames[frame_id].modified = True
            return False
        
        # Page fault
        self.load_page(page_id, process_id, is_write)
        self.load_order.append(page_id)
        return True
    
    def select_victim(self) -> int:
        """Select the oldest page (FIFO)."""
        while self.load_order:
            victim = self.load_order.popleft()
            if victim in self.page_table:
                return victim
        # Should not reach here if frames are full
        return list(self.page_table.keys())[0]


class LRU(PageReplacementAlgorithm):
    """
    Least Recently Used Page Replacement Algorithm.
    
    Replaces the page that has not been used for the longest time.
    Good for workloads with locality but requires tracking access times.
    """
    
    def __init__(self, num_frames: int):
        super().__init__(num_frames)
        self.access_order: OrderedDict = OrderedDict()  # page_id -> None
        
    def access_page(self, page_id: int, process_id: int = 0, is_write: bool = False) -> bool:
        self.current_time += 1
        
        if self.is_page_in_memory(page_id):
            # Page hit - update access order
            self.access_order.move_to_end(page_id)
            frame_id = self.page_table[page_id]
            self.frames[frame_id].referenced = True
            self.frames[frame_id].last_reference_time = self.current_time
            if is_write:
                self.frames[frame_id].modified = True
            return False
        
        # Page fault
        self.load_page(page_id, process_id, is_write)
        self.access_order[page_id] = None
        return True
    
    def select_victim(self) -> int:
        """
        Select the least recently used page and remove it from the access order.

        The base ``load_page`` method uses the victim page's ID to look up its
        frame in ``self.page_table``. If the algorithm-specific bookkeeping
        structures are not kept in sync with the page table, it's possible for
        ``select_victim`` to return a page that has already been evicted. This
        would lead to a ``KeyError`` when ``page_table`` is queried, as seen in
        the test suite. To avoid this, remove the chosen victim from
        ``access_order`` here so it stays consistent with ``frames`` and
        ``page_table``.
        """
        # Get the least recently used page ID
        victim = next(iter(self.access_order))
        # Remove it from the access tracking so that future calls won't return
        # the same victim again if the page is already gone from memory.
        self.access_order.pop(victim, None)
        return victim


class NRU(PageReplacementAlgorithm):
    """
    Not Recently Used Page Replacement Algorithm.
    
    Uses reference and modify bits to classify pages into 4 classes:
    Class 0: not referenced, not modified
    Class 1: not referenced, modified
    Class 2: referenced, not modified
    Class 3: referenced, modified
    
    Replaces from lowest non-empty class.
    """
    
    def __init__(self, num_frames: int):
        super().__init__(num_frames)
        self.clock_interval = 100  # Reset reference bits periodically
        
    def access_page(self, page_id: int, process_id: int = 0, is_write: bool = False) -> bool:
        self.current_time += 1
        
        # Periodically clear reference bits
        if self.current_time % self.clock_interval == 0:
            self.clear_reference_bits()
        
        if self.is_page_in_memory(page_id):
            # Page hit
            frame_id = self.page_table[page_id]
            self.frames[frame_id].referenced = True
            self.frames[frame_id].last_reference_time = self.current_time
            if is_write:
                self.frames[frame_id].modified = True
            return False
        
        # Page fault
        self.load_page(page_id, process_id, is_write)
        return True
    
    def clear_reference_bits(self):
        """Clear all reference bits (simulates clock interrupt)."""
        for page in self.frames.values():
            page.referenced = False
    
    def select_victim(self) -> int:
        """Select page from lowest non-empty class."""
        # Classify pages
        classes = {0: [], 1: [], 2: [], 3: []}
        
        for page_id, frame_id in self.page_table.items():
            page = self.frames[frame_id]
            class_num = (2 if page.referenced else 0) + (1 if page.modified else 0)
            classes[class_num].append(page_id)
        
        # Select from lowest non-empty class
        for class_num in range(4):
            if classes[class_num]:
                # Return first page from lowest class
                return classes[class_num][0]
        
        return list(self.page_table.keys())[0]


class SecondChance(PageReplacementAlgorithm):
    """
    Second Chance (Clock) Page Replacement Algorithm.
    
    FIFO with a twist: give pages a second chance if referenced.
    Uses a circular list and reference bits.
    """
    
    def __init__(self, num_frames: int):
        super().__init__(num_frames)
        self.clock_hand = 0
        self.frame_list: List[int] = []  # List of page_ids in frames
        
    def access_page(self, page_id: int, process_id: int = 0, is_write: bool = False) -> bool:
        self.current_time += 1
        
        if self.is_page_in_memory(page_id):
            # Page hit - set reference bit
            frame_id = self.page_table[page_id]
            self.frames[frame_id].referenced = True
            self.frames[frame_id].last_reference_time = self.current_time
            if is_write:
                self.frames[frame_id].modified = True
            return False
        
        # Page fault
        self.load_page(page_id, process_id, is_write)
        if page_id not in self.frame_list:
            self.frame_list.append(page_id)
        return True
    
    def select_victim(self) -> int:
        """Select victim using clock algorithm."""
        while True:
            # Get page at clock hand
            if self.clock_hand >= len(self.frame_list):
                self.clock_hand = 0
            
            page_id = self.frame_list[self.clock_hand]
            
            if page_id not in self.page_table:
                # Page was already replaced
                self.frame_list.pop(self.clock_hand)
                continue
            
            frame_id = self.page_table[page_id]
            page = self.frames[frame_id]
            
            if page.referenced:
                # Give second chance
                page.referenced = False
                self.clock_hand += 1
            else:
                # Select this page
                victim = page_id
                self.frame_list.pop(self.clock_hand)
                return victim


class WSClock(PageReplacementAlgorithm):
    """
    Working Set Clock Page Replacement Algorithm.
    
    Combines clock algorithm with working set model.
    Considers both reference bit and time since last reference.
    Pages not in working set are candidates for replacement.
    
    Reference: Carr and Hennessey (1981)
    """
    
    def __init__(self, num_frames: int, tau: int = 100):
        """
        Args:
            num_frames: Number of frames
            tau: Working set window (time units)
        """
        super().__init__(num_frames)
        self.tau = tau  # Working set window
        self.clock_hand = 0
        self.frame_list: List[int] = []
        
    def access_page(self, page_id: int, process_id: int = 0, is_write: bool = False) -> bool:
        self.current_time += 1
        
        if self.is_page_in_memory(page_id):
            # Page hit
            frame_id = self.page_table[page_id]
            self.frames[frame_id].referenced = True
            self.frames[frame_id].last_reference_time = self.current_time
            if is_write:
                self.frames[frame_id].modified = True
            return False
        
        # Page fault
        self.load_page(page_id, process_id, is_write)
        if page_id not in self.frame_list:
            self.frame_list.append(page_id)
        return True
    
    def in_working_set(self, page: Page) -> bool:
        """Check if page is in working set."""
        return (self.current_time - page.last_reference_time) <= self.tau
    
    def select_victim(self) -> int:
        """Select victim using WSClock algorithm."""
        if not self.frame_list:
            return list(self.page_table.keys())[0]

        first_dirty_candidate = None
        inspected = 0
        frame_count = len(self.frame_list)

        while inspected < 2 * frame_count and self.frame_list:
            if self.clock_hand >= len(self.frame_list):
                self.clock_hand = 0

            page_id = self.frame_list[self.clock_hand]

            if page_id not in self.page_table:
                self.frame_list.pop(self.clock_hand)
                frame_count = len(self.frame_list)
                if frame_count == 0:
                    break
                continue

            frame_id = self.page_table[page_id]
            page = self.frames[frame_id]
            in_ws = self.in_working_set(page)

            if not in_ws and not page.modified:
                victim = page_id
                self.frame_list.pop(self.clock_hand)
                return victim

            if not in_ws and first_dirty_candidate is None:
                first_dirty_candidate = (self.clock_hand, page_id)

            page.referenced = False
            self.clock_hand += 1
            inspected += 1

        if first_dirty_candidate is not None:
            hand, victim = first_dirty_candidate
            if hand < len(self.frame_list) and self.frame_list[hand] == victim:
                self.frame_list.pop(hand)
            else:
                try:
                    self.frame_list.remove(victim)
                except ValueError:
                    pass
            return victim

        # Final fallback: evict the oldest tracked page so we never spin forever.
        return self.frame_list.pop(0)


def get_algorithm(name: str, num_frames: int, **kwargs) -> PageReplacementAlgorithm:
    """
    Factory function to create algorithm instances.
    
    Args:
        name: Algorithm name (FIFO, LRU, NRU, SecondChance, WSClock)
        num_frames: Number of frames
        **kwargs: Additional algorithm-specific parameters
    
    Returns:
        PageReplacementAlgorithm instance
    """
    algorithms = {
        'FIFO': FIFO,
        'LRU': LRU,
        'NRU': NRU,
        'SecondChance': SecondChance,
        'WSClock': WSClock
    }
    
    if name not in algorithms:
        raise ValueError(f"Unknown algorithm: {name}. Available: {list(algorithms.keys())}")
    
    return algorithms[name](num_frames, **kwargs)
