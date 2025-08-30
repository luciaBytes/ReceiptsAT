"""
Unit tests for API Monitor functionality.

Tests the monitoring of Portal das Finanças for changes that could affect
the receipt processing automation.
"""

import unittest
import os
import tempfile
import json
import hashlib
from unittest.mock import Mock, patch, MagicMock
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.api_monitor import (
    PortalAPIMonitor, 
    PageSnapshot, 
    ChangeDetection, 
    MonitoringConfig
)


class TestPageSnapshot(unittest.TestCase):
    """Test cases for PageSnapshot dataclass."""
    
    def test_page_snapshot_creation(self):
        """Test creating a PageSnapshot instance."""
        snapshot = PageSnapshot(
            url="https://example.com",
            timestamp="2025-08-30T12:00:00",
            content_hash="abc123",
            form_fields=["username", "password"],
            critical_elements={"login": "form#login"},
            javascript_functions=["login()", "validate()"],
            meta_info={"title": "Test Page"},
            status_code=200,
            response_time_ms=150
        )
        
        self.assertEqual(snapshot.url, "https://example.com")
        self.assertEqual(snapshot.status_code, 200)
        self.assertEqual(len(snapshot.form_fields), 2)
        self.assertIn("username", snapshot.form_fields)


class TestChangeDetection(unittest.TestCase):
    """Test cases for ChangeDetection dataclass."""
    
    def test_change_detection_creation(self):
        """Test creating a ChangeDetection instance."""
        change = ChangeDetection(
            change_type="form",
            severity="medium",
            description="Username field no longer found",
            old_value="input[name='username']",
            new_value="",
            affected_functionality=["login"],
            recommended_action="Update form selector",
            timestamp="2025-08-30T12:00:00"
        )
        
        self.assertEqual(change.change_type, "form")
        self.assertEqual(change.severity, "medium")
        self.assertEqual(change.old_value, "input[name='username']")
        self.assertEqual(change.new_value, "")


class TestMonitoringConfig(unittest.TestCase):
    """Test cases for MonitoringConfig dataclass."""
    
    def test_default_config_creation(self):
        """Test creating MonitoringConfig with defaults."""
        config = MonitoringConfig()
        
        self.assertEqual(config.check_interval_hours, 4)
        self.assertIn("https://www.portaldasfinancas.gov.pt/", config.critical_pages)
        self.assertIn("form[name='loginForm']", config.form_selectors)
        self.assertIn("login_button", config.element_selectors)
        self.assertIn("function\\s+login\\s*\\(", config.javascript_patterns)
    
    def test_custom_config_creation(self):
        """Test creating MonitoringConfig with custom values."""
        config = MonitoringConfig(
            check_interval_hours=2,
            critical_pages=["https://test.com"],
            form_selectors=["form.test"]
        )
        
        self.assertEqual(config.check_interval_hours, 2)
        self.assertEqual(config.critical_pages, ["https://test.com"])
        self.assertIn("form.test", config.form_selectors)


