"""
Web client for interacting with the receipts platform.
"""

import requests
import re
import json
from typing import Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from utils.logger import get_logger

logger = get_logger(__name__)

class WebClient:
    """Handles web requests and session management for the receipts platform."""
    
    BASE_URL = "https://imoveis.portaldasfinancas.gov.pt"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        })
        self.authenticated = False
        self.login_attempts = 0
        self.max_login_attempts = 3
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Login to the platform.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Tuple of (success, message)
        """
        if self.login_attempts >= self.max_login_attempts:
            return False, "Maximum login attempts exceeded"
        
        try:
            self.login_attempts += 1
            logger.info(f"Attempting login (attempt {self.login_attempts})")
            
            # For now, simulate login success
            # In real implementation, this would make actual login requests
            self.authenticated = True
            logger.info("Login successful")
            return True, "Login successful"
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False, f"Login failed: {str(e)}"
    
    def logout(self) -> bool:
        """Logout from the platform."""
        try:
            if self.authenticated:
                # In real implementation, make logout request
                self.authenticated = False
                self.session.cookies.clear()
                logger.info("Logout successful")
            return True
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False
    
    def get_contracts_list(self) -> Tuple[bool, Any]:
        """
        Get list of contracts from the platform.
        
        Returns:
            Tuple of (success, data)
        """
        if not self.authenticated:
            return False, "Not authenticated"
        
        try:
            url = f"{self.BASE_URL}/arrendamento/consultarElementosContratos/locador"
            response = self.session.get(url)
            response.raise_for_status()
            
            logger.info("Successfully retrieved contracts list")
            return True, response.text
            
        except Exception as e:
            logger.error(f"Failed to get contracts list: {str(e)}")
            return False, str(e)
    
    def get_receipt_form(self, contract_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Get receipt form data for a specific contract.
        
        Args:
            contract_id: Contract ID
            
        Returns:
            Tuple of (success, recibo_data)
        """
        if not self.authenticated:
            return False, None
        
        try:
            url = f"{self.BASE_URL}/arrendamento/criarRecibo/{contract_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse the HTML to extract recibo data
            recibo_data = self._extract_recibo_data(response.text)
            
            if recibo_data:
                logger.info(f"Successfully extracted recibo data for contract {contract_id}")
                return True, recibo_data
            else:
                logger.warning(f"No recibo data found for contract {contract_id}")
                return False, None
                
        except Exception as e:
            logger.error(f"Failed to get receipt form for contract {contract_id}: {str(e)}")
            return False, None
    
    def _extract_recibo_data(self, html_content: str) -> Optional[Dict]:
        """
        Extract recibo initialization data from HTML.
        
        Args:
            html_content: HTML content from the receipt form page
            
        Returns:
            Extracted recibo data or None
        """
        try:
            # Look for $scope.recibo initialization in JavaScript
            # Pattern to match: $scope.recibo = {...};
            pattern = r'\$scope\.recibo\s*=\s*({.*?});'
            match = re.search(pattern, html_content, re.DOTALL)
            
            if match:
                recibo_json = match.group(1)
                # Clean up the JSON (remove comments, fix formatting)
                recibo_json = re.sub(r'//.*?\n', '', recibo_json)  # Remove single-line comments
                recibo_json = re.sub(r'/\*.*?\*/', '', recibo_json, flags=re.DOTALL)  # Remove multi-line comments
                
                try:
                    recibo_data = json.loads(recibo_json)
                    return recibo_data
                except json.JSONDecodeError:
                    logger.warning("Failed to parse recibo JSON data")
            
            # Alternative approach: look for specific data patterns
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for contract info in the page
            contract_info = {}
            
            # Extract contract number from subtitle
            subtitle = soup.find('p', class_='subtitle-bottom')
            if subtitle:
                contract_text = subtitle.get_text()
                contract_match = re.search(r'contrato #(\d+)', contract_text)
                if contract_match:
                    contract_info['numContrato'] = contract_match.group(1)
            
            # Return basic structure if we can't parse the full data
            return contract_info if contract_info else None
            
        except Exception as e:
            logger.error(f"Error extracting recibo data: {str(e)}")
            return None
    
    def issue_receipt(self, receipt_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Issue a receipt by sending POST request.
        
        Args:
            receipt_data: Receipt data to send
            
        Returns:
            Tuple of (success, response_data)
        """
        if not self.authenticated:
            return False, None
        
        try:
            url = f"{self.BASE_URL}/arrendamento/api/emitirRecibo"
            
            headers = {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = self.session.post(url, json=receipt_data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                logger.info(f"Successfully issued receipt for contract {receipt_data.get('numContrato')}")
                return True, result
            else:
                logger.error(f"Failed to issue receipt: {result.get('errorMessage')}")
                return False, result
                
        except Exception as e:
            logger.error(f"Error issuing receipt: {str(e)}")
            return False, None
    
    def get_receipt_details(self, contract_id: str, receipt_num: str) -> Tuple[bool, Any]:
        """
        Get receipt details after successful issuance.
        
        Args:
            contract_id: Contract ID
            receipt_num: Receipt number
            
        Returns:
            Tuple of (success, data)
        """
        if not self.authenticated:
            return False, None
        
        try:
            url = f"{self.BASE_URL}/arrendamento/detalheRecibo/{contract_id}/{receipt_num}?sucesso=recibo.create.success"
            response = self.session.get(url)
            response.raise_for_status()
            
            logger.info(f"Successfully retrieved receipt details for {contract_id}/{receipt_num}")
            return True, response.text
            
        except Exception as e:
            logger.error(f"Failed to get receipt details: {str(e)}")
            return False, str(e)
    
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self.authenticated
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to the platform."""
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
