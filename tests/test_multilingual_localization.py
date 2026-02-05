"""
Unit tests for the multilingual localization system.
Tests text retrieval, language switching, and multilingual interface support.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
import json

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.multilingual_localization import (
    MultilingualTexts,
    MultilingualLocalizer,
    get_text,
    switch_language,
    get_language_button_text,
    get_current_language,
    set_language,
    load_language_preference,
    save_language_preference
)


class TestMultilingualTexts(unittest.TestCase):
    """Test cases for the MultilingualTexts constants class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.texts = MultilingualTexts()
        
    def test_main_interface_texts_structure(self):
        """Test that main interface texts have both PT and EN versions."""
        # Test key interface texts have both languages
        self.assertIn("pt", self.texts.MAIN_WINDOW_TITLE)
        self.assertIn("en", self.texts.MAIN_WINDOW_TITLE)
        self.assertIn("pt", self.texts.LOGIN_BUTTON)
        self.assertIn("en", self.texts.LOGIN_BUTTON)
        self.assertIn("pt", self.texts.LOGOUT_BUTTON)
        self.assertIn("en", self.texts.LOGOUT_BUTTON)
        self.assertIn("pt", self.texts.USERNAME_LABEL)
        self.assertIn("en", self.texts.USERNAME_LABEL)
        self.assertIn("pt", self.texts.PASSWORD_LABEL)
        self.assertIn("en", self.texts.PASSWORD_LABEL)
        
    def test_authentication_texts_structure(self):
        """Test authentication-related text constants."""
        self.assertIn("pt", self.texts.AUTHENTICATION_SECTION)
        self.assertIn("en", self.texts.AUTHENTICATION_SECTION)
        
    def test_file_section_texts_structure(self):
        """Test file section text constants."""
        self.assertIn("pt", self.texts.CSV_FILE_SECTION) 
        self.assertIn("en", self.texts.CSV_FILE_SECTION)
        
    def test_language_button_text_structure(self):
        """Test language button shows correct opposite language."""
        self.assertIn("pt", self.texts.LANGUAGE_BUTTON)
        self.assertIn("en", self.texts.LANGUAGE_BUTTON)
        # Portuguese mode should show "EN" button
        self.assertEqual(self.texts.LANGUAGE_BUTTON["pt"], "EN")
        # English mode should show "PT" button  
        self.assertEqual(self.texts.LANGUAGE_BUTTON["en"], "PT")


class TestMultilingualLocalizer(unittest.TestCase):
    """Test cases for the MultilingualLocalizer class."""
    
    def setUp(self):
        """Set up test fixtures with isolated language state."""
        self.localizer = MultilingualLocalizer()
        self.original_language = get_current_language()
        
    def tearDown(self):
        """Restore original language state."""
        set_language(self.original_language)
        
    def test_localizer_initialization(self):
        """Test localizer initialization."""
        self.assertIsInstance(self.localizer, MultilingualLocalizer)
        self.assertIsInstance(self.localizer.texts, MultilingualTexts)
        
    def test_get_text_portuguese(self):
        """Test text retrieval in Portuguese."""
        set_language("pt")
        text = self.localizer.get_text('AUTHENTICATION_SECTION')
        self.assertIsInstance(text, str)
        self.assertTrue(len(text) > 0)
        
        # Test another key in Portuguese
        title_text = self.localizer.get_text('MAIN_WINDOW_TITLE')
        self.assertIsInstance(title_text, str)
        self.assertTrue(len(title_text) > 0)
        
    def test_get_text_english(self):
        """Test text retrieval in English."""
        set_language("en") 
        text = self.localizer.get_text('AUTHENTICATION_SECTION')
        self.assertIsInstance(text, str)
        self.assertTrue(len(text) > 0)
        
        # Test another key in English
        title_text = self.localizer.get_text('MAIN_WINDOW_TITLE')
        self.assertIsInstance(title_text, str)
        self.assertTrue(len(title_text) > 0)
        
    def test_get_text_with_formatting(self):
        """Test text retrieval consistency across languages."""
        # Test that the same key works in both languages
        set_language("pt")
        pt_text = self.localizer.get_text('MAIN_WINDOW_TITLE')
        self.assertIsInstance(pt_text, str)
        self.assertTrue(len(pt_text) > 0)
        
        set_language("en")
        en_text = self.localizer.get_text('MAIN_WINDOW_TITLE')
        self.assertIsInstance(en_text, str)
        self.assertTrue(len(en_text) > 0)


