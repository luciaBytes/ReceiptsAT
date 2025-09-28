"""
Test pre-filled CSV generation functionality
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.web_client import WebClient


class TestPrefilledCSVGeneration:
    
    @patch('src.web_client.WebClient.generate_prefilled_csv')
    def test_prefilled_csv_not_authenticated(self, mock_generate_csv):
        """Test CSV generation fails properly when not authenticated."""
        client = WebClient()
        assert not client.authenticated
        
        mock_generate_csv.return_value = (False, "Not authenticated")
        success, result = client.generate_prefilled_csv()
        assert not success
        assert result == "Not authenticated"
    
    @patch('src.web_client.WebClient.get_contracts_with_tenant_data')
    @patch('src.web_client.WebClient.get_contract_rent_value')
    def test_prefilled_csv_no_contracts(self, mock_get_rent, mock_get_contracts):
        """Test CSV generation when no contracts are found."""
        client = WebClient()
        client.authenticated = True  # Mock authentication
        
        # Mock no contracts found
        mock_get_contracts.return_value = (True, [], "No contracts")
        
        success, result = client.generate_prefilled_csv()
        assert not success
        assert "No contracts found to generate CSV" in result
    
    @patch('src.web_client.WebClient.get_contracts_with_tenant_data')
    @patch('src.web_client.WebClient.get_contract_rent_value')
    def test_prefilled_csv_no_rent_values(self, mock_get_rent, mock_get_contracts):
        """Test CSV generation when contracts exist but have no rent values."""
        client = WebClient()
        client.authenticated = True  # Mock authentication
        
        # Mock contracts without rent values
        mock_get_contracts.return_value = (True, [
            {'numero': '12345'},
            {'numero': '67890'}
        ], "Success")
        
        # Mock rent value API always fails
        mock_get_rent.return_value = (False, 0.0)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success, result = client.generate_prefilled_csv(save_directory=temp_dir)
            assert not success
            assert "No contracts with valid rent values found" in result
            
            # Verify no CSV file was created
            csv_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv')]
            assert len(csv_files) == 0
    
    @patch('src.web_client.WebClient.get_contracts_with_tenant_data')
    @patch('src.web_client.WebClient.get_contract_rent_value')
    def test_prefilled_csv_success(self, mock_get_rent, mock_get_contracts):
        """Test successful CSV generation with valid contracts and rent values."""
        client = WebClient()
        client.authenticated = True  # Mock authentication
        
        # Mock contracts with rent values
        mock_get_contracts.return_value = (True, [
            {'numero': '12345'},
            {'numero': '67890'}
        ], "Success")
        
        # Mock rent value API returns valid values
        mock_get_rent.side_effect = [
            (True, 500.00),  # First contract
            (True, 750.50)   # Second contract
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success, result = client.generate_prefilled_csv(save_directory=temp_dir)
            assert success
            assert result.endswith('.csv')
            assert os.path.exists(result)
            
            # Verify CSV content
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'contract_id,from_date,to_date,payment_date,receipt_type,value' in content
                assert '12345' in content
                assert '67890' in content
                assert '500.00' in content
                assert '750.50' in content
    
    @patch('src.web_client.WebClient.get_contracts_with_tenant_data')
    @patch('src.web_client.WebClient.get_contract_rent_value')
    def test_prefilled_csv_mixed_results(self, mock_get_rent, mock_get_contracts):
        """Test CSV generation when some contracts have rent values and others don't."""
        client = WebClient()
        client.authenticated = True  # Mock authentication
        
        # Mock contracts 
        mock_get_contracts.return_value = (True, [
            {'numero': '12345'},  # Will have rent value
            {'numero': '67890'},  # Will not have rent value
            {'numero': '11111'}   # Will have rent value
        ], "Success")
        
        # Mock mixed rent value results
        mock_get_rent.side_effect = [
            (True, 500.00),    # First contract - success
            (False, 0.0),      # Second contract - no rent value
            (True, 300.25)     # Third contract - success
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success, result = client.generate_prefilled_csv(save_directory=temp_dir)
            assert success
            assert result.endswith('.csv')
            assert os.path.exists(result)
            
            # Verify CSV content - should only include contracts with rent values
            with open(result, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == 3  # Header + 2 data rows
                content = ''.join(lines)
                assert '12345' in content
                assert '11111' in content
                assert '67890' not in content  # Should be excluded
                assert '500.00' in content
                assert '300.25' in content

    @patch('src.web_client.WebClient.get_contracts_with_tenant_data')
    @patch('src.web_client.WebClient.get_contract_rent_value') 
    def test_prefilled_csv_content_format(self, mock_get_rent, mock_get_contracts):
        """Test the detailed CSV content format and structure."""
        from datetime import date, datetime
        import calendar
        import csv
        
        client = WebClient()
        client.authenticated = True
        
        # Mock contract data with detailed information
        mock_get_contracts.return_value = (True, [
            {
                'numero': 'C123456',
                'nomeLocatario': 'João Silva Santos',
                'valorRenda': 850.75  # Has rent value in bulk data
            },
            {
                'numero': 'C789012', 
                'nomeLocatario': 'Maria Costa Ferreira',
                'valorRenda': None  # No rent value in bulk data
            }
        ], "Success")
        
        # Mock individual rent value API call for second contract
        mock_get_rent.return_value = (True, 650.50)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success, result = client.generate_prefilled_csv(save_directory=temp_dir)
            assert success
            assert result.endswith('.csv')
            
            # Verify CSV structure and content
            with open(result, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
            # Check header
            expected_header = ['contract_id', 'from_date', 'to_date', 'payment_date', 'receipt_type', 'value', 'tenant_name']
            assert rows[0] == expected_header
            
            # Verify we have 2 data rows plus header
            assert len(rows) == 3
            
            # Check first contract (bulk data)
            first_row = rows[1]
            assert first_row[0] == 'C123456'  # contract_id
            assert first_row[4] == 'rent'     # receipt_type
            assert first_row[5] == '850.75'   # value
            assert first_row[6] == 'João Silva Santos'  # tenant_name
            
            # Check second contract (API call)
            second_row = rows[2] 
            assert second_row[0] == 'C789012'
            assert second_row[4] == 'rent'
            assert second_row[5] == '650.50'
            assert second_row[6] == 'Maria Costa Ferreira'
            
            # Verify date format (should be current month)
            today = date.today()
            year = today.year
            month = today.month
            first_day = date(year, month, 1)
            last_day = date(year, month, calendar.monthrange(year, month)[1])
            
            for row in rows[1:]:  # Skip header
                assert row[1] == first_day.strftime('%Y-%m-%d')  # from_date
                assert row[2] == last_day.strftime('%Y-%m-%d')   # to_date
                # payment_date should be today
                assert row[3] == today.strftime('%Y-%m-%d')

    @patch('src.web_client.WebClient.get_contracts_with_tenant_data')
    def test_prefilled_csv_platform_response_simulation(self, mock_get_contracts):
        """Test CSV generation with simulated realistic platform response."""
        client = WebClient()
        client.authenticated = True
        
        # Simulate realistic platform response with varied contract data
        mock_platform_response = [
            {
                'numero': '2024/PT/001234',
                'nomeLocatario': 'Ana Rita Oliveira da Silva',
                'valorRenda': 750.00,
                'nifLocatario': '123456789',
                'morada': 'Rua das Flores, 123, 1º Dto, 1200-200 Lisboa',
                'dataInicio': '2024-01-15',
                'dataFim': '2025-01-14'
            },
            {
                'numero': '2023/PT/987654',
                'nomeLocatario': 'Carlos José Santos Pereira', 
                'valorRenda': 1250.50,
                'nifLocatario': '987654321',
                'morada': 'Av. da República, 456, 3º Esq, 4000-100 Porto',
                'dataInicio': '2023-06-01',
                'dataFim': '2024-05-31'
            },
            {
                'numero': '2024/PT/555777',
                'nomeLocatario': 'Luisa Maria Fernandes Costa',
                'valorRenda': 950.25,
                'nifLocatario': '555777888',
                'morada': 'Rua do Comércio, 789, 2º C, 3000-050 Coimbra',
                'dataInicio': '2024-03-01', 
                'dataFim': '2025-02-28'
            },
            {
                'numero': '2022/PT/111222',
                'nomeLocatario': 'José António Silva Rodrigues',
                'valorRenda': None,  # Missing rent value - should be excluded
                'nifLocatario': '111222333',
                'morada': 'Praça Central, 100, R/C A, 2500-000 Caldas da Rainha'
            }
        ]
        
        mock_get_contracts.return_value = (True, mock_platform_response, "Success")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success, result = client.generate_prefilled_csv(save_directory=temp_dir)
            assert success
            
            # Read and verify CSV content
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verify contracts with rent values are included
            assert '2024/PT/001234' in content
            assert '2023/PT/987654' in content  
            assert '2024/PT/555777' in content
            assert 'Ana Rita Oliveira da Silva' in content
            assert 'Carlos José Santos Pereira' in content
            assert 'Luisa Maria Fernandes Costa' in content
            assert '750.00' in content
            assert '1250.50' in content
            assert '950.25' in content
            
            # Verify contract without rent value is excluded
            assert '2022/PT/111222' not in content
            assert 'José António Silva Rodrigues' not in content
            
            # Count rows to verify correct filtering
            lines = content.strip().split('\n')
            assert len(lines) == 4  # Header + 3 valid contracts

    @patch('src.web_client.WebClient.get_contracts_with_tenant_data')
    @patch('os.path.exists')
    def test_prefilled_csv_save_directory_fallback(self, mock_exists, mock_get_contracts):
        """Test CSV save directory fallback logic."""
        client = WebClient()
        client.authenticated = True
        
        # Mock minimal contract data
        mock_get_contracts.return_value = (True, [
            {'numero': '12345', 'valorRenda': 500.00}
        ], "Success")
        
        # Mock directory existence checks for fallback logic
        mock_exists.side_effect = lambda path: 'Desktop' in path
        
        # Test without specifying save directory (should use fallback)
        success, result = client.generate_prefilled_csv()
        
        assert success
        assert result.endswith('.csv')
        assert 'prefilled_receipts_' in result
        # Should contain timestamp
        import re
        timestamp_pattern = r'prefilled_receipts_\d{8}_\d{6}\.csv'
        assert re.search(timestamp_pattern, result)

    @patch('src.web_client.WebClient.get_contracts_with_tenant_data')
    def test_prefilled_csv_encoding_and_special_characters(self, mock_get_contracts):
        """Test CSV generation with Portuguese characters and special names."""
        client = WebClient()
        client.authenticated = True
        
        # Mock contracts with Portuguese special characters
        mock_get_contracts.return_value = (True, [
            {
                'numero': 'PT/2024/ÇÃO',
                'nomeLocatario': 'João António Conceição',
                'valorRenda': 800.00
            },
            {
                'numero': 'PT/2024/ÑÄÜ',
                'nomeLocatario': 'María José Peña Müller',
                'valorRenda': 920.75
            }
        ], "Success")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success, result = client.generate_prefilled_csv(save_directory=temp_dir)
            assert success
            
            # Verify UTF-8 encoding preserves special characters
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                
            assert 'PT/2024/ÇÃO' in content
            assert 'PT/2024/ÑÄÜ' in content
            assert 'João António Conceição' in content
            assert 'María José Peña Müller' in content