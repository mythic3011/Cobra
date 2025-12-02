"""
Tests for reference preview and filtering UI components.

Tests the ReferencePreviewGallery class and filter_references function
to ensure proper functionality of the reference preview system.
"""

import pytest
from pathlib import Path
from PIL import Image
import tempfile
import os

from batch_processing.ui.reference_preview import (
    ReferencePreviewGallery,
    filter_references
)
from batch_processing.classification.classifier import ImageType
from batch_processing.exceptions import ValidationError


class TestReferencePreviewGallery:
    """Tests for ReferencePreviewGallery class."""
    
    def test_initialization(self):
        """Test gallery initialization."""
        gallery = ReferencePreviewGallery()
        
        assert gallery.reference_images == []
        assert gallery.classifications == {}
        assert gallery.selected_indices == set()
    
    def test_load_references_empty(self):
        """Test loading with empty reference list."""
        gallery = ReferencePreviewGallery()
        
        images, choices, selected = gallery.load_references([], {})
        
        assert images == []
        assert choices == []
        assert selected == []
    
    def test_load_references_with_images(self, tmp_path):
        """Test loading references with actual images."""
        gallery = ReferencePreviewGallery()
        
        # Create test images
        img_paths = []
        classifications = {}
        
        for i in range(3):
            img_path = tmp_path / f"ref_{i}.png"
            img = Image.new('RGB', (100, 100), color=(255, 0, 0))
            img.save(img_path)
            img_paths.append(str(img_path))
            
            # Create classification
            classifications[str(img_path)] = ImageType(
                type="colored",
                confidence=0.8 + i * 0.05,
                metrics={
                    "saturation": 0.5,
                    "color_count": 5000,
                    "edge_density": 0.1
                }
            )
        
        # Load references
        images, choices, selected = gallery.load_references(img_paths, classifications)
        
        # Verify results
        assert len(images) == 3
        assert len(choices) == 3
        assert len(selected) == 3
        assert selected == [0, 1, 2]
        
        # Verify choice labels contain confidence
        for choice in choices:
            assert "confidence:" in choice
            assert "%" in choice
        
        # Verify internal state
        assert gallery.reference_images == img_paths
        assert gallery.classifications == classifications
        assert gallery.selected_indices == {0, 1, 2}
    
    def test_select_all(self):
        """Test select all functionality."""
        gallery = ReferencePreviewGallery()
        choices = ["Image 0", "Image 1", "Image 2"]
        
        selected = gallery.select_all(choices)
        
        assert selected == [0, 1, 2]
        assert gallery.selected_indices == {0, 1, 2}
    
    def test_deselect_all(self):
        """Test deselect all functionality."""
        gallery = ReferencePreviewGallery()
        gallery.selected_indices = {0, 1, 2}
        
        selected = gallery.deselect_all()
        
        assert selected == []
        assert gallery.selected_indices == set()
    
    def test_auto_select_best(self, tmp_path):
        """Test auto-select best functionality."""
        gallery = ReferencePreviewGallery()
        
        # Create test images with varying confidence
        img_paths = []
        classifications = {}
        confidences = [0.9, 0.6, 0.8, 0.5]  # Two above 0.7, two below
        
        for i, conf in enumerate(confidences):
            img_path = tmp_path / f"ref_{i}.png"
            img = Image.new('RGB', (100, 100), color=(255, 0, 0))
            img.save(img_path)
            img_paths.append(str(img_path))
            
            classifications[str(img_path)] = ImageType(
                type="colored",
                confidence=conf,
                metrics={}
            )
        
        # Load references
        gallery.load_references(img_paths, classifications)
        
        # Auto-select with threshold 0.7
        choices = [f"Image {i}" for i in range(4)]
        selected = gallery.auto_select_best(choices, threshold=0.7)
        
        # Should select indices 0 and 2 (confidence 0.9 and 0.8)
        assert set(selected) == {0, 2}
        assert gallery.selected_indices == {0, 2}
    
    def test_update_selection(self):
        """Test updating selection."""
        gallery = ReferencePreviewGallery()
        
        gallery.update_selection([1, 3, 5])
        
        assert gallery.selected_indices == {1, 3, 5}
    
    def test_get_confidence_display_empty(self):
        """Test confidence display with no selection."""
        gallery = ReferencePreviewGallery()
        
        display = gallery.get_confidence_display([])
        
        assert "No images selected" in display
    
    def test_get_confidence_display_with_selection(self, tmp_path):
        """Test confidence display with selected images."""
        gallery = ReferencePreviewGallery()
        
        # Create test image
        img_path = tmp_path / "ref_0.png"
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        img.save(img_path)
        
        classifications = {
            str(img_path): ImageType(
                type="colored",
                confidence=0.85,
                metrics={
                    "saturation": 0.5,
                    "color_count": 5000,
                    "edge_density": 0.1
                }
            )
        }
        
        # Load references
        gallery.load_references([str(img_path)], classifications)
        
        # Get display for first image
        display = gallery.get_confidence_display([0])
        
        # Verify display contains expected information
        assert "ref_0.png" in display
        assert "85.0%" in display
        assert "Saturation:" in display
        assert "Unique Colors:" in display
        assert "Edge Density:" in display