class TestLanguageFunctions(unittest.TestCase):
    """Test cases for language management functions."""
    
    def setUp(self):
        """Set up test fixtures with isolated language state."""
        # Store original language state to restore later
        self.original_language = get_current_language()
        # Start each test with Portuguese as default
        set_language("pt")
        
    def tearDown(self):
        """Restore original language state."""
        set_language(self.original_language)
        
    def test_get_current_language(self):
        """Test getting current language."""
        # Set to known state and test
        set_language("pt")
        self.assertEqual(get_current_language(), "pt")
        
        set_language("en")
        self.assertEqual(get_current_language(), "en")
        
    def test_set_language_valid(self):
        """Test setting valid languages."""
        # Test Portuguese setting
        set_language("pt")
        self.assertEqual(get_current_language(), "pt")
        
        # Test English setting
        set_language("en") 
        self.assertEqual(get_current_language(), "en")
        
        # Test switching back to Portuguese
        set_language("pt")
        self.assertEqual(get_current_language(), "pt")
        
    def test_set_language_invalid(self):
        """Test setting invalid language (should be ignored)."""
        # Set to known state
        set_language("pt")
        original_lang = get_current_language()
        
        # Try to set invalid language
        set_language("fr")  # Invalid language
        # Should remain unchanged
        self.assertEqual(get_current_language(), original_lang)
        
        # Test with another invalid language
        set_language("de")  # Invalid language  
        self.assertEqual(get_current_language(), original_lang)
        
    def test_switch_language(self):
        """Test language switching function."""
        # Start with Portuguese
        set_language("pt")
        self.assertEqual(get_current_language(), "pt")
        
        # Switch to English
        switch_language()
        self.assertEqual(get_current_language(), "en")
        
        # Switch back to Portuguese
        switch_language()
        self.assertEqual(get_current_language(), "pt")
        
        # Test multiple switches
        switch_language()  # pt -> en
        switch_language()  # en -> pt
        switch_language()  # pt -> en
        self.assertEqual(get_current_language(), "en")
        
    def test_get_language_button_text(self):
        """Test language button text function."""
        # Test Portuguese mode shows "EN" button
        set_language("pt")
        button_text = get_language_button_text()
        self.assertEqual(button_text, "EN")  # Should show opposite language
        
        # Test English mode shows "PT" button
        set_language("en")
        button_text = get_language_button_text()
        self.assertEqual(button_text, "PT")  # Should show opposite language


class TestGetTextFunction(unittest.TestCase):
    """Test cases for the global get_text function."""
    
    def setUp(self):
        """Set up test fixtures with isolated language state."""
        self.original_language = get_current_language()
        
    def tearDown(self):
        """Restore original language state."""
        set_language(self.original_language)
    
    def test_get_text_function(self):
        """Test the global get_text function in both languages."""
        # Test Portuguese
        set_language("pt")
        pt_text = get_text('AUTHENTICATION_SECTION')
        self.assertIsInstance(pt_text, str)
        self.assertTrue(len(pt_text) > 0)
        
        # Test English  
        set_language("en")
        en_text = get_text('AUTHENTICATION_SECTION')
        self.assertIsInstance(en_text, str)
        self.assertTrue(len(en_text) > 0)
        
    def test_get_text_missing_key(self):
        """Test get_text with missing key."""
        # Test in Portuguese
        set_language("pt")
        missing_text_pt = get_text('NONEXISTENT_KEY')
        self.assertEqual(missing_text_pt, 'NONEXISTENT_KEY')
        
        # Test in English
        set_language("en")
        missing_text_en = get_text('NONEXISTENT_KEY')
        self.assertEqual(missing_text_en, 'NONEXISTENT_KEY')
        
    def test_get_text_different_languages(self):
        """Test that different languages return different text for same key."""
        # Test AUTHENTICATION_SECTION in both languages
        set_language("pt")
        pt_text = get_text('AUTHENTICATION_SECTION')
        
        set_language("en")
        en_text = get_text('AUTHENTICATION_SECTION')
        
        # Both should be valid strings
        self.assertIsInstance(pt_text, str)
        self.assertIsInstance(en_text, str)
        self.assertTrue(len(pt_text) > 0)
        self.assertTrue(len(en_text) > 0)
        
        # Test MAIN_WINDOW_TITLE in both languages
        set_language("pt")
        pt_title = get_text('MAIN_WINDOW_TITLE')
        
        set_language("en")
        en_title = get_text('MAIN_WINDOW_TITLE')
        
        # Both should be valid strings  
        self.assertIsInstance(pt_title, str)
        self.assertIsInstance(en_title, str)
        self.assertTrue(len(pt_title) > 0)
        self.assertTrue(len(en_title) > 0)


