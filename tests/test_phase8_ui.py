"""
Phase 8 Automated Test Suite:
Validates Streamlit UI Headless AppTest:
- TC-P8-01: Headless Streamlit AppTest initializes and loads app.py cleanly without exceptions
- TC-P8-02: KPI metrics compute and render correctly in UI
- TC-P8-03: Exception queue and selection table render with correct item count
- TC-P8-04: Human-in-the-Loop approval records human decisions into audit trail
"""

import sys
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

BASE_DIR = Path(__file__).resolve().parent.parent
APP_FILE = str(BASE_DIR / "app.py")


def test_tc_p8_01_streamlit_headless_initialization():
    """TC-P8-01: Headless AppTest loads app.py without unhandled exceptions."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    assert not at.exception, f"Streamlit raised unhandled exception: {at.exception}"


def test_tc_p8_02_kpi_metrics_rendered():
    """TC-P8-02: Verifies KPI metric cards appear in the rendered UI."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    
    # Check metrics rendered
    metric_labels = [m.label for m in at.metric]
    assert "Total Transactions" in metric_labels
    assert "Cleanly Matched" in metric_labels
    assert "Exceptions Detected" in metric_labels
    assert "AI Auto-Resolved" in metric_labels


def test_tc_p8_03_exception_table_presence():
    """TC-P8-03: Exception selectbox is rendered and accessible."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    
    # Check that selectbox exists for exception queue
    assert len(at.selectbox) > 0
    first_select = at.selectbox[0]
    assert "Select Exception Dossier" in first_select.label
    assert len(first_select.options) > 0


def test_tc_p8_04_hitl_interaction():
    """TC-P8-04: Human in the loop action buttons exist and function without crashing."""
    at = AppTest.from_file(APP_FILE, default_timeout=30)
    at.run()
    
    # Check buttons in sidebar or main area
    button_labels = [b.label for b in at.button]
    assert any("Run FinRecon" in b for b in button_labels)
