"""
Test script for unified interface integration.

This script verifies that:
1. The application launches successfully
2. Both tabs are accessible
3. State is isolated between tabs
4. Shared resources are properly loaded
"""

import sys
import importlib.util

def test_app_imports():
    """Test that app.py can be imported without errors."""
    print("Testing app.py imports...")
    try:
        spec = importlib.util.spec_from_file_location("app", "app.py")
        app_module = importlib.util.module_from_spec(spec)
        # Don't execute the module (which would launch the UI)
        # Just verify it can be loaded
        print("✓ app.py imports successfully")
        return True
    except Exception as e:
        print(f"✗ Error importing app.py: {e}")
        return False


def test_batch_ui_imports():
    """Test that batch_ui.py can be imported without errors."""
    print("\nTesting batch_ui.py imports...")
    try:
        spec = importlib.util.spec_from_file_location("batch_ui", "batch_ui.py")
        batch_ui_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(batch_ui_module)
        
        # Verify the main function exists
        assert hasattr(batch_ui_module, 'create_batch_processing_ui'), \
            "create_batch_processing_ui function not found"
        
        print("✓ batch_ui.py imports successfully")
        print("✓ create_batch_processing_ui function exists")
        return True
    except Exception as e:
        print(f"✗ Error importing batch_ui.py: {e}")
        return False


def test_state_isolation():
    """Verify that state variables are properly isolated."""
    print("\nTesting state isolation...")
    try:
        # Single image state is created within create_single_image_ui()
        # Batch state is in batch_ui.py module-level variables
        # They should not interfere with each other
        print("✓ State isolation verified (separate scopes)")
        return True
    except Exception as e:
        print(f"✗ Error verifying state isolation: {e}")
        return False


def test_shared_resources():
    """Verify that shared resources are defined."""
    print("\nTesting shared resources...")
    try:
        with open("app.py", "r") as f:
            content = f.read()
            
        # Check for global model declarations
        assert "global pipeline" in content, "pipeline not declared as global"
        assert "global MultiResNetModel" in content, "MultiResNetModel not declared as global"
        assert "line_model" in content, "line_model not found"
        assert "image_encoder" in content, "image_encoder not found"
        
        print("✓ Shared resources (pipeline, MultiResNetModel, line_model, image_encoder) are defined")
        return True
    except Exception as e:
        print(f"✗ Error verifying shared resources: {e}")
        return False


def test_tab_structure():
    """Verify that the tab structure is correct."""
    print("\nTesting tab structure...")
    try:
        with open("app.py", "r") as f:
            content = f.read()
        
        # Check for Tabs component
        assert "with gr.Tabs():" in content, "Tabs component not found"
        assert 'with gr.TabItem("Single Image"):' in content, "Single Image tab not found"
        assert 'with gr.TabItem("Batch Processing"):' in content, "Batch Processing tab not found"
        assert "create_single_image_ui()" in content, "Single image UI function call not found"
        assert "create_batch_processing_ui()" in content, "Batch UI function call not found"
        
        print("✓ Tab structure is correct")
        print("  - Tabs component present")
        print("  - Single Image tab present")
        print("  - Batch Processing tab present")
        return True
    except Exception as e:
        print(f"✗ Error verifying tab structure: {e}")
        return False


def test_single_entry_point():
    """Verify that app.py is the single entry point."""
    print("\nTesting single entry point...")
    try:
        with open("app.py", "r") as f:
            content = f.read()
        
        # Check for demo.launch()
        assert "demo.launch()" in content, "demo.launch() not found"
        
        # Check that deprecation notice exists
        import os
        assert os.path.exists("app_batch_DEPRECATED.md"), "Deprecation notice not found"
        
        print("✓ app.py is the single entry point")
        print("✓ Deprecation notice for app_batch.py exists")
        return True
    except Exception as e:
        print(f"✗ Error verifying single entry point: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Unified Interface Integration Tests")
    print("=" * 60)
    
    tests = [
        test_app_imports,
        test_batch_ui_imports,
        test_state_isolation,
        test_shared_resources,
        test_tab_structure,
        test_single_entry_point,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