class TestPortalAPIMonitor(unittest.TestCase):
    """Test cases for PortalAPIMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.monitor = PortalAPIMonitor(data_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_monitor_initialization(self):
        """Test PortalAPIMonitor initialization."""
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertIsInstance(self.monitor.config, MonitoringConfig)
        self.assertEqual(self.monitor.data_dir, self.test_dir)
    
    def test_config_save_and_load(self):
        """Test saving and loading configuration."""
        # Modify config
        self.monitor.config.check_interval_hours = 6
        self.monitor._save_config(self.monitor.config)
        
        # Create new monitor instance to test loading
        new_monitor = PortalAPIMonitor(data_dir=self.test_dir)
        self.assertEqual(new_monitor.config.check_interval_hours, 6)
    
    def test_extract_form_fields(self):
        """Test extracting form fields from HTML content."""
        html_content = """
        <html>
        <body>
            <form name="loginForm">
                <input name="username" type="text">
                <input name="password" type="password">
                <input type="submit" value="Login">
            </form>
        </body>
        </html>
        """
        
        form_fields = self.monitor._extract_form_fields(html_content)
        
        # Fields are returned as JSON strings
        username_field = '{"id": "", "name": "username", "tag": "input", "type": "text"}'
        password_field = '{"id": "", "name": "password", "tag": "input", "type": "password"}'
        
        self.assertIn(username_field, form_fields)
        self.assertIn(password_field, form_fields)
    
    def test_extract_meta_info(self):
        """Test extracting meta information from HTML content."""
        html_content = """
        <html>
        <head>
            <title>Portal das Finanças</title>
            <meta name="description" content="Tax portal">
        </head>
        <body>
            <h1>Welcome</h1>
        </body>
        </html>
        """
        
        meta_info = self.monitor._extract_meta_info(html_content)
        self.assertEqual(meta_info.get("title"), "Portal das Finanças")
        self.assertEqual(meta_info.get("description"), "Tax portal")
    
    def test_extract_javascript_functions(self):
        """Test extracting JavaScript functions from HTML content."""
        html_content = """
        <html>
        <body>
            <script>
            function login() {
                return true;
            }
            
            function validateForm() {
                // validation logic
            }
            </script>
        </body>
        </html>
        """
        
        js_functions = self.monitor._extract_javascript_functions(html_content)
        
        # The regex pattern finds "function login(" from the HTML
        self.assertGreater(len(js_functions), 0)
        self.assertTrue(any("login" in func for func in js_functions))
    
    @patch('requests.Session.get')
    def test_capture_page_snapshot_success(self, mock_get):
        """Test successful page snapshot capture."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <form name="loginForm">
                <input name="username" type="text">
            </form>
        </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        snapshot = self.monitor.capture_page_snapshot("https://example.com")
        
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.url, "https://example.com")
        self.assertEqual(snapshot.status_code, 200)
        
        # Check for form field in JSON format
        username_field = '{"id": "", "name": "username", "tag": "input", "type": "text"}'
        self.assertIn(username_field, snapshot.form_fields)
        self.assertEqual(snapshot.meta_info.get("title"), "Test Page")
    
    @patch('requests.Session.get')
    def test_capture_page_snapshot_failure(self, mock_get):
        """Test page snapshot capture with HTTP error."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        snapshot = self.monitor.capture_page_snapshot("https://example.com/notfound")
        
        self.assertIsNone(snapshot)
    
    @patch('requests.Session.get')
    def test_capture_page_snapshot_exception(self, mock_get):
        """Test page snapshot capture with network exception."""
        # Mock network exception
        mock_get.side_effect = Exception("Network error")
        
        snapshot = self.monitor.capture_page_snapshot("https://example.com")
        
        self.assertIsNone(snapshot)
    
    def test_compare_snapshots_no_changes(self):
        """Test comparing identical snapshots."""
        snapshot1 = PageSnapshot(
            url="https://example.com",
            timestamp="2025-08-30T12:00:00",
            content_hash="abc123",
            form_fields=["username", "password"],
            critical_elements={"login": "form#login"},
            javascript_functions=["login()"],
            meta_info={"title": "Test Page"},
            status_code=200,
            response_time_ms=150
        )
        
        snapshot2 = PageSnapshot(
            url="https://example.com",
            timestamp="2025-08-30T12:05:00",
            content_hash="abc123",
            form_fields=["username", "password"],
            critical_elements={"login": "form#login"},
            javascript_functions=["login()"],
            meta_info={"title": "Test Page"},
            status_code=200,
            response_time_ms=160
        )
        
        changes = self.monitor.compare_snapshots(snapshot1, snapshot2)
        
        # Should only detect response time change (not critical)
        self.assertEqual(len(changes), 0)
    
    def test_compare_snapshots_with_changes(self):
        """Test comparing snapshots with differences."""
        snapshot1 = PageSnapshot(
            url="https://example.com",
            timestamp="2025-08-30T12:00:00",
            content_hash="abc123",
            form_fields=["username", "password"],
            critical_elements={"login": "form#login"},
            javascript_functions=["login()"],
            meta_info={"title": "Test Page"},
            status_code=200,
            response_time_ms=150
        )
        
        snapshot2 = PageSnapshot(
            url="https://example.com",
            timestamp="2025-08-30T12:05:00",
            content_hash="def456",  # Different hash
            form_fields=["username"],  # Missing password field
            critical_elements={"login": "form#newlogin"},  # Different selector
            javascript_functions=["newLogin()"],  # Different function
            meta_info={"title": "New Test Page"},  # Different title
            status_code=200,
            response_time_ms=160
        )
        
        changes = self.monitor.compare_snapshots(snapshot1, snapshot2)
        
        # Should detect multiple changes
        self.assertGreater(len(changes), 0)
        
        # Check for specific change types that actually exist
        change_types = [change.change_type for change in changes]
        
        # The actual change types are: 'content', 'form', 'element', 'javascript'
        self.assertIn("content", change_types)  # Content hash changed
        self.assertIn("form", change_types)  # Form fields changed
        self.assertIn("element", change_types)  # Critical elements changed
    
    def test_should_run_check_interval(self):
        """Test check interval logic."""
        # Should run check initially (no snapshots)
        self.assertTrue(self.monitor.should_run_check())
        
        # Add a recent snapshot
        recent_snapshot = PageSnapshot(
            url="https://example.com",
            timestamp=datetime.now().isoformat(),
            content_hash="abc123",
            form_fields=[],
            critical_elements={},
            javascript_functions=[],
            meta_info={},
            status_code=200,
            response_time_ms=150
        )
        self.monitor.snapshots = [recent_snapshot]
        
        # Should not run check immediately after (within interval)
        self.assertFalse(self.monitor.should_run_check())
    
    @patch.object(PortalAPIMonitor, 'capture_page_snapshot')
    def test_monitor_all_pages(self, mock_capture):
        """Test monitoring all configured pages."""
        # Mock successful snapshot capture
        mock_snapshot = PageSnapshot(
            url="https://example.com",
            timestamp="2025-08-30T12:00:00",
            content_hash="abc123",
            form_fields=["username"],
            critical_elements={"login": "form#login"},
            javascript_functions=["login()"],
            meta_info={"title": "Test Page"},
            status_code=200,
            response_time_ms=150
        )
        mock_capture.return_value = mock_snapshot
        
        # Set up minimal config for testing
        self.monitor.config.critical_pages = ["https://example.com"]
        
        snapshots, changes = self.monitor.monitor_all_pages()
        
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].url, "https://example.com")
        # First run should have no changes to compare against
        self.assertEqual(len(changes), 0)
    
    def test_generate_monitoring_report(self):
        """Test generating monitoring report."""
        # Add some test data
        test_snapshot = PageSnapshot(
            url="https://example.com",
            timestamp="2025-08-30T12:00:00",
            content_hash="abc123",
            form_fields=["username"],
            critical_elements={"login": "form#login"},
            javascript_functions=["login()"],
            meta_info={"title": "Test Page"},
            status_code=200,
            response_time_ms=150
        )
        
        test_change = ChangeDetection(
            change_type="form",
            severity="medium",
            description="Password field removed",
            old_value="password",
            new_value="",
            affected_functionality=["authentication"],
            recommended_action="Update form selectors",
            timestamp="2025-08-30T12:00:00"
        )
        
        self.monitor.snapshots = [test_snapshot]
        self.monitor.changes = [test_change]
        
        report = self.monitor.generate_monitoring_report()
        
        # Check for actual keys in the report
        self.assertIn("monitoring_status", report)
        self.assertIn("recent_changes", report)
        self.assertIn("total_changes_detected", report)
        self.assertEqual(report["total_changes_detected"], 1)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
