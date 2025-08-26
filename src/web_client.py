"""
Web client for interacting with the Portal das Finanças.
This module handles real authentication and web interactions with the Portuguese Tax Authority platform.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import json
from typing import Dict, Tuple, Any, Optional, List
from urllib.parse import urljoin, urlparse

try:
    from .utils.logger import get_logger
except ImportError:
    # Fallback for when imported directly
    from utils.logger import get_logger

logger = get_logger(__name__)

class WebClient:
    """Web client for Portal das Finanças interactions."""
    
    def __init__(self, testing_mode: bool = False):
        """
        Initialize WebClient.
        
        Args:
            testing_mode: If True, enables mock authentication for testing
        """
        self.testing_mode = testing_mode
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-PT,pt;q=0.9,pt-BR;q=0.8,en;q=0.7,en-US;q=0.6,en-GB;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        self.authenticated = False
        self.pending_2fa = False  # Flag to track if 2FA is pending
        self.auth_base_url = "https://www.acesso.gov.pt"
        # Updated login URLs based on actual Portuguese government authentication system
        # Using the original /v2/login endpoint that matches the HTTP request
        self.login_page_url = f"{self.auth_base_url}/v2/loginForm?partID=PFAP"
        self.login_url = f"{self.auth_base_url}/v2/login"
        self.receipts_base_url = "https://imoveis.portaldasfinancas.gov.pt"
        self._csrf_token = None
        self._session_id = None
        self.login_attempts = 0
        self.max_login_attempts = 3
        self._current_username = None  # Store username for 2FA verification
        
        # Keep SSL verification enabled for security
        self.session.verify = True
        
        # Cache for contract data to avoid duplicate requests
        self._cached_contracts = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # Cache for 5 minutes (300 seconds)
        
        mode_info = "testing mode" if testing_mode else "production mode"
        logger.info(f"WebClient initialized in {mode_info}")
        if not testing_mode:
            logger.info("WebClient initialized for Autenticação.Gov authentication")
            logger.info(f"Login page URL: {self.login_page_url}")
            logger.info(f"Login action URL: {self.login_url}")
        else:
            logger.info("Testing mode enabled - using mock authentication")
    
    def _is_cache_valid(self) -> bool:
        """Check if cached contract data is still valid."""
        if self._cached_contracts is None or self._cache_timestamp is None:
            return False
        
        import time
        current_time = time.time()
        return (current_time - self._cache_timestamp) < self._cache_ttl
    
    def _clear_cache(self):
        """Clear cached contract data."""
        self._cached_contracts = None
        self._cache_timestamp = None
        logger.info("Cleared contract data cache")
    
    def _find_credential_fields(self) -> Tuple[str, str]:
        """Find the actual username and password field names for SPA authentication."""
        # For the Portuguese government SPA, the field names are standard
        # Based on the JavaScript configuration and common patterns
        logger.info("Using standard SPA credential field names")
        
        # Standard field names for Portuguese government authentication
        username_field = "username"  # Could also be "utilizador" or "email"
        password_field = "password"  # Could also be "palavrapasse"
        
        logger.info(f"Using credential fields: {username_field}, {password_field}")
        return username_field, password_field

    def _set_login_headers(self):
        """Set appropriate headers for login form submission."""
        login_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'pt-PT,pt;q=0.9,pt-BR;q=0.8,en;q=0.7,en-US;q=0.6,en-GB;q=0.5',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.auth_base_url,
            'Referer': self.login_page_url,
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        self.session.headers.update(login_headers)

    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to the Autenticação.Gov platform or return mock response in testing mode."""
        if self.testing_mode:
            logger.info("Testing connection (mock mode)")
            return True, "Mock connection successful"
        
        try:
            logger.info("Testing connection to Autenticação.Gov...")
            
            response = self.session.get(self.login_page_url, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Connection response: Status {response.status_code}, URL: {response.url}")
            
            # Check for login page indicators
            response_lower = response.text.lower()
            if (any(indicator in response_lower for indicator in [
                "autenticação.gov", "acesso.gov.pt", "autenticacao.gov", 
                "login", "utilizador", "password", "palavra-passe",
                "entrar", "iniciar sessão", "autenticar"]) or
                "form" in response_lower):
                logger.info("Connection test successful - login page detected")
                return True, "Connection successful"
            else:
                logger.warning("Login page not detected in response")
                return False, "Unexpected response from server - login page not detected"
                
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Autenticação.Gov - check internet connection"
            logger.error(error_msg)
            return False, error_msg
        except requests.exceptions.Timeout:
            error_msg = "Connection timeout - server may be overloaded"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False, str(e)
    
    def _get_csrf_token_data(self) -> Optional[Dict[str, str]]:
        """Extract CSRF token data from login page for secure form submission."""
        try:
            logger.info("Extracting CSRF token data from login page...")
            
            response = self.session.get(self.login_page_url, timeout=10)
            response.raise_for_status()
            
            import re
            import json
            
            # Look for the specific CSRF object pattern found in the JavaScript
            # Pattern: { parameterName: `_csrf`, token: `token-value` }
            csrf_object_pattern = r'{\s*parameterName\s*:\s*`([^`]+)`\s*,\s*token\s*:\s*`([^`]+)`\s*}'
            match = re.search(csrf_object_pattern, response.text, re.IGNORECASE | re.DOTALL)
            
            if match:
                param_name = match.group(1)
                token_value = match.group(2)
                logger.info(f"Found CSRF object: parameterName='{param_name}', token='{token_value[:10]}...{token_value[-4:]}'")
                return {
                    'parameterName': param_name,
                    'token': token_value
                }
            
            # Alternative pattern with quotes instead of backticks
            csrf_object_pattern2 = r'{\s*parameterName\s*:\s*["\']([^"\']+)["\']\s*,\s*token\s*:\s*["\']([^"\']+)["\']\s*}'
            match = re.search(csrf_object_pattern2, response.text, re.IGNORECASE | re.DOTALL)
            
            if match:
                param_name = match.group(1)
                token_value = match.group(2)
                logger.info(f"Found CSRF object (alt pattern): parameterName='{param_name}', token='{token_value[:10]}...{token_value[-4:]}'")
                return {
                    'parameterName': param_name,
                    'token': token_value
                }
            
            # Look for separate parameterName and token assignments
            param_pattern = r'parameterName\s*:\s*[`"\']([^`"\']+)[`"\']'
            token_pattern = r'token\s*:\s*[`"\']([^`"\']+)[`"\']'
            
            param_match = re.search(param_pattern, response.text, re.IGNORECASE)
            token_match = re.search(token_pattern, response.text, re.IGNORECASE)
            
            if param_match and token_match:
                param_name = param_match.group(1)
                token_value = token_match.group(1)
                logger.info(f"Found separate CSRF components: parameterName='{param_name}', token='{token_value[:10]}...{token_value[-4:]}'")
                return {
                    'parameterName': param_name,
                    'token': token_value
                }
            
            # Look for CSRF data in JSON script tags
            script_patterns = [
                r'<script[^>]*type=["\']application/json["\'][^>]*>([^<]+)</script>'
            ]
            
            for pattern in script_patterns:
                matches = re.findall(pattern, response.text)
                for script_content in matches:
                    try:
                        data = json.loads(script_content)
                        # Look for _csrf object in the JSON data
                        if '_csrf' in data and isinstance(data['_csrf'], dict):
                            csrf_data = data['_csrf']
                            if 'parameterName' in csrf_data and 'token' in csrf_data:
                                logger.info(f"Found CSRF in JSON script: parameterName='{csrf_data['parameterName']}', token='{csrf_data['token'][:10]}...{csrf_data['token'][-4:]}'")
                                return csrf_data
                    except json.JSONDecodeError:
                        continue
            
            # Fallback: Look for traditional CSRF patterns
            csrf_token_patterns = [
                r'<meta name="csrf-token" content="([^"]+)"',
                r'<input[^>]+name="[^"]*csrf[^"]*"[^>]+value="([^"]+)"',
                r'<input[^>]+value="([^"]+)"[^>]+name="[^"]*csrf[^"]*"',
                r'"csrf[^"]*token[^"]*"\s*:\s*"([^"]+)"',
                r'csrf_token[\'"]?\s*:\s*[\'"]([^\'"]+)[\'"]'
            ]
            
            for pattern in csrf_token_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    csrf_token = match.group(1)
                    logger.info(f"Found CSRF token (fallback): {csrf_token[:10]}...{csrf_token[-4:]}")
                    return {
                        'parameterName': '_token',  # Default parameter name
                        'token': csrf_token
                    }
            
            # Check cookies for CSRF token
            for cookie in self.session.cookies:
                if 'csrf' in cookie.name.lower() or 'xsrf' in cookie.name.lower():
                    logger.info(f"Found CSRF token in cookie: {cookie.name}")
                    return {
                        'parameterName': cookie.name,
                        'token': cookie.value
                    }
            
            logger.warning("No CSRF token found in page, JSON, cookies, or headers")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract CSRF token data: {str(e)}")
            return None

    def _get_login_form_data(self) -> Optional[Dict[str, str]]:
        """Get login form data from the modern SPA-based authentication system."""
        try:
            logger.info("Fetching login form data from modern SPA...")
            
            # Make sure we visit the login page first to establish session cookies
            response = self.session.get(self.login_page_url, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Login page response: Status {response.status_code}")
            logger.info(f"Cookies received: {[f'{c.name}={c.value[:10]}...' for c in self.session.cookies]}")
            
            # The new system uses JSON script tags for configuration instead of inline JavaScript
            import re
            import json
            
            # Extract partID from JSON data-attributes script
            data_attr_pattern = r'<script id="data-attributes" type="application/json">([^<]+)</script>'
            data_attr_match = re.search(data_attr_pattern, response.text)
            
            form_data = {}
            
            if data_attr_match:
                try:
                    data_attrs = json.loads(data_attr_match.group(1))
                    if 'partID' in data_attrs:
                        form_data['partID'] = data_attrs['partID']
                        logger.info(f"Extracted partID from JSON: {data_attrs['partID']}")
                except json.JSONDecodeError:
                    logger.warning("Failed to parse data-attributes JSON")
            
            # Extract root-data attributes for form submission configuration
            root_data_pattern = r'<div id="root-data"([^>]+)>'
            root_data_match = re.search(root_data_pattern, response.text)
            
            if root_data_match:
                # Extract data attributes
                attr_text = root_data_match.group(1)
                
                # Parse data-submit-* attributes which indicate form submission parameters
                data_attrs = re.findall(r'data-([^=]+)="([^"]*)"', attr_text)
                for attr_name, attr_value in data_attrs:
                    if attr_name.startswith('submit-nif-form-'):
                        # These are form configuration attributes
                        config_key = attr_name.replace('submit-nif-form-', '')
                        if config_key == 'allow-personal-data':
                            form_data['envioDadosPessoais'] = 'true' if attr_value.lower() == 'true' else 'false'
                        elif config_key == 'selected-auth-method':
                            form_data['selectedAuthMethod'] = attr_value or 'N'  # Default to NIF
                
                logger.info("Extracted SPA configuration from root-data attributes")
            
            # For the modern system, we need to simulate the form submission
            # Based on real working request: partID, selectedAuthMethod, authVersion, _csrf
            if 'partID' not in form_data:
                form_data['partID'] = 'PFAP'  # Default value from URL parameter
                
            if 'selectedAuthMethod' not in form_data:
                form_data['selectedAuthMethod'] = 'N'  # N for NIF authentication
            
            # Add authentication version (required in working request)
            form_data['authVersion'] = '2'
            
            # Remove fields not present in working request
            form_data.pop('envioDadosPessoais', None)
            form_data.pop('isMultipleAuthentication', None)
            
            logger.info(f"Prepared modern SPA form data with {len(form_data)} fields")
            logger.info(f"Form data keys: {list(form_data.keys())}")
            
            return form_data
            
        except Exception as e:
            logger.error(f"Failed to get modern SPA login form data: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _establish_session(self) -> bool:
        """Establish a proper session by visiting the Portal das Finanças first."""
        try:
            logger.info("Establishing session with Portal das Finanças...")
            
            # Visit the main portal first to establish session
            portal_url = "https://www.portaldasfinancas.gov.pt"
            response = self.session.get(portal_url, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Portal visit successful: {response.status_code}")
            
            # Then visit the login page to get proper cookies
            response = self.session.get(self.login_page_url, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Login page visit successful: {response.status_code}")
            logger.info(f"Session cookies: {[f'{c.name}={c.value[:10]}...' for c in self.session.cookies]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to establish session: {str(e)}")
            return False

    def login(self, username: str, password: str, sms_code: str = None) -> Tuple[bool, str]:
        """Login to Autenticação.Gov with optional 2FA SMS verification."""
        if self.login_attempts >= self.max_login_attempts:
            return False, "Maximum login attempts exceeded. Please wait before trying again."
        
        # Handle testing mode
        if self.testing_mode:
            return self._mock_login(username, password, sms_code)
        
        try:
            # If SMS code is provided, this is a 2FA verification step
            if sms_code:
                return self._verify_2fa_sms(sms_code)
            
            # Establish proper session first
            if not self._establish_session():
                return False, "Failed to establish session with authentication server"
            
            # Initial login attempt
            self.login_attempts += 1
            logger.info(f"Attempting login (attempt {self.login_attempts})")
            
            # Get login form data
            form_data = self._get_login_form_data()
            if not form_data:
                return False, "Failed to retrieve login form"
            
            # Get CSRF token data for secure submission
            csrf_data = self._get_csrf_token_data()
            if csrf_data:
                form_data[csrf_data['parameterName']] = csrf_data['token']
                logger.info(f"Added CSRF token to form data: {csrf_data['parameterName']}={csrf_data['token'][:10]}...{csrf_data['token'][-4:]}")
            
            # Add credentials to form data in exact format matching working request
            form_data.update({
                'username': username,           # Should be Portuguese NIF (tax ID), not email
                'password': password,
                'selectedAuthMethod': 'N',      # N for NIF authentication  
                'authVersion': '2'              # Required version field
            })
            
            # Remove fields that aren't in the working request
            form_data.pop('envioDadosPessoais', None)
            form_data.pop('isMultipleAuthentication', None)
            
            # Store username for potential 2FA verification
            self._current_username = username
            
            logger.info(f"Prepared login form with {len(form_data)} fields")
            logger.info(f"Form data keys: {list(form_data.keys())}")
            
            # Try JSON submission first (modern approach)
            try:
                logger.info("Attempting JSON login submission...")
                
                json_headers = {
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
                    'Content-Type': 'application/json',
                    'Origin': self.auth_base_url,
                    'Referer': self.login_page_url,
                    'X-Requested-With': 'XMLHttpRequest',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
                    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
                }
                
                if csrf_data:
                    json_headers['X-CSRF-Token'] = csrf_data['token']
                
                json_response = self.session.post(
                    self.login_url,
                    json=form_data,
                    headers=json_headers,
                    timeout=15,
                    allow_redirects=False  # Handle redirects manually
                )
                
                logger.info(f"JSON login response: Status {json_response.status_code}")
                logger.info(f"JSON response content: {json_response.text[:200]}")
                
                if json_response.status_code == 200:
                    logger.info("JSON login submission successful")
                    return self._analyze_login_response(json_response)
                elif json_response.status_code in [302, 303, 307, 308]:
                    # Handle redirect manually
                    redirect_url = json_response.headers.get('Location')
                    if redirect_url:
                        logger.info(f"Following redirect to: {redirect_url}")
                        redirect_response = self.session.get(redirect_url, timeout=15)
                        return self._analyze_login_response(redirect_response)
                elif json_response.status_code == 403:
                    if 'invalidCsrfToken' in json_response.text:
                        logger.warning("CSRF token invalid, falling back to form submission")
                    else:
                        logger.warning(f"403 Forbidden: {json_response.text[:100]}")
                    # Fall through to form submission
                else:
                    logger.warning(f"JSON submission failed with {json_response.status_code}: {json_response.text[:100]}")
                    # Fall through to form submission
                    
            except Exception as json_error:
                logger.warning(f"JSON submission error: {json_error}, falling back to form submission")
            
            # Fallback to traditional form submission
            logger.info("Attempting traditional form submission...")
            
            # Set headers for form submission
            self._set_login_headers()
            
            # Submit login form
            logger.info("Submitting login credentials...")
            response = self.session.post(
                self.login_url,
                data=form_data,
                timeout=15,
                allow_redirects=True
            )
            response.raise_for_status()
            
            logger.info(f"Login response: Status {response.status_code}, URL: {response.url}")
            
            # Analyze response to determine login success or 2FA requirement
            return self._analyze_login_response(response)
            
        except requests.exceptions.ConnectionError:
            error_msg = "Connection failed - check internet connection"
            logger.error(error_msg)
            return False, error_msg
        except requests.exceptions.Timeout:
            error_msg = "Login timeout - server may be overloaded"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False, f"Login error: {str(e)}"
    
    def _analyze_login_response(self, response: requests.Response) -> Tuple[bool, str]:
        """Analyze login response to determine success, failure, or 2FA requirement."""
        response_text = response.text.lower()
        response_url = response.url.lower()
        
        logger.info(f"Login response analysis: Status {response.status_code}, URL: {response.url}")
        
        # Check for 2FA requirement (SMS verification)
        # Only trigger 2FA when portal explicitly indicates it's required
        
        # More precise 2FA detection - look for specific indicators
        is_2fa_required = False
        
        # Primary check: JavaScript is2FA flag set to true
        if ('is2fa: parseboolean(\'true\')' in response_text or 
            'is2fa: true' in response_text or 
            '"is2fa":true' in response_text):
            logger.info("2FA detected: is2FA flag is true in JavaScript")
            is_2fa_required = True
        
        # Secondary check: SMS field errors (indicates 2FA form is active)
        elif ('codigosms2fa' in response_text and 
              'fielderror' in response_text and 
              'field":"codigosms2fa"' in response_text):
            logger.info("2FA detected: SMS code field error present")
            is_2fa_required = True
        
        # Tertiary check: Explicit 2FA error messages
        elif any(indicator in response_text for indicator in [
            'código incorreto. por favor, solicite o envio de um novo código',
            'código de verificação enviado',
            'introduza o código sms'
        ]):
            logger.info("2FA detected: SMS verification messages found")
            is_2fa_required = True
        
        # Make sure we don't trigger 2FA for successful logins
        if ('loginsuccess: parseboolean(\'true\')' in response_text or 
            'authenticated' in response_text or
            'bem-vindo' in response_text):
            logger.info("Login appears successful - not triggering 2FA")
            is_2fa_required = False
        
        # Check for SMS code expired or failed
        if ('codeexpired2fa: parseboolean(\'true\')' in response_text):
            logger.warning("SMS code has expired - user needs to request a new code")
            is_2fa_required = True  # Still need 2FA but with expired code message
        
        if ('sendremaining: parseint(\'0\')' in response_text or 
            'sendsremaining: parseint(\'0\')' in response_text):
            logger.warning("No SMS sends remaining - user may need to wait or use alternative authentication")
        
        if is_2fa_required:
            logger.info("2FA SMS verification required - portal indicates 2FA is active")
            self.pending_2fa = True  # Set flag to indicate 2FA is pending
            
            # Check for specific error conditions to provide better user feedback
            if 'código incorreto' in response_text:
                return False, "2FA_INCORRECT_CODE"  # Incorrect SMS code
            elif 'codeexpired2fa: parseboolean(\'true\')' in response_text:
                return False, "2FA_CODE_EXPIRED"  # SMS code expired
            elif 'sendsremaining: parseint(\'0\')' in response_text:
                return False, "2FA_NO_SENDS_REMAINING"  # No SMS sends left
            else:
                return False, "2FA_REQUIRED"  # General 2FA needed
        
        # Success indicators for Autenticação.Gov
        success_indicators = [
            'área reservada', 'área pessoal', 'dashboard', 'menu principal',
            'bem-vindo', 'welcome', 'logout', 'terminar sessão', 'sair',
            'minha área', 'dados pessoais', 'serviços disponíveis',
            'autenticado', 'authenticated', 'sessão iniciada'
        ]
        
        # URL-based success indicators
        success_urls = ['dashboard', 'home', 'main', 'index', 'area']
        
        # Failure indicators
        failure_indicators = [
            'credenciais inválidas', 'dados incorretos', 'erro de autenticação',
            'username ou password', 'utilizador ou palavra-passe incorretos',
            'login incorreto', 'acesso negado', 'authentication failed',
            'invalid credentials', 'dados de acesso incorretos'
        ]
        
        # Check for success indicators
        if (any(indicator in response_text for indicator in success_indicators) or 
            any(url_part in response_url for url_part in success_urls)):
            
            self.authenticated = True
            self.pending_2fa = False  # Clear 2FA flag on success
            logger.info("Login successful")
            
            # Update session headers for authenticated requests
            self.session.headers.update({
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            # Reset login attempts on success
            self.login_attempts = 0
            
            return True, "Authentication successful"
        
        # Check for specific failure conditions
        elif any(indicator in response_text for indicator in failure_indicators):
            logger.warning("Login failed: Invalid credentials detected")
            return False, "Invalid username or password"
        
        elif 'captcha' in response_text or 'código de segurança' in response_text:
            logger.warning("Login failed: CAPTCHA required")
            return False, "CAPTCHA verification required. Please login through the website first to clear CAPTCHA."
        
        elif any(blocked in response_text for blocked in ['conta bloqueada', 'account locked', 'temporarily blocked']):
            logger.warning("Login failed: Account locked")
            return False, "Account is temporarily locked. Please try again later or contact support."
        
        elif 'maintenance' in response_text or 'manutenção' in response_text:
            logger.warning("Login failed: System maintenance")
            return False, "System is under maintenance. Please try again later."
        
        # Check response status and URL for additional clues
        elif response.status_code != 200:
            logger.error(f"Login failed: HTTP status {response.status_code}")
            return False, f"Server error (HTTP {response.status_code})"
        
        elif 'error' in response_url or 'erro' in response_url:
            logger.error("Login failed: Redirected to error page")
            return False, "Login failed - server reported an error"
        
        # Generic failure
        else:
            logger.error("Login failed: Unable to determine authentication status")
            return False, "Login failed - authentication status unclear. Check credentials and try again."
    
    def _verify_2fa_sms(self, sms_code: str) -> Tuple[bool, str]:
        """Verify SMS code for 2FA authentication."""
        if not self.pending_2fa:
            return False, "No 2FA verification pending"
        
        if not sms_code or not sms_code.strip():
            return False, "SMS code is required"
        
        try:
            logger.info(f"Attempting 2FA SMS verification with code: {sms_code}")
            
            # Get current CSRF token using the same method as initial login
            csrf_data = self._get_csrf_token_data()
            
            if not csrf_data:
                logger.error("Could not extract CSRF token for 2FA verification")
                return False, "Failed to get authentication token for SMS verification"
            
            csrf_param_name = csrf_data.get('parameterName', '_csrf')
            csrf_token = csrf_data.get('token')
            
            logger.info(f"Using CSRF token for 2FA: {csrf_param_name}")
            
            # Prepare form data for SMS verification (based on your payload example)
            form_data = {
                csrf_param_name: csrf_token,
                'path': '/geral/dashboard',
                'authVersion': '2',
                'partID': 'PFAP',
                'selectedAuthMethod': 'N',
                'nif': self._current_username,  # Use the NIF from initial login
                'codigoSms2Fa': sms_code.strip()  # This is the correct field name
            }
            
            logger.info(f"Submitting 2FA verification with {len(form_data)} fields")
            
            # Set headers for 2FA submission
            self._set_login_headers()
            
            # Submit SMS verification to the same login endpoint
            response = self.session.post(
                self.login_url,
                data=form_data,
                timeout=15,
                allow_redirects=True
            )
            response.raise_for_status()
            
            logger.info(f"2FA verification response: Status {response.status_code}, URL: {response.url}")
            
            # Analyze the response to determine success or failure
            result = self._analyze_login_response(response)
            
            if result[0]:  # Success
                self.pending_2fa = False
                logger.info("2FA SMS verification successful")
            else:
                logger.warning(f"2FA SMS verification failed: {result[1]}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during 2FA verification: {str(e)}")
            return False, f"Network error during SMS verification: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during 2FA verification: {str(e)}")
            return False, f"SMS verification failed: {str(e)}"
    
    def _analyze_2fa_response(self, response: requests.Response) -> Tuple[bool, str]:
        """Analyze 2FA verification response."""
        response_text = response.text.lower()
        response_url = response.url.lower()
        
        logger.info(f"2FA response analysis: Status {response.status_code}, URL: {response.url}")
        
        # Success indicators
        success_indicators = [
            'área reservada', 'área pessoal', 'dashboard', 'menu principal',
            'bem-vindo', 'welcome', 'logout', 'terminar sessão', 'sair',
            'minha área', 'dados pessoais', 'serviços disponíveis',
            'autenticado', 'authenticated', 'sessão iniciada',
            'verification successful', 'verificação bem-sucedida'
        ]
        
        # Failure indicators specific to 2FA
        failure_indicators = [
            'código inválido', 'invalid code', 'código incorreto',
            'wrong code', 'verification failed', 'código expirado',
            'expired code', 'tempo esgotado', 'timeout'
        ]
        
        # Check for success
        if any(indicator in response_text for indicator in success_indicators):
            return True, "2FA verification successful"
        
        # Check for specific failures
        elif any(indicator in response_text for indicator in failure_indicators):
            return False, "Invalid or expired SMS code"
        
        # Check response status
        elif response.status_code != 200:
            return False, f"Server error during 2FA verification (HTTP {response.status_code})"
        
        else:
            return False, "2FA verification failed - please check the SMS code and try again"
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self.authenticated
    
    def logout(self) -> Tuple[bool, str]:
        """Logout from the current session."""
        if not self.authenticated:
            return True, "Already logged out"
        
        try:
            self.authenticated = False
            self.session.cookies.clear()
            self.login_attempts = 0  # Reset login attempts
            self._clear_cache()  # Clear cached contract data
            logger.info("Logged out successfully")
            return True, "Logged out successfully"
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return False, f"Logout failed: {str(e)}"
    
    def get_contracts_list(self) -> Tuple[bool, Any]:
        """
        Get the list of available contracts from Portal das Finanças.
        This method would be implemented to fetch rental contracts.
        """
        if not self.authenticated:
            return False, "Not authenticated"
        
        if self.testing_mode:
            logger.info("Getting mock contracts list")
            # Return mock contracts for testing
            mock_contracts = [
                {"contractId": "123456", "property": "Narnia, 123", "tenant": "Test Tenant"},
                {"contractId": "789012", "property": "Avenida Central, 456", "tenant": "Maria Santos"},
                {"contractId": "345678", "property": "Praça da República, 789", "tenant": "António Costa"}
            ]
            return True, mock_contracts
        
        logger.info("Getting contracts list from Portal das Finanças")
        
        # Use the enhanced method that handles 401 authentication and has fallback mechanisms
        success, contracts_data, message = self.get_contracts_with_tenant_data()
        
        if not success:
            logger.error(f"Failed to retrieve contracts: {message}")
            return False, message
        
        # Convert to the expected format for backward compatibility
        contracts_list = []
        for contract in contracts_data:
            contract_info = {
                "contractId": contract.get('numero', ''),
                "property": f"{contract.get('morada', 'N/A')} - {contract.get('imovelAlternateId', 'N/A')}",
                "tenant": contract.get('nomeLocatario', 'N/A'),
                "rent_amount": contract.get('valorRenda', 'N/A'),
                "status": contract.get('estado', 'N/A')
            }
            contracts_list.append(contract_info)
        
        logger.info(f"Successfully retrieved {len(contracts_list)} contracts from portal")
        return True, contracts_list
    
    def submit_receipt(self, receipt_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Submit a receipt to Portal das Finanças.
        This method would be implemented to submit receipt data.
        """
        if not self.authenticated:
            return False, "Not authenticated"
        
        if self.testing_mode:
            logger.info(f"Mock submitting receipt: {receipt_data.get('contractId', 'N/A')}")
            return True, "Mock receipt submitted successfully"
        
        logger.info(f"Submitting receipt (placeholder implementation): {receipt_data}")
        # This is a placeholder - actual implementation would submit receipt data
        return True, "Receipt submitted successfully"
    
    def get_receipt_form(self, contract_id: str) -> Tuple[bool, Dict]:
        """
        Get receipt form data for a specific contract.
        
        Args:
            contract_id: Contract ID to get form data for
            
        Returns:
            Tuple of (success, form_data)
        """
        if not self.authenticated:
            logger.error("Not authenticated")
            return False, None
        
        if self.testing_mode:
            logger.info(f"Mock getting receipt form for contract: {contract_id}")
            return True, {
                'contractId': contract_id,
                'tenantName': 'Mock Tenant',
                'value': 100.00
            }
        
        try:
            # Get the receipt creation form for the specific contract
            form_url = f"{self.receipts_base_url}/arrendamento/criarRecibo/{contract_id}"
            logger.info(f"Fetching receipt form from: {form_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': f'{self.receipts_base_url}/arrendamento/consultarElementosContratos/locador',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.session.get(form_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to get receipt form. Status: {response.status_code}")
                return False, None
            
            # Parse the HTML to extract form data
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract contract information from the page
            form_data = {
                'contractId': contract_id,
                'url': form_url,
                'html_content': response.text[:1000]  # First 1000 chars for debugging
            }
            
            # Look for Angular scope data that contains contract details
            script_tags = soup.find_all('script')
            contract_details = {}
            
            for script in script_tags:
                if script.string and 'recibo' in script.string:
                    # Extract contract data from JavaScript
                    script_content = script.string
                    if 'numContrato' in script_content:
                        # Found the contract data - try to extract key information
                        logger.info("Found contract data in JavaScript")
                        
                        # Try to extract contract number
                        contract_match = re.search(r'"numContrato":\s*(\d+)', script_content)
                        if contract_match:
                            contract_details['numContrato'] = int(contract_match.group(1))
                        
                        # Try to extract NIF emitente
                        nif_match = re.search(r'"nifEmitente":\s*(\d+)', script_content)
                        if nif_match:
                            contract_details['nifEmitente'] = int(nif_match.group(1))
                        
                        # Try to extract landlord name
                        landlord_match = re.search(r'"nomeEmitente":\s*"([^"]+)"', script_content)
                        if landlord_match:
                            contract_details['nomeEmitente'] = landlord_match.group(1).strip()
                        
                        # Try to extract contract version
                        version_match = re.search(r'"versaoContrato":\s*(\d+)', script_content)
                        if version_match:
                            contract_details['versaoContrato'] = int(version_match.group(1))
                        
                        # Try to extract tenant data including NIF for ALL tenants
                        # Look for locatarios array in the JavaScript
                        locatarios_pattern = r'"locatarios":\s*\[(.*?)\]'
                        locatarios_match = re.search(locatarios_pattern, script_content, re.DOTALL)
                        if locatarios_match:
                            locatarios_data = locatarios_match.group(1)
                            logger.info("Found locatarios data in JavaScript")
                            
                            # Parse all tenants from the array
                            tenants_list = []
                            
                            # Try to parse the full JSON structure first
                            try:
                                import json
                                # Extract the full locatarios array as valid JSON
                                full_array_pattern = r'"locatarios":\s*(\[.*?\])'
                                full_array_match = re.search(full_array_pattern, script_content, re.DOTALL)
                                if full_array_match:
                                    locatarios_json = full_array_match.group(1)
                                    # Clean up the JSON (remove any trailing commas, etc.)
                                    locatarios_json = re.sub(r',\s*}', '}', locatarios_json)
                                    locatarios_json = re.sub(r',\s*]', ']', locatarios_json)
                                    
                                    tenants_array = json.loads(locatarios_json)
                                    
                                    for i, tenant in enumerate(tenants_array):
                                        tenant_info = {
                                            'nif': tenant.get('nif'),
                                            'nome': tenant.get('nome', '').strip(),
                                            'pais': tenant.get('pais', {}),
                                            'retencao': tenant.get('retencao', {})
                                        }
                                        tenants_list.append(tenant_info)
                                        logger.info(f"Extracted tenant {i+1}: NIF={tenant_info['nif']}, Name={tenant_info['nome']}")
                                    
                                    contract_details['locatarios'] = tenants_list
                                    contract_details['tenant_count'] = len(tenants_list)
                                    logger.info(f"Extracted {len(tenants_list)} tenants from JavaScript")
                                    
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.warning(f"Failed to parse locatarios JSON, falling back to regex: {e}")
                                
                                # Fallback to regex parsing for individual tenant objects
                                # Find all tenant objects in the array
                                tenant_objects = re.findall(r'\{[^}]*"nif"[^}]*\}', locatarios_data, re.DOTALL)
                                
                                for i, tenant_obj in enumerate(tenant_objects):
                                    # Extract NIF
                                    nif_match = re.search(r'"nif":\s*(\d+)', tenant_obj)
                                    # Extract name
                                    name_match = re.search(r'"nome":\s*"([^"]+)"', tenant_obj)
                                    
                                    if nif_match or name_match:
                                        tenant_info = {
                                            'nif': int(nif_match.group(1)) if nif_match else None,
                                            'nome': name_match.group(1).strip() if name_match else '',
                                            'pais': {"codigo": "2724", "label": "PORTUGAL"},
                                            'retencao': {
                                                "taxa": 0,
                                                "codigo": "RIRS03", 
                                                "label": "Dispensa de retenção - artigo 101.º-B, n.º 1, do CIRS"
                                            }
                                        }
                                        tenants_list.append(tenant_info)
                                        logger.info(f"Extracted tenant {i+1} (regex): NIF={tenant_info['nif']}, Name={tenant_info['nome']}")
                                
                                contract_details['locatarios'] = tenants_list
                                contract_details['tenant_count'] = len(tenants_list)
                                logger.info(f"Extracted {len(tenants_list)} tenants using regex fallback")
                            
                            # For backward compatibility, also set the first tenant's data individually
                            if tenants_list:
                                contract_details['tenant_nif'] = tenants_list[0]['nif']
                                contract_details['tenant_name'] = tenants_list[0]['nome']
                                logger.info(f"Primary tenant: NIF={contract_details['tenant_nif']}, Name={contract_details['tenant_name']}")
                            else:
                                logger.warning("No tenant data could be extracted from locatarios array")
                        
                        # Try to extract landlord data including NIF for ALL landlords
                        # Look for locadores array in the JavaScript
                        locadores_pattern = r'"locadores":\s*\[(.*?)\]'
                        locadores_match = re.search(locadores_pattern, script_content, re.DOTALL)
                        if locadores_match:
                            logger.info("Found locadores data in JavaScript")
                            
                            # Parse all landlords from the array
                            landlords_list = []
                            
                            try:
                                # Try to parse the full JSON structure first
                                full_array_pattern = r'"locadores":\s*(\[.*?\])'
                                full_array_match = re.search(full_array_pattern, script_content, re.DOTALL)
                                if full_array_match:
                                    locadores_json = full_array_match.group(1)
                                    # Clean up the JSON
                                    locadores_json = re.sub(r',\s*}', '}', locadores_json)
                                    locadores_json = re.sub(r',\s*]', ']', locadores_json)
                                    
                                    landlords_array = json.loads(locadores_json)
                                    
                                    for i, landlord in enumerate(landlords_array):
                                        landlord_info = {
                                            'nif': landlord.get('nif'),
                                            'nome': landlord.get('nome', '').strip(),
                                            'quotaParte': landlord.get('quotaParte', '1/1'),
                                            'sujeitoPassivo': landlord.get('sujeitoPassivo', 'V')
                                        }
                                        landlords_list.append(landlord_info)
                                        logger.info(f"Extracted landlord {i+1}: NIF={landlord_info['nif']}, Name={landlord_info['nome']}")
                                    
                                    contract_details['locadores'] = landlords_list
                                    contract_details['landlord_count'] = len(landlords_list)
                                    logger.info(f"Extracted {len(landlords_list)} landlords from JavaScript")
                                    
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.warning(f"Failed to parse locadores JSON, falling back to regex: {e}")
                                
                                # Fallback to regex parsing for individual landlord objects
                                landlord_objects = re.findall(r'\{[^}]*"nif"[^}]*\}', locadores_match.group(1), re.DOTALL)
                                
                                for i, landlord_obj in enumerate(landlord_objects):
                                    # Extract NIF
                                    nif_match = re.search(r'"nif":\s*(\d+)', landlord_obj)
                                    # Extract name
                                    name_match = re.search(r'"nome":\s*"([^"]+)"', landlord_obj)
                                    # Extract quota parte
                                    quota_match = re.search(r'"quotaParte":\s*"([^"]+)"', landlord_obj)
                                    
                                    if nif_match or name_match:
                                        landlord_info = {
                                            'nif': int(nif_match.group(1)) if nif_match else None,
                                            'nome': name_match.group(1).strip() if name_match else '',
                                            'quotaParte': quota_match.group(1) if quota_match else '1/1',
                                            'sujeitoPassivo': 'V'
                                        }
                                        landlords_list.append(landlord_info)
                                        logger.info(f"Extracted landlord {i+1} (regex): NIF={landlord_info['nif']}, Name={landlord_info['nome']}")
                                
                                contract_details['locadores'] = landlords_list
                                contract_details['landlord_count'] = len(landlords_list)
                                logger.info(f"Extracted {len(landlords_list)} landlords using regex fallback")
                            
                            # For backward compatibility, also set the first landlord's data individually
                            if landlords_list:
                                contract_details['landlord_nif'] = landlords_list[0]['nif']
                                contract_details['landlord_name'] = landlords_list[0]['nome']
                                logger.info(f"Primary landlord: NIF={contract_details['landlord_nif']}, Name={contract_details['landlord_name']}")
                            else:
                                logger.warning("No landlord data could be extracted from locadores array")
                        
                        # Check for inheritance case (hasNifHerancaIndivisa)
                        inheritance_match = re.search(r'"hasNifHerancaIndivisa":\s*(true|false)', script_content)
                        if inheritance_match:
                            has_inheritance = inheritance_match.group(1) == 'true'
                            contract_details['hasNifHerancaIndivisa'] = has_inheritance
                            logger.info(f"Inheritance flag detected: {has_inheritance}")
                            
                            if has_inheritance:
                                # Extract inheritance-specific data
                                
                                # Extract locadoresHerancaIndivisa
                                heranca_pattern = r'"locadoresHerancaIndivisa":\s*(\[.*?\])'
                                heranca_match = re.search(heranca_pattern, script_content, re.DOTALL)
                                if heranca_match:
                                    try:
                                        heranca_json = heranca_match.group(1)
                                        heranca_json = re.sub(r',\s*}', '}', heranca_json)
                                        heranca_json = re.sub(r',\s*]', ']', heranca_json)
                                        
                                        heranca_landlords = json.loads(heranca_json)
                                        contract_details['locadoresHerancaIndivisa'] = heranca_landlords
                                        logger.info(f"Extracted {len(heranca_landlords)} inheritance landlords")
                                        
                                    except (json.JSONDecodeError, ValueError) as e:
                                        logger.warning(f"Failed to parse locadoresHerancaIndivisa: {e}")
                                        contract_details['locadoresHerancaIndivisa'] = []
                                
                                # Extract herdeiros (heirs)
                                herdeiros_pattern = r'"herdeiros":\s*(\[.*?\])'
                                herdeiros_match = re.search(herdeiros_pattern, script_content, re.DOTALL)
                                if herdeiros_match:
                                    try:
                                        herdeiros_json = herdeiros_match.group(1)
                                        herdeiros_json = re.sub(r',\s*}', '}', herdeiros_json)
                                        herdeiros_json = re.sub(r',\s*]', ']', herdeiros_json)
                                        
                                        heirs = json.loads(herdeiros_json)
                                        contract_details['herdeiros'] = heirs
                                        logger.info(f"Extracted {len(heirs)} heirs information")
                                        
                                        # Log heir details for debugging
                                        for i, heir in enumerate(heirs):
                                            heir_nif = heir.get('nifHerdeiro')
                                            quota = heir.get('quotaParte')
                                            logger.info(f"Heir {i+1}: NIF={heir_nif}, Quota={quota}")
                                        
                                    except (json.JSONDecodeError, ValueError) as e:
                                        logger.warning(f"Failed to parse herdeiros: {e}")
                                        contract_details['herdeiros'] = []
                                
                                logger.info("Successfully extracted inheritance data from receipt form")
                            else:
                                # Set default empty values for non-inheritance cases
                                contract_details['locadoresHerancaIndivisa'] = []
                                contract_details['herdeiros'] = []
                        else:
                            # Default values if inheritance flag not found
                            contract_details['hasNifHerancaIndivisa'] = False
                            contract_details['locadoresHerancaIndivisa'] = []
                            contract_details['herdeiros'] = []
                        
                        # Try to extract imoveis (property) data
                        imoveis_pattern = r'"imoveis":\s*\[(.*?)\]'
                        imoveis_match = re.search(imoveis_pattern, script_content, re.DOTALL)
                        if imoveis_match:
                            imoveis_data = imoveis_match.group(1)
                            # Extract property address
                            address_match = re.search(r'"morada":\s*"([^"]+)"', imoveis_data)
                            if address_match:
                                contract_details['property_address'] = address_match.group(1).strip()
                        
                        form_data['contract_details'] = contract_details
                        form_data['has_contract_data'] = True
                        break
            
            # Update form_data with extracted details
            form_data.update(contract_details)
            
            logger.info(f"Successfully retrieved receipt form for contract {contract_id}")
            return True, form_data
            
        except Exception as e:
            logger.error(f"Error getting receipt form for contract {contract_id}: {str(e)}")
            return False, None
    
    def issue_receipt(self, submission_data: Dict) -> Tuple[bool, Dict]:
        """
        Issue a receipt with the provided data.
        
        Args:
            submission_data: Receipt data to submit
            
        Returns:
            Tuple of (success, response_data)
        """
        if not self.authenticated:
            logger.error("Not authenticated")
            return False, None
        
        if self.testing_mode:
            logger.info(f"Mock issuing receipt for contract: {submission_data.get('contractId', 'N/A')}")
            return True, {
                'receiptNumber': 'MOCK-001',
                'success': True
            }
        
        try:
            # Prepare the receipt submission
            api_url = f"{self.receipts_base_url}/arrendamento/api/emitirRecibo"
            logger.info(f"Submitting receipt to: {api_url}")
            
            # Headers for JSON API call
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/json;charset=UTF-8',
                'Referer': f'{self.receipts_base_url}/arrendamento/criarRecibo/{submission_data.get("numContrato", "")}',
                'Origin': self.receipts_base_url,
                'Connection': 'keep-alive',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # Prepare the payload based on the expected format
            payload = {
                "numContrato": submission_data.get('numContrato'),
                "versaoContrato": submission_data.get('versaoContrato', 1),
                "nifEmitente": submission_data.get('nifEmitente'),
                "nomeEmitente": submission_data.get('nomeEmitente'),
                "isNifEmitenteColetivo": submission_data.get('isNifEmitenteColetivo', False),
                "valor": submission_data.get('valor'),
                "tipoContrato": submission_data.get('tipoContrato'),
                "locadores": submission_data.get('locadores', []),
                "locatarios": submission_data.get('locatarios', []),
                "imoveis": submission_data.get('imoveis', []),
                "hasNifHerancaIndivisa": submission_data.get('hasNifHerancaIndivisa', False),
                "locadoresHerancaIndivisa": submission_data.get('locadoresHerancaIndivisa', []),
                "herdeiros": submission_data.get('herdeiros', []),
                "dataInicio": submission_data.get('dataInicio'),
                "dataFim": submission_data.get('dataFim'),
                "dataRecebimento": submission_data.get('dataRecebimento'),
                "tipoImportancia": submission_data.get('tipoImportancia', {
                    "codigo": "RENDAC",
                    "label": "Renda"
                })
            }
            
            logger.info(f"Submitting receipt payload for contract {payload.get('numContrato')}")
            
            # Submit the receipt
            response = self.session.post(
                api_url, 
                json=payload, 
                headers=headers, 
                timeout=60
            )
            
            logger.info(f"Receipt submission response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"Receipt submission response: {response_data}")
                    
                    # Check if the response indicates success or failure
                    platform_success = response_data.get('success', False)
                    
                    if platform_success:
                        logger.info(f"Receipt issued successfully for contract {payload.get('numContrato')}")
                        return True, {
                            'receiptNumber': response_data.get('numeroRecibo', 'ISSUED'),
                            'success': True,
                            'response': response_data
                        }
                    else:
                        # Platform returned an error within 200 response
                        error_msg = response_data.get('errorMessage', 'Unknown error from platform')
                        field_errors = response_data.get('fieldErrors', {})
                        
                        if field_errors:
                            error_details = []
                            for field, error in field_errors.items():
                                error_details.append(f"{field}: {error}")
                            error_msg += f" Field errors: {'; '.join(error_details)}"
                        
                        logger.error(f"Receipt submission failed: {error_msg}")
                        return False, {
                            'success': False,
                            'error': error_msg,
                            'platform_response': response_data
                        }
                        
                except ValueError:
                    # Response might not be JSON
                    logger.info("Receipt submitted successfully (non-JSON response)")
                    return True, {
                        'receiptNumber': 'ISSUED',
                        'success': True,
                        'response_text': response.text[:500]
                    }
            else:
                error_msg = f"Receipt submission failed with status {response.status_code}"
                logger.error(f"{error_msg}. Response: {response.text[:500]}")
                
                return False, {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code,
                    'response_text': response.text[:500]
                }
                
        except Exception as e:
            error_msg = f"Exception during receipt submission: {str(e)}"
            logger.error(error_msg)
            return False, {
                'success': False,
                'error': error_msg
            }
    
    def get_contracts_with_tenant_data(self) -> Tuple[bool, List[Dict], str]:
        """
        Get complete contract data including tenant names from Portal das Finanças.
        Returns contract data with tenant information.
        """
        if not self.authenticated:
            return False, [], "Not authenticated"
        
        # Check cache first (only for production mode to avoid caching mock data)
        if not self.testing_mode and self._is_cache_valid():
            logger.info(f"Using cached contract data ({len(self._cached_contracts)} contracts)")
            return True, self._cached_contracts.copy(), f"Retrieved {len(self._cached_contracts)} contracts from cache"
        
        if self.testing_mode:
            logger.info("Mock fetching contract data with tenant information")
            # Return mock data with tenant names for testing
            mock_contracts = [
                {
                    "numero": "123456",
                    "referencia": "CT123456", 
                    "nomeLocador": "TEST LANDLORD NAME",
                    "nomeLocatario": "Test Tenant Name",
                    "imovelAlternateId": "Narnia, 123, 1º Dto",
                    "valorRenda": 100.00,
                    "estado": {"codigo": "ACTIVO", "label": "Ativo"}
                },
                {
                    "numero": "789012",
                    "referencia": "CT789012",
                    "nomeLocador": "TEST LANDLORD NAME", 
                    "nomeLocatario": "Maria Santos Costa",
                    "imovelAlternateId": "Avenida Central, 456, 2º Esq",
                    "valorRenda": 100.00,
                    "estado": {"codigo": "ACTIVO", "label": "Ativo"}
                }
            ]
            return True, mock_contracts, f"Retrieved {len(mock_contracts)} contracts"
        
        try:
            import json
            
            # Log current session state for debugging
            logger.info(f"Current session cookies: {list(self.session.cookies.keys())}")
            logger.info(f"Authentication status: {self.authenticated}")
            
            # STEP 1: First, navigate through proper authentication redirect
            logger.info("Step 1: Navigating through authentication redirect to establish session...")
            
            # Use the SICI redirect URL that properly transfers authentication
            redirect_url = "https://www.acesso.gov.pt/v2/loginForm?partID=SICI&path=/arrendamento/consultarElementosContratos/locador"
            
            # First navigate through the auth redirect
            logger.info("Navigating through authentication redirect...")
            response = self.session.get(redirect_url, timeout=15, allow_redirects=True)
            
            logger.info(f"Auth redirect response: Status {response.status_code}, URL: {response.url}")
            logger.info(f"Auth redirect cookies: {list(self.session.cookies.keys())}")
            
            # Check if we're still on the auth domain (session transfer failed)
            if 'acesso.gov.pt' in response.url:
                logger.error("Session transfer failed - still on auth domain")
                # Try to complete the authentication flow
                if 'loginForm' in response.url:
                    logger.info("Attempting to complete authentication flow...")
                    
                    # Extract form data and submit if needed
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for redirect form or continue button
                    forms = soup.find_all('form')
                    for form in forms:
                        if form.get('action') and 'imoveis.portaldasfinancas.gov.pt' in form.get('action', ''):
                            logger.info("Found portal redirect form, submitting...")
                            
                            # Extract form data
                            form_data = {}
                            for input_tag in form.find_all('input'):
                                name = input_tag.get('name')
                                value = input_tag.get('value', '')
                                if name:
                                    form_data[name] = value
                            
                            # Submit the form
                            form_action = form.get('action')
                            if not form_action.startswith('http'):
                                form_action = 'https://www.acesso.gov.pt' + form_action
                            
                            response = self.session.post(form_action, data=form_data, timeout=15, allow_redirects=True)
                            logger.info(f"Form submission response: Status {response.status_code}, URL: {response.url}")
                            break
            
            # Now navigate to the actual portal page
            portal_page_url = "https://imoveis.portaldasfinancas.gov.pt/arrendamento/consultarElementosContratos/locador"
            
            # Set headers for navigating to portal (if we're not already there)
            if 'imoveis.portaldasfinancas.gov.pt' not in response.url:
                portal_headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Referer': redirect_url,
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
                }
                
                # Navigate to portal page
                response = self.session.get(portal_page_url, headers=portal_headers, timeout=15)
            
            logger.info(f"Portal page response: Status {response.status_code}, URL: {response.url}")
            logger.info(f"Portal page cookies: {list(self.session.cookies.keys())}")
            
            # Check if we got redirected to login (session expired)
            if 'login' in response.url.lower() or 'acesso.gov.pt' in response.url:
                logger.error("Session expired - redirected to login page when accessing portal")
                self.authenticated = False
                self._clear_cache()  # Clear cached data on session expiry
                return False, [], "Session expired - please re-authenticate"
            
            if response.status_code != 200:
                logger.error(f"Failed to access portal page: HTTP {response.status_code}")
                return False, [], f"Failed to access portal page: HTTP {response.status_code}"
            
            # STEP 2: Now try the AJAX endpoint with proper headers
            logger.info("Step 2: Making AJAX request to contracts endpoint...")
            ajax_url = "https://imoveis.portaldasfinancas.gov.pt/arrendamento/api/obterElementosContratosEmissaoRecibos/locador"
            
            # Set AJAX headers (important for API call)
            ajax_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': portal_page_url,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            }
            
            logger.info(f"Making AJAX request to: {ajax_url}")
            
            response = self.session.get(ajax_url, headers=ajax_headers, timeout=15)
            
            logger.info(f"AJAX Response status: {response.status_code}")
            logger.info(f"AJAX Response URL: {response.url}")
            logger.info(f"AJAX Response content length: {len(response.text)} chars")
            
            # Check if we got redirected to login page
            if 'login' in response.url.lower() or 'acesso.gov.pt' in response.url:
                logger.error("AJAX request redirected to login page - session expired!")
                self.authenticated = False
                self._clear_cache()  # Clear cached data on session expiry
                return False, [], "Session expired during AJAX request - please re-authenticate"
            
            if response.status_code == 200:
                try:
                    # Parse JSON response
                    contracts_data = response.json()
                    
                    logger.info(f"JSON parsing successful. Data type: {type(contracts_data)}")
                    
                    if isinstance(contracts_data, list):
                        logger.info(f"Successfully retrieved {len(contracts_data)} contracts with full data")
                        
                        # Log sample of what we got (first contract if available)
                        if contracts_data:
                            sample = contracts_data[0]
                            logger.info(f"Sample contract data keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")
                            logger.info(f"Sample contract: {sample}")
                        else:
                            logger.info("Contracts array is empty - user has no contracts")
                        
                        # Cache the successful result (only in production mode)
                        if not self.testing_mode:
                            import time
                            self._cached_contracts = contracts_data.copy()
                            self._cache_timestamp = time.time()
                            logger.info(f"Cached {len(contracts_data)} contracts for future requests")
                        
                        return True, contracts_data, f"Retrieved {len(contracts_data)} contracts with tenant data"
                    else:
                        logger.warning(f"Unexpected JSON format: {type(contracts_data)}")
                        logger.info(f"Response data: {contracts_data}")
                        return False, [], "Unexpected data format from server"
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Response content (first 500 chars): {response.text[:500]}...")
                    
                    # Save response for debugging
                    with open('debug_ajax_response.html', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.info("Non-JSON response saved to debug_ajax_response.html")
                    
                    return False, [], "Invalid JSON response from server"
                    
            elif response.status_code == 401:
                logger.error("401 Unauthorized - attempting to re-establish portal session...")
                
                # STEP 3: Try alternative approach - parse contracts from HTML page
                logger.info("Step 3: Falling back to HTML parsing approach...")
                return self._fallback_html_parsing(portal_page_url, portal_headers)
                
            elif response.status_code == 403:
                logger.error("Access denied - session may have expired")
                self.authenticated = False
                self._clear_cache()  # Clear cached data on session expiry
                return False, [], "Access denied - please re-authenticate"
                
            else:
                logger.error(f"AJAX request failed: HTTP {response.status_code}")
                logger.error(f"Response content: {response.text[:200]}...")
                
                # Try fallback HTML parsing
                logger.info("Trying fallback HTML parsing approach...")
                return self._fallback_html_parsing(portal_page_url, portal_headers)
                
        except Exception as e:
            logger.error(f"Error fetching contract data: {str(e)}")
            return False, [], f"Error: {str(e)}"
    
    def _fallback_html_parsing(self, portal_page_url: str, portal_headers: dict) -> Tuple[bool, List[Dict], str]:
        """
        Fallback method to extract contract data from HTML when AJAX fails.
        """
        try:
            logger.info("Attempting fallback HTML parsing...")
            
            # Re-fetch the portal page
            response = self.session.get(portal_page_url, headers=portal_headers, timeout=15)
            
            if response.status_code != 200:
                return False, [], f"Fallback failed: HTTP {response.status_code}"
            
            # Save HTML for debugging
            with open('debug_portal_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("Portal page HTML saved to debug_portal_page.html")
            
            # Look for any contract references in the HTML
            import re
            
            # Try to find AJAX configuration in the HTML
            ajax_pattern = r'sAjaxSource["\s]*:["\s]*[\'"]([^\'"]+)'
            ajax_match = re.search(ajax_pattern, response.text)
            
            if ajax_match:
                ajax_url = ajax_match.group(1)
                logger.info(f"Found AJAX URL in HTML: {ajax_url}")
                
                # Make the URL absolute if it's relative
                if ajax_url.startswith('/'):
                    ajax_url = 'https://imoveis.portaldasfinancas.gov.pt' + ajax_url
                
                # Try the AJAX URL with different headers
                simple_headers = {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': portal_page_url
                }
                
                ajax_response = self.session.get(ajax_url, headers=simple_headers, timeout=15)
                logger.info(f"Fallback AJAX response: {ajax_response.status_code}")
                
                if ajax_response.status_code == 200:
                    try:
                        data = ajax_response.json()
                        if isinstance(data, list):
                            logger.info(f"Fallback AJAX success: {len(data)} contracts")
                            return True, data, f"Retrieved {len(data)} contracts via fallback AJAX"
                    except:
                        pass
            
            # If AJAX still fails, look for embedded data in the HTML
            logger.info("Trying to extract embedded contract data from HTML...")
            
            # Look for JavaScript data embedded in the page
            data_patterns = [
                r'var\s+contractsData\s*=\s*(\[.*?\]);',
                r'contractsData["\s]*:["\s]*(\[.*?\])',
                r'"contracts"["\s]*:["\s]*(\[.*?\])',
            ]
            
            for pattern in data_patterns:
                match = re.search(pattern, response.text, re.DOTALL)
                if match:
                    try:
                        import json
                        data = json.loads(match.group(1))
                        if isinstance(data, list) and data:
                            logger.info(f"Found embedded contract data: {len(data)} contracts")
                            return True, data, f"Retrieved {len(data)} contracts from embedded HTML data"
                    except:
                        continue
            
            # Last resort - check if the page indicates no contracts
            if 'sem dados' in response.text.lower() or 'no data' in response.text.lower():
                logger.info("Portal page indicates no contracts available")
                return True, [], "No contracts found in your account"
            
            logger.warning("No contract data found in HTML page")
            return True, [], "Unable to extract contract data from portal page"
            
        except Exception as e:
            logger.error(f"Fallback HTML parsing failed: {str(e)}")
            return False, [], f"Fallback parsing error: {str(e)}"

    def get_contract_ids(self) -> Tuple[bool, List[str], str]:
        """
        Fetch list of contract IDs from Portal das Finanças.
        Returns: (success, contract_ids_list, message)
        """
        # Use the enhanced method and extract just the IDs
        success, contracts_data, message = self.get_contracts_with_tenant_data()
        
        if not success:
            return False, [], message
        
        # Extract contract IDs from the full data
        contract_ids = []
        for contract in contracts_data:
            if isinstance(contract, dict):
                # Try both 'numero' and 'referencia' fields
                contract_id = contract.get('numero') or contract.get('referencia')
                if contract_id:
                    contract_ids.append(str(contract_id))
        
        logger.info(f"Extracted {len(contract_ids)} contract IDs: {contract_ids}")
        return True, contract_ids, f"Retrieved {len(contract_ids)} contract IDs"
        
        try:
            # Set up headers for Portal das Finanças requests
            portal_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'pt-PT,pt;q=0.9,pt-BR;q=0.8,en;q=0.7,en-US;q=0.6,en-GB;q=0.5',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Referer': 'https://www.acesso.gov.pt/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0'
            }
            self.session.headers.update(portal_headers)
            
            # Fetch contracts list from Portal das Finanças
            contracts_url = "https://imoveis.portaldasfinancas.gov.pt/arrendamento/consultarElementosContratos/locador"
            
            logger.info(f"Fetching contracts from: {contracts_url}")
            response = self.session.get(contracts_url, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"Successfully fetched contracts page (length: {len(response.text)} chars)")
                
                # Parse contract IDs from the HTML response
                contract_ids = self._parse_contract_ids(response.text)
                
                if contract_ids:
                    logger.info(f"Found {len(contract_ids)} contract IDs: {contract_ids}")
                    return True, contract_ids, f"Successfully retrieved {len(contract_ids)} contracts"
                else:
                    logger.warning("No contract IDs found in response")
                    return True, [], "No contracts found in your account"
                    
            elif response.status_code == 403:
                logger.error("Access denied when fetching contracts - session may have expired")
                return False, [], "Access denied - please re-authenticate"
                
            elif response.status_code == 404:
                logger.error("Contracts page not found - URL may be incorrect")
                return False, [], "Contracts page not found"
                
            else:
                logger.error(f"Failed to fetch contracts: HTTP {response.status_code}")
                return False, [], f"Failed to fetch contracts: HTTP {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error fetching contracts: {str(e)}")
            return False, [], f"Error fetching contracts: {str(e)}"
    
    def _parse_contract_ids(self, html_content: str) -> List[str]:
        """
        Parse contract IDs from the HTML response.
        This method looks for contract IDs in various HTML patterns.
        """
        import re
        
        contract_ids = []
        
        try:
            # Pattern 1: Look for contract IDs in data attributes or form inputs
            patterns = [
                r'data-contract-id["\s]*=["\s]*([^">\s]+)',
                r'contractId["\s]*:["\s]*[\'"]([^\'"]+)[\'"]',
                r'contract_id["\s]*=["\s]*[\'"]([^\'"]+)[\'"]',
                r'value["\s]*=["\s]*([0-9]{4,})["\s]',  # Numeric IDs
                r'/criarRecibo/([0-9]+)',  # IDs in URLs
                r'contract["\s]*:["\s]*[\'"]([0-9]+)[\'"]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if match and match.isdigit() and len(match) >= 4:  # Reasonable contract ID length
                        if match not in contract_ids:
                            contract_ids.append(match)
            
            # Pattern 2: Look for table rows with contract information
            table_pattern = r'<tr[^>]*>.*?(?:contrato|contract).*?([0-9]{4,}).*?</tr>'
            table_matches = re.findall(table_pattern, html_content, re.IGNORECASE | re.DOTALL)
            for match in table_matches:
                if match not in contract_ids:
                    contract_ids.append(match)
            
            # Sort and deduplicate
            contract_ids = sorted(list(set(contract_ids)))
            
            logger.info(f"Parsed contract IDs using regex patterns: {contract_ids}")
            
        except Exception as e:
            logger.error(f"Error parsing contract IDs: {str(e)}")
            
        return contract_ids
    
    def validate_csv_contracts(self, csv_contract_ids: List[str]) -> Dict[str, Any]:
        """
        Validate CSV contract IDs against Portal das Finanças contract list.
        Returns validation report with tenant information and inconsistencies.
        """
        logger.info(f"Validating {len(csv_contract_ids)} contract IDs from CSV")
        
        # Fetch current contracts WITH TENANT DATA from portal
        success, portal_contracts_data, message = self.get_contracts_with_tenant_data()
        
        # Filter to only include ACTIVE contracts
        active_portal_contracts = []
        if success and portal_contracts_data:
            for contract in portal_contracts_data:
                # Check if contract is active
                estado = contract.get('estado', {})
                if isinstance(estado, dict):
                    status_code = estado.get('codigo', '').upper()
                    if status_code == 'ACTIVO':
                        active_portal_contracts.append(contract)
                elif isinstance(estado, str):
                    # Handle case where estado might be a string
                    if estado.upper() in ['ACTIVO', 'ATIVO', 'ACTIVE']:
                        active_portal_contracts.append(contract)
        
        logger.info(f"Filtered to {len(active_portal_contracts)} active contracts from {len(portal_contracts_data) if portal_contracts_data else 0} total contracts")
        
        # Extract just the contract IDs for comparison (from active contracts only)
        portal_contract_ids = []
        for contract in active_portal_contracts:
            # Try both 'numero' and 'referencia' fields
            contract_id = contract.get('numero') or contract.get('referencia')
            if contract_id:
                portal_contract_ids.append(str(contract_id))
        
        validation_report = {
            'success': success,
            'message': message,
            'portal_contracts_count': len(active_portal_contracts),  # Count of active contracts only
            'csv_contracts_count': len(csv_contract_ids),
            'portal_contracts': portal_contract_ids,
            'portal_contracts_data': active_portal_contracts,  # Only active contracts data
            'csv_contracts': csv_contract_ids,
            'valid_contracts': [],
            'valid_contracts_data': [],  # Full data for valid contracts
            'invalid_contracts': [],
            'missing_from_csv': [],
            'missing_from_csv_data': [],  # Full data for missing contracts
            'missing_from_portal': [],
            'validation_errors': []
        }
        
        if not success:
            validation_report['validation_errors'].append(f"Failed to fetch portal contracts: {message}")
            return validation_report
        
        # Check for empty lists
        if not active_portal_contracts:
            validation_report['validation_errors'].append("No active contracts found in Portal das Finanças")
            logger.warning("No active contracts found in Portal das Finanças - this could mean:")
            logger.warning("1. Authentication session expired")
            logger.warning("2. User has no active contracts registered")
            logger.warning("3. All contracts are inactive/terminated")
            logger.warning("4. Portal API is not returning data")
            return validation_report
        
        if not csv_contract_ids:
            validation_report['validation_errors'].append("No contract IDs provided from CSV")
            return validation_report
        
        # Create lookup dictionary for active portal contracts
        portal_lookup = {}
        for contract in active_portal_contracts:
            contract_id = contract.get('numero') or contract.get('referencia')
            if contract_id:
                portal_lookup[str(contract_id)] = contract
        
        # Validate each CSV contract ID
        for csv_id in csv_contract_ids:
            csv_id_str = str(csv_id).strip()
            if csv_id_str in portal_lookup:
                validation_report['valid_contracts'].append(csv_id_str)
                validation_report['valid_contracts_data'].append(portal_lookup[csv_id_str])
            else:
                validation_report['invalid_contracts'].append(csv_id_str)
        
        # Find contracts in portal but not in CSV
        for portal_id in portal_contract_ids:
            if portal_id not in csv_contract_ids:
                validation_report['missing_from_csv'].append(portal_id)
                validation_report['missing_from_csv_data'].append(portal_lookup[portal_id])
        
        # Find contracts in CSV but not in portal
        for csv_id in csv_contract_ids:
            csv_id_str = str(csv_id).strip()
            if csv_id_str not in portal_contract_ids:
                validation_report['missing_from_portal'].append(csv_id_str)
        
        logger.info(f"Validation completed: {len(validation_report['valid_contracts'])} valid, "
                   f"{len(validation_report['invalid_contracts'])} invalid (compared against active contracts only)")
        
        return validation_report

    # Mock methods for testing mode
    def _mock_login(self, username: str, password: str, sms_code: str = None) -> Tuple[bool, str]:
        """Mock login for testing purposes with optional 2FA simulation."""
        
        # If SMS code is provided, simulate 2FA verification
        if sms_code:
            if not self.pending_2fa:
                return False, "No 2FA verification pending"
            
            # Accept specific test SMS codes
            if sms_code in ["123456", "000000", "111111"]:
                self.authenticated = True
                self.pending_2fa = False
                self.login_attempts = 0
                logger.info(f"Mock 2FA verification successful with code: {sms_code}")
                return True, "Mock 2FA verification successful"
            else:
                logger.warning(f"Mock 2FA verification failed with code: {sms_code}")
                return False, "Invalid SMS code. Use '123456', '000000', or '111111' for testing."
        
        # Initial login attempt
        self.login_attempts += 1
        logger.info(f"Mock login attempt {self.login_attempts} for user: {username}")
        
        # Simulate 2FA requirement for specific usernames
        if username in ["2fa", "sms"] and password in ["test", "demo"]:
            self.pending_2fa = True
            logger.info(f"Mock login triggering 2FA for user: {username}")
            return False, "2FA_REQUIRED"
        
        # Accept specific test credentials
        if username in ["test", "demo"] and password in ["test", "demo"]:
            self.authenticated = True
            self.pending_2fa = False
            self.login_attempts = 0  # Reset on success
            logger.info(f"Mock login successful for user: {username}")
            return True, "Mock login successful"
        elif username == "admin" and password == "admin":
            self.authenticated = True
            self.pending_2fa = False
            self.login_attempts = 0
            logger.info("Mock login successful for admin user")
            return True, "Mock admin login successful"
        else:
            logger.warning(f"Mock login failed for user: {username}")
            return False, "Invalid mock credentials. Use 'test/test', 'demo/demo', or 'admin/admin' for testing."