class TestFilterReferences:
    """Tests for filter_references function."""
    
    def test_filter_references_basic(self):
        """Test basic reference filtering."""
        all_refs = ['/path/ref1.png', '/path/ref2.png', '/path/ref3.png']
        selected_indices = [0, 2]
        
        filtered = filter_references(all_refs, selected_indices)
        
        assert filtered == ['/path/ref1.png', '/path/ref3.png']
    
    def test_filter_references_all_selected(self):
        """Test filtering with all references selected."""
        all_refs = ['/path/ref1.png', '/path/ref2.png']
        selected_indices = [0, 1]
        
        filtered = filter_references(all_refs, selected_indices)
        
        assert filtered == all_refs
    
    def test_filter_references_none_selected(self):
        """Test filtering with no references selected."""
        all_refs = ['/path/ref1.png', '/path/ref2.png']
        selected_indices = []
        
        filtered = filter_references(all_refs, selected_indices)
        
        assert filtered == []
    
    def test_filter_references_empty_input(self):
        """Test filtering with empty input list."""
        filtered = filter_references([], [])
        
        assert filtered == []
    
    def test_filter_references_invalid_index_negative(self):
        """Test filtering with negative index raises error."""
        all_refs = ['/path/ref1.png', '/path/ref2.png']
        selected_indices = [-1]
        
        with pytest.raises(ValidationError) as exc_info:
            filter_references(all_refs, selected_indices)
        
        assert "Invalid index" in str(exc_info.value)
    
    def test_filter_references_invalid_index_too_large(self):
        """Test filtering with out-of-bounds index raises error."""
        all_refs = ['/path/ref1.png', '/path/ref2.png']
        selected_indices = [5]
        
        with pytest.raises(ValidationError) as exc_info:
            filter_references(all_refs, selected_indices)
        
        assert "Invalid index" in str(exc_info.value)
    
    def test_filter_references_single_selection(self):
        """Test filtering with single selection."""
        all_refs = ['/path/ref1.png', '/path/ref2.png', '/path/ref3.png']
        selected_indices = [1]
        
        filtered = filter_references(all_refs, selected_indices)
        
        assert filtered == ['/path/ref2.png']
    
    def test_filter_references_preserves_order(self):
        """Test that filtering preserves the order of selected indices."""
        all_refs = ['/path/ref1.png', '/path/ref2.png', '/path/ref3.png', '/path/ref4.png']
        selected_indices = [3, 0, 2]  # Out of order
        
        filtered = filter_references(all_refs, selected_indices)
        
        # Should maintain the order of selected_indices
        assert filtered == ['/path/ref4.png', '/path/ref1.png', '/path/ref3.png']


class TestIntegration:
    """Integration tests for reference preview system."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow from loading to filtering."""
        # Create test images
        img_paths = []
        classifications = {}
        
        for i in range(5):
            img_path = tmp_path / f"ref_{i}.png"
            img = Image.new('RGB', (100, 100), color=(255, 0, 0))
            img.save(img_path)
            img_paths.append(str(img_path))
            
            classifications[str(img_path)] = ImageType(
                type="colored",
                confidence=0.7 + i * 0.05,
                metrics={}
            )
        
        # Initialize gallery
        gallery = ReferencePreviewGallery()
        
        # Load references
        images, choices, selected = gallery.load_references(img_paths, classifications)
        assert len(images) == 5
        assert len(selected) == 5
        
        # Deselect some
        gallery.update_selection([0, 2, 4])
        
        # Filter based on selection
        filtered = filter_references(img_paths, [0, 2, 4])
        
        assert len(filtered) == 3
        assert filtered[0] == img_paths[0]
        assert filtered[1] == img_paths[2]
        assert filtered[2] == img_paths[4]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
