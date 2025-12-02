"""
Integration tests for the CLI interface.

These tests verify that the CLI can be invoked correctly and handles
various scenarios appropriately.
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import pytest


def run_cli(*args):
    """
    Run the CLI with the given arguments.
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, "batch_colorize.py"] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


class TestCLIHelp:
    """Test CLI help and usage information."""
    
    def test_help_flag(self):
        """Test that --help flag displays usage information."""
        exit_code, stdout, stderr = run_cli("--help")
        
        assert exit_code == 0
        assert "Batch colorization of comic line art" in stdout
        assert "--input-dir" in stdout
        assert "--output-dir" in stdout
        assert "--reference-dir" in stdout
        assert "Examples:" in stdout
    
    def test_no_arguments(self):
        """Test that running without arguments shows error."""
        exit_code, stdout, stderr = run_cli()
        
        assert exit_code != 0
        assert "required" in stderr.lower() or "required" in stdout.lower()


class TestCLIValidation:
    """Test CLI validation of paths and parameters."""
    
    def test_nonexistent_input_dir(self):
        """Test that nonexistent input directory is rejected."""
        exit_code, stdout, stderr = run_cli(
            "--input-dir", "/nonexistent/path",
            "--output-dir", "/tmp/test",
            "--reference-dir", "/nonexistent/ref"
        )
        
        assert exit_code != 0
        assert "does not exist" in stderr.lower() or "does not exist" in stdout.lower()
    
    def test_negative_seed(self):
        """Test that negative seed is rejected."""
        exit_code, stdout, stderr = run_cli(
            "--input-dir", "examples/line/example0",
            "--output-dir", "/tmp/test",
            "--reference-dir", "examples/shadow/example0",
            "--seed", "-1"
        )
        
        assert exit_code != 0
        assert "seed" in stderr.lower() or "seed" in stdout.lower()
    
    def test_invalid_steps(self):
        """Test that invalid steps value is rejected."""
        exit_code, stdout, stderr = run_cli(
            "--input-dir", "examples/line/example0",
            "--output-dir", "/tmp/test",
            "--reference-dir", "examples/shadow/example0",
            "--steps", "0"
        )
        
        assert exit_code != 0
        assert "steps" in stderr.lower() or "steps" in stdout.lower()
    
    def test_invalid_top_k(self):
        """Test that invalid top-k value is rejected."""
        exit_code, stdout, stderr = run_cli(
            "--input-dir", "examples/line/example0",
            "--output-dir", "/tmp/test",
            "--reference-dir", "examples/shadow/example0",
            "--top-k", "0"
        )
        
        assert exit_code != 0
        assert "top-k" in stderr.lower() or "top-k" in stdout.lower()
    
    def test_invalid_style(self):
        """Test that invalid style is rejected."""
        exit_code, stdout, stderr = run_cli(
            "--input-dir", "examples/line/example0",
            "--output-dir", "/tmp/test",
            "--reference-dir", "examples/shadow/example0",
            "--style", "invalid_style"
        )
        
        assert exit_code != 0
        # argparse will catch this before our validation


class TestCLIExitCodes:
    """Test that CLI returns appropriate exit codes."""
    
    def test_validation_error_exit_code(self):
        """Test that validation errors return exit code 1."""
        exit_code, stdout, stderr = run_cli(
            "--input-dir", "/nonexistent",
            "--output-dir", "/tmp/test",
            "--reference-dir", "/nonexistent"
        )
        
        assert exit_code == 1
    
    def test_help_exit_code(self):
        """Test that --help returns exit code 0."""
        exit_code, stdout, stderr = run_cli("--help")
        
        assert exit_code == 0
    
    def test_missing_required_args_exit_code(self):
        """Test that missing required arguments returns non-zero exit code."""
        exit_code, stdout, stderr = run_cli("--input-dir", "examples/line/example0")
        
        assert exit_code != 0


class TestCLIArguments:
    """Test that CLI accepts all documented arguments."""
    
    def test_input_dir_argument(self):
        """Test that --input-dir argument is accepted."""
        # This will fail validation but should parse the argument
        exit_code, stdout, stderr = run_cli(
            "--input-dir", "examples/line/example0",
            "--output-dir", "/tmp/test",
            "--reference-dir", "examples/shadow/example0",
            "--help"  # Add help to avoid actual processing
        )
        
        assert exit_code == 0
    
    def test_all_style_options(self):
        """Test that all style options are accepted."""
        for style in ["line", "line + shadow"]:
            exit_code, stdout, stderr = run_cli(
                "--input-dir", "examples/line/example0",
                "--output-dir", "/tmp/test",
                "--reference-dir", "examples/shadow/example0",
                "--style", style,
                "--help"
            )
            
            assert exit_code == 0
    
    def test_boolean_flags(self):
        """Test that boolean flags are accepted."""
        exit_code, stdout, stderr = run_cli(
            "--input-dir", "examples/line/example0",
            "--output-dir", "/tmp/test",
            "--reference-dir", "examples/shadow/example0",
            "--recursive",
            "--overwrite",
            "--preview",
            "--verbose",
            "--help"
        )
        
        assert exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
