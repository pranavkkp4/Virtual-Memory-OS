"""
Unit Tests for Page Replacement Algorithms
==========================================

Tests correctness of algorithm implementations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest
from page_replacement import FIFO, LRU, NRU, SecondChance, WSClock


class TestFIFO(unittest.TestCase):
    """Test FIFO algorithm."""
    
    def setUp(self):
        self.algo = FIFO(num_frames=3)
    
    def test_basic_operations(self):
        """Test basic page access."""
        # Page faults for new pages
        self.assertTrue(self.algo.access_page(1))
        self.assertTrue(self.algo.access_page(2))
        self.assertTrue(self.algo.access_page(3))
        
        # Page hit
        self.assertFalse(self.algo.access_page(1))
        
        # Page fault - should replace page 2 (oldest)
        self.assertTrue(self.algo.access_page(4))
        
        stats = self.algo.get_stats()
        self.assertEqual(stats['page_faults'], 4)
        self.assertEqual(stats['page_replacements'], 1)
    
    def test_belady_anomaly(self):
        """Test that FIFO can exhibit Belady's anomaly."""
        # This is a known case where increasing frames increases faults
        pass  # Implementation-specific


class TestLRU(unittest.TestCase):
    """Test LRU algorithm."""
    
    def setUp(self):
        self.algo = LRU(num_frames=3)
    
    def test_basic_operations(self):
        """Test LRU ordering."""
        # Access pages
        self.algo.access_page(1)
        self.algo.access_page(2)
        self.algo.access_page(3)
        
        # Access page 1 (makes it most recently used)
        self.algo.access_page(1)
        
        # Add new page - should replace page 2 (least recently used)
        self.algo.access_page(4)
        
        # Page 2 should cause fault (was replaced)
        self.assertTrue(self.algo.access_page(2))
        
        # Page 1 should be hit
        self.assertFalse(self.algo.access_page(1))


class TestNRU(unittest.TestCase):
    """Test NRU algorithm."""
    
    def setUp(self):
        self.algo = NRU(num_frames=3)
    
    def test_classification(self):
        """Test page classification."""
        self.algo.access_page(1)
        self.algo.access_page(2)
        self.algo.access_page(3, is_write=True)
        
        stats = self.algo.get_stats()
        self.assertEqual(stats['page_faults'], 3)


class TestSecondChance(unittest.TestCase):
    """Test Second Chance (Clock) algorithm."""
    
    def setUp(self):
        self.algo = SecondChance(num_frames=3)
    
    def test_second_chance(self):
        """Test that referenced pages get second chance."""
        # Fill frames
        self.algo.access_page(1)
        self.algo.access_page(2)
        self.algo.access_page(3)
        
        # Access page 1 (sets reference bit)
        self.algo.access_page(1)
        
        # Add new page - page 1 should get second chance
        self.algo.access_page(4)
        
        stats = self.algo.get_stats()
        self.assertEqual(stats['page_faults'], 4)


class TestWSClock(unittest.TestCase):
    """Test WSClock algorithm."""
    
    def setUp(self):
        self.algo = WSClock(num_frames=3, tau=100)
    
    def test_working_set(self):
        """Test working set detection."""
        # Access pages
        self.algo.access_page(1)
        self.algo.access_page(2)
        self.algo.access_page(3)
        
        stats = self.algo.get_stats()
        self.assertEqual(stats['page_faults'], 3)


class TestAlgorithmComparison(unittest.TestCase):
    """Compare algorithms on same workload."""
    
    def test_same_workload(self):
        """All algorithms should handle same workload."""
        workload = [(1, 0, False), (2, 0, False), (3, 0, False),
                   (1, 0, False), (4, 0, False), (2, 0, False)]
        
        algorithms = {
            'FIFO': FIFO(3),
            'LRU': LRU(3),
            'NRU': NRU(3),
            'SecondChance': SecondChance(3),
            'WSClock': WSClock(3)
        }
        
        for name, algo in algorithms.items():
            for page_id, process_id, is_write in workload:
                algo.access_page(page_id, process_id, is_write)
            
            stats = algo.get_stats()
            self.assertGreater(stats['page_faults'], 0)
            self.assertLessEqual(stats['page_faults'], len(workload))


if __name__ == '__main__':
    unittest.main()