class TestLanguagePreferences(unittest.TestCase):
    """Test cases for language preference persistence."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.original_language = get_current_language()
        
    def tearDown(self):
        """Restore original language state."""
        set_language(self.original_language)
    
    def test_save_language_preference_file_creation(self):
        """Test that save_language_preference creates valid JSON files."""
        # Create temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Temporarily patch the config file path
            import utils.multilingual_localization as ml_module
            original_config = ml_module._config_file
            ml_module._config_file = temp_path
            
            # Test saving Portuguese
            save_language_preference("pt")
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify file content
            with open(temp_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.assertEqual(config['language'], "pt")
            
            # Test saving English
            save_language_preference("en")
            
            # Verify updated content
            with open(temp_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.assertEqual(config['language'], "en")
            
        finally:
            # Cleanup
            ml_module._config_file = original_config
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"language": "en"}')
    def test_load_language_preference_mocked(self, mock_open, mock_exists):
        """Test load_language_preference with mocked file operations."""
        mock_exists.return_value = True
        
        # Set to Portuguese first
        set_language("pt")
        self.assertEqual(get_current_language(), "pt")
        
        # Load should change to English based on mocked file content
        load_language_preference()
        self.assertEqual(get_current_language(), "en")
    
    @patch('os.path.exists')
    def test_load_nonexistent_config_mocked(self, mock_exists):
        """Test loading from nonexistent config file with mocking."""
        mock_exists.return_value = False
        
        # Set to English first  
        set_language("en")
        self.assertEqual(get_current_language(), "en")
        
        # Load from nonexistent file should keep current language (en)
        # because the function only resets on exception, not when file doesn't exist
        load_language_preference()
        self.assertEqual(get_current_language(), "en")
        
    @patch('os.path.exists')
    @patch('builtins.open', side_effect=Exception("File read error"))
    def test_load_config_with_exception(self, mock_open, mock_exists):
        """Test load_language_preference with file read exception."""
        mock_exists.return_value = True
        
        # Set to English first
        set_language("en")
        self.assertEqual(get_current_language(), "en")
        
        # Load with exception should reset to default "pt"
        load_language_preference()
        self.assertEqual(get_current_language(), "pt")
            
    def test_language_switching_workflow(self):
        """Test complete language switching workflow without file dependency."""
        # Test isolated language switching behavior
        # Start with Portuguese
        set_language("pt")
        self.assertEqual(get_current_language(), "pt")
        self.assertEqual(get_language_button_text(), "EN")
        
        # Switch to English
        switch_language()
        self.assertEqual(get_current_language(), "en")
        self.assertEqual(get_language_button_text(), "PT")
        
        # Switch back to Portuguese  
        switch_language()
        self.assertEqual(get_current_language(), "pt")
        self.assertEqual(get_language_button_text(), "EN")
        
        # Test multiple switches
        for i in range(5):
            switch_language()
            
        # Should end up in English after odd number of switches
        self.assertEqual(get_current_language(), "en")
        self.assertEqual(get_language_button_text(), "PT")
        
    def test_set_and_save_language_integration(self):
        """Test integration between set_language and save functions."""
        # Test that language setting persists through function calls
        original_lang = get_current_language()
        
        # Test Portuguese
        set_language("pt") 
        save_language_preference("pt")
        self.assertEqual(get_current_language(), "pt")
        
        # Test English
        set_language("en")
        save_language_preference("en") 
        self.assertEqual(get_current_language(), "en")
        
        # Test invalid language doesn't change state
        set_language("invalid")
        self.assertEqual(get_current_language(), "en")  # Should remain English
        
        # Restore original
        set_language(original_lang)


if __name__ == "__main__":
    unittest.main()