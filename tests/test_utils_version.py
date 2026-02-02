"""
Unit tests for utils.version module.
Tests version retrieval from different execution contexts.
"""

import pytest
import os
import sys
from unittest.mock import patch, mock_open, MagicMock

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import version


class TestGetVersion:
    """Test get_version function."""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='1.2.3\n')
    def test_get_version_reads_file(self, mock_file, mock_exists):
        """Test that get_version reads from .version file."""
        mock_exists.return_value = True
        
        result = version.get_version()
        
        assert result == '1.2.3'
        mock_file.assert_called()
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='  1.0.0  \n')
    def test_get_version_strips_whitespace(self, mock_file, mock_exists):
        """Test that version string is stripped of whitespace."""
        mock_exists.return_value = True
        
        result = version.get_version()
        
        assert result == '1.0.0'
        assert not result.startswith(' ')
        assert not result.endswith(' ')
    
    @patch('os.path.exists')
    def test_get_version_file_not_found(self, mock_exists):
        """Test fallback when .version file doesn't exist."""
        mock_exists.return_value = False
        
        result = version.get_version()
        
        # Should return a default version
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('os.path.exists')
    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    def test_get_version_permission_error(self, mock_file, mock_exists):
        """Test handling of permission errors when reading version file."""
        mock_exists.return_value = True
        
        result = version.get_version()
        
        # Should handle error gracefully and return default
        assert isinstance(result, str)


class TestVersionInPyInstallerContext:
    """Test version retrieval in PyInstaller executable context."""
    
    @patch('sys._MEIPASS', '/path/to/frozen/app', create=True)
    @patch('sys.executable', '/path/to/frozen/app/myapp.exe')
    @patch('os.path.dirname')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='2.0.0\n')
    def test_get_version_pyinstaller_mode(self, mock_file, mock_exists, mock_dirname):
        """Test version retrieval when running as PyInstaller executable."""
        mock_exists.return_value = True
        mock_dirname.return_value = '/path/to/frozen/app'
        
        result = version.get_version()
        
        assert result == '2.0.0'


class TestVersionInScriptContext:
    """Test version retrieval when running as a script."""
    
    @patch('os.path.abspath')
    @patch('os.path.dirname')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='1.5.0\n')
    def test_get_version_script_mode(self, mock_file, mock_exists, mock_dirname, mock_abspath):
        """Test version retrieval when running as a Python script."""
        mock_exists.return_value = True
        # Simulate directory structure: src/utils/version.py -> project_root
        mock_abspath.return_value = '/project/src/utils/version.py'
        mock_dirname.side_effect = lambda p: '/project/src/utils' if 'version.py' in p else '/project/src' if 'utils' in p else '/project'
        
        result = version.get_version()
        
        assert result == '1.5.0'


class TestVersionFileFormats:
    """Test handling of different version file formats."""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='v1.0.0\n')
    def test_version_with_v_prefix(self, mock_file, mock_exists):
        """Test version string with 'v' prefix."""
        mock_exists.return_value = True
        
        result = version.get_version()
        
        # Should handle 'v' prefix (depending on implementation)
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='1.0.0-beta\n')
    def test_version_with_suffix(self, mock_file, mock_exists):
        """Test version with pre-release suffix."""
        mock_exists.return_value = True
        
        result = version.get_version()
        
        assert '1.0.0' in result
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='')
    def test_empty_version_file(self, mock_file, mock_exists):
        """Test handling of empty version file."""
        mock_exists.return_value = True
        
        result = version.get_version()
        
        # Should return a default or handle gracefully
        assert isinstance(result, str)


class TestVersionCaching:
    """Test version caching behavior if implemented."""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='1.0.0\n')
    def test_multiple_calls_return_same_version(self, mock_file, mock_exists):
        """Test that multiple calls return consistent version."""
        mock_exists.return_value = True
        
        result1 = version.get_version()
        result2 = version.get_version()
        
        assert result1 == result2


class TestGetVersionInfo:
    """Test get_version_info if it exists."""
    
    def test_get_version_info_exists(self):
        """Test if get_version_info function exists and is callable."""
        if hasattr(version, 'get_version_info'):
            assert callable(version.get_version_info)
    
    @patch('utils.version.get_version', return_value='1.2.3')
    def test_get_version_info_returns_dict(self, mock_get_version):
        """Test get_version_info returns structured data if implemented."""
        if hasattr(version, 'get_version_info'):
            result = version.get_version_info()
            assert isinstance(result, dict)


class TestVersionFormatting:
    """Test version string formatting and handling."""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='v1.2.3\n')
    def test_version_with_leading_v(self, mock_file, mock_exists):
        """Test handling of version strings with leading 'v'."""
        mock_exists.return_value = True
        
        result = version.get_version()
        # Should handle both with and without 'v' prefix
        assert '1.2.3' in result
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='1.2.3-beta\n')
    def test_version_with_suffix(self, mock_file, mock_exists):
        """Test version strings with suffixes like -beta, -alpha."""
        mock_exists.return_value = True
        
        result = version.get_version()
        assert '1.2.3' in result


class TestModuleFunctions:
    """Test module-level functions and attributes."""
    
    def test_version_module_has_get_version(self):
        """Test that get_version function exists."""
        assert hasattr(version, 'get_version')
        assert callable(version.get_version)
    
    def test_get_version_returns_string(self):
        """Test that get_version always returns a string."""
        result = version.get_version()
        assert isinstance(result, str)
        assert len(result) > 0
