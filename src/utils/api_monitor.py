"""
Portal das Finanças API Evolution Monitor

Monitors the Portal das Finanças website for changes that could affect
the receipt processing automation. Detects changes in:
- Form structure and field names
- Authentication flow and 2FA requirements
- Receipt generation endpoints and parameters
- Page layouts and CSS selectors
- JavaScript functionality and AJAX calls

This system helps maintain compatibility and adapts automatically
to minor changes while alerting for major structural changes.
"""

import requests
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import re
from urllib.parse import urljoin, urlparse
import time
import logging

try:
    from .logger import get_logger
except ImportError:
    from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PageSnapshot:
    """Snapshot of a monitored page's critical elements."""
    url: str
    timestamp: str
    content_hash: str
    form_fields: List[str]
    critical_elements: Dict[str, str]  # CSS selector -> element info
    javascript_functions: List[str]
    meta_info: Dict[str, str]  # Page title, description, etc.
    status_code: int
    response_time_ms: int

@dataclass
class ChangeDetection:
    """Details about detected changes."""
    change_type: str  # 'form', 'element', 'javascript', 'content', 'structure'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    old_value: str
    new_value: str
    affected_functionality: List[str]  # What features might be affected
    recommended_action: str
    timestamp: str

@dataclass
class MonitoringConfig:
    """Configuration for API monitoring."""
    check_interval_hours: int = 4  # How often to check
    critical_pages: List[str] = None  # URLs to monitor
    form_selectors: List[str] = None  # Important form selectors
    element_selectors: Dict[str, str] = None  # Critical elements to track
    javascript_patterns: List[str] = None  # Important JS function patterns
    max_response_time_ms: int = 10000  # Alert if slower than this
    
    def __post_init__(self):
        if self.critical_pages is None:
            self.critical_pages = [
                "https://www.portaldasfinancas.gov.pt/",
                "https://www.portaldasfinancas.gov.pt/at/html/index.html",
                "https://servicos.portaldasfinancas.gov.pt/",
            ]
        
        if self.form_selectors is None:
            self.form_selectors = [
                "form[name='loginForm']",
                "form#loginForm", 
                "form.login-form",
                "input[name='username']",
                "input[name='password']",
                "input[type='submit']",
            ]
        
        if self.element_selectors is None:
            self.element_selectors = {
                "login_button": "input[type='submit'], button[type='submit']",
                "username_field": "input[name='username'], input[id='username']",
                "password_field": "input[name='password'], input[id='password']", 
                "error_messages": ".error, .alert-danger, .message-error",
                "success_messages": ".success, .alert-success, .message-success",
                "2fa_elements": "input[name*='token'], input[name*='code'], .two-factor",
            }
        
        if self.javascript_patterns is None:
            self.javascript_patterns = [
                r"function\s+login\s*\(",
                r"function\s+authenticate\s*\(",
                r"function\s+submitForm\s*\(",
                r"ajax\s*\(\s*{",
                r"\.post\s*\(",
                r"fetch\s*\(",
            ]


class PortalAPIMonitor:
    """Monitor Portal das Finanças for API and interface changes."""
    
    def __init__(self, data_dir: str = "monitoring_data"):
        self.data_dir = data_dir
        self.snapshots_file = os.path.join(data_dir, "page_snapshots.json")
        self.changes_file = os.path.join(data_dir, "detected_changes.json")
        self.config_file = os.path.join(data_dir, "monitor_config.json")
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Load or create configuration
        self.config = self._load_config()
        
        # Load existing snapshots and changes
        self.snapshots = self._load_snapshots()
        self.changes = self._load_changes()
        
        # Setup session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-PT,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _load_config(self) -> MonitoringConfig:
        """Load monitoring configuration."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return MonitoringConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        # Create default config
        config = MonitoringConfig()
        self._save_config(config)
        return config
    
    def _save_config(self, config: MonitoringConfig):
        """Save monitoring configuration."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _load_snapshots(self) -> List[PageSnapshot]:
        """Load previous page snapshots."""
        if os.path.exists(self.snapshots_file):
            try:
                with open(self.snapshots_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return [PageSnapshot(**snapshot) for snapshot in data]
            except Exception as e:
                logger.warning(f"Failed to load snapshots: {e}")
        return []
    
    def _save_snapshots(self):
        """Save page snapshots."""
        try:
            data = [asdict(snapshot) for snapshot in self.snapshots]
            with open(self.snapshots_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save snapshots: {e}")
    
    def _load_changes(self) -> List[ChangeDetection]:
        """Load detected changes."""
        if os.path.exists(self.changes_file):
            try:
                with open(self.changes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return [ChangeDetection(**change) for change in data]
            except Exception as e:
                logger.warning(f"Failed to load changes: {e}")
        return []
    
    def _save_changes(self):
        """Save detected changes."""
        try:
            data = [asdict(change) for change in self.changes]
            with open(self.changes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save changes: {e}")
    
    def capture_page_snapshot(self, url: str) -> Optional[PageSnapshot]:
        """Capture a snapshot of a page's critical elements."""
        try:
            logger.info(f"Capturing snapshot for {url}")
            start_time = time.time()
            
            response = self.session.get(url, timeout=30)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code != 200:
                logger.warning(f"Non-200 response for {url}: {response.status_code}")
                return None
            
            content = response.text
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # Extract form fields
            form_fields = self._extract_form_fields(content)
            
            # Extract critical elements
            critical_elements = self._extract_critical_elements(content)
            
            # Extract JavaScript functions
            javascript_functions = self._extract_javascript_functions(content)
            
            # Extract meta information
            meta_info = self._extract_meta_info(content)
            
            snapshot = PageSnapshot(
                url=url,
                timestamp=datetime.now().isoformat(),
                content_hash=content_hash,
                form_fields=form_fields,
                critical_elements=critical_elements,
                javascript_functions=javascript_functions,
                meta_info=meta_info,
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
            
            logger.info(f"Captured snapshot for {url}: {len(form_fields)} forms, {len(critical_elements)} elements")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to capture snapshot for {url}: {e}")
            return None
    
    def _extract_form_fields(self, content: str) -> List[str]:
        """Extract form field information."""
        form_fields = []
        
        # Extract form tags and their attributes
        form_pattern = r'<form[^>]*>(.*?)</form>'
        forms = re.findall(form_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for form in forms:
            # Extract input fields
            input_pattern = r'<input[^>]*>'
            inputs = re.findall(input_pattern, form, re.IGNORECASE)
            
            for input_tag in inputs:
                # Extract name, type, id attributes
                name_match = re.search(r'name=["\']([^"\']*)["\']', input_tag, re.IGNORECASE)
                type_match = re.search(r'type=["\']([^"\']*)["\']', input_tag, re.IGNORECASE)
                id_match = re.search(r'id=["\']([^"\']*)["\']', input_tag, re.IGNORECASE)
                
                field_info = {
                    'tag': 'input',
                    'name': name_match.group(1) if name_match else '',
                    'type': type_match.group(1) if type_match else '',
                    'id': id_match.group(1) if id_match else '',
                }
                
                form_fields.append(json.dumps(field_info, sort_keys=True))
        
        return list(set(form_fields))  # Remove duplicates
    
    def _extract_critical_elements(self, content: str) -> Dict[str, str]:
        """Extract critical page elements."""
        critical_elements = {}
        
        # This is a simplified version - in practice, you'd use BeautifulSoup
        # or a similar library for more robust HTML parsing
        
        for element_name, selector in self.config.element_selectors.items():
            # Simple regex-based extraction (would be better with proper HTML parser)
            if 'input[name' in selector:
                name_pattern = selector.replace('input[name=\'', '').replace('\']', '').replace('input[name="', '').replace('"]', '')
                pattern = f'<input[^>]*name=["\']?{re.escape(name_pattern)}["\']?[^>]*>'
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    critical_elements[element_name] = matches[0]
            elif selector.startswith('.'):
                class_name = selector[1:]  # Remove the dot
                pattern = f'<[^>]*class=["\'][^"\']*{re.escape(class_name)}[^"\']*["\'][^>]*>'
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    critical_elements[element_name] = str(len(matches))  # Count of elements
        
        return critical_elements
    
    def _extract_javascript_functions(self, content: str) -> List[str]:
        """Extract JavaScript function signatures."""
        javascript_functions = []
        
        for pattern in self.config.javascript_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            javascript_functions.extend(matches)
        
        return list(set(javascript_functions))  # Remove duplicates
    
    def _extract_meta_info(self, content: str) -> Dict[str, str]:
        """Extract meta information from page."""
        meta_info = {}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            meta_info['title'] = title_match.group(1).strip()
        
        # Extract meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
        if desc_match:
            meta_info['description'] = desc_match.group(1)
        
        # Extract viewport
        viewport_match = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
        if viewport_match:
            meta_info['viewport'] = viewport_match.group(1)
        
        return meta_info
    
    def compare_snapshots(self, old_snapshot: PageSnapshot, new_snapshot: PageSnapshot) -> List[ChangeDetection]:
        """Compare two snapshots and detect changes."""
        changes = []
        
        # Compare content hash
        if old_snapshot.content_hash != new_snapshot.content_hash:
            changes.append(ChangeDetection(
                change_type='content',
                severity='low',
                description='Page content has changed',
                old_value=old_snapshot.content_hash,
                new_value=new_snapshot.content_hash,
                affected_functionality=['general'],
                recommended_action='Review page changes for impact',
                timestamp=datetime.now().isoformat()
            ))
        
        # Compare form fields
        old_fields = set(old_snapshot.form_fields)
        new_fields = set(new_snapshot.form_fields)
        
        if old_fields != new_fields:
            removed_fields = old_fields - new_fields
            added_fields = new_fields - old_fields
            
            if removed_fields or added_fields:
                severity = 'high' if any('password' in field.lower() or 'username' in field.lower() for field in removed_fields | added_fields) else 'medium'
                
                changes.append(ChangeDetection(
                    change_type='form',
                    severity=severity,
                    description=f'Form fields changed: {len(removed_fields)} removed, {len(added_fields)} added',
                    old_value=str(list(removed_fields)[:3]),  # Show first 3
                    new_value=str(list(added_fields)[:3]),    # Show first 3
                    affected_functionality=['authentication', 'form_submission'],
                    recommended_action='Update form field selectors and validation',
                    timestamp=datetime.now().isoformat()
                ))
        
        # Compare critical elements
        for element_name in set(old_snapshot.critical_elements.keys()) | set(new_snapshot.critical_elements.keys()):
            old_value = old_snapshot.critical_elements.get(element_name, '')
            new_value = new_snapshot.critical_elements.get(element_name, '')
            
            if old_value != new_value:
                severity = 'critical' if 'login' in element_name or 'password' in element_name else 'medium'
                
                changes.append(ChangeDetection(
                    change_type='element',
                    severity=severity,
                    description=f'Critical element "{element_name}" changed',
                    old_value=old_value[:100],  # Truncate for readability
                    new_value=new_value[:100],
                    affected_functionality=['authentication', 'navigation'],
                    recommended_action='Update element selectors in web client',
                    timestamp=datetime.now().isoformat()
                ))
        
        # Compare response time
        if new_snapshot.response_time_ms > self.config.max_response_time_ms:
            changes.append(ChangeDetection(
                change_type='performance',
                severity='medium',
                description=f'Page response time exceeded threshold',
                old_value=str(old_snapshot.response_time_ms),
                new_value=str(new_snapshot.response_time_ms),
                affected_functionality=['performance', 'user_experience'],
                recommended_action='Monitor server performance and adjust timeouts',
                timestamp=datetime.now().isoformat()
            ))
        
        return changes
    
    def monitor_all_pages(self) -> Tuple[List[PageSnapshot], List[ChangeDetection]]:
        """Monitor all configured pages for changes."""
        new_snapshots = []
        all_changes = []
        
        logger.info(f"Starting monitoring of {len(self.config.critical_pages)} pages")
        
        for url in self.config.critical_pages:
            snapshot = self.capture_page_snapshot(url)
            if not snapshot:
                continue
                
            new_snapshots.append(snapshot)
            
            # Find previous snapshot for this URL
            previous_snapshot = None
            for old_snapshot in self.snapshots:
                if old_snapshot.url == url:
                    previous_snapshot = old_snapshot
                    break
            
            if previous_snapshot:
                changes = self.compare_snapshots(previous_snapshot, snapshot)
                all_changes.extend(changes)
                
                if changes:
                    logger.info(f"Detected {len(changes)} changes for {url}")
                    for change in changes:
                        logger.info(f"  {change.severity.upper()}: {change.description}")
            else:
                logger.info(f"No previous snapshot found for {url} - this is the baseline")
        
        # Update snapshots (keep only latest for each URL)
        self.snapshots = new_snapshots
        self.changes.extend(all_changes)
        
        # Save updates
        self._save_snapshots()
        self._save_changes()
        
        return new_snapshots, all_changes
    
    def get_recent_changes(self, hours: int = 24) -> List[ChangeDetection]:
        """Get changes detected in the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_changes = []
        
        for change in self.changes:
            try:
                change_time = datetime.fromisoformat(change.timestamp)
                if change_time > cutoff_time:
                    recent_changes.append(change)
            except ValueError:
                # Skip changes with invalid timestamps
                continue
        
        return recent_changes
    
    def get_critical_changes(self) -> List[ChangeDetection]:
        """Get all critical and high severity changes."""
        return [change for change in self.changes if change.severity in ['critical', 'high']]
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate a comprehensive monitoring report."""
        recent_changes = self.get_recent_changes(24)
        critical_changes = self.get_critical_changes()
        
        # Calculate statistics
        total_snapshots = len(self.snapshots)
        total_changes = len(self.changes)
        
        severity_counts = {}
        for change in self.changes:
            severity_counts[change.severity] = severity_counts.get(change.severity, 0) + 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'monitoring_status': 'active',
            'total_pages_monitored': len(self.config.critical_pages),
            'total_snapshots_taken': total_snapshots,
            'total_changes_detected': total_changes,
            'recent_changes_24h': len(recent_changes),
            'critical_changes_total': len(critical_changes),
            'severity_breakdown': severity_counts,
            'last_check_times': {
                snapshot.url: snapshot.timestamp for snapshot in self.snapshots
            },
            'critical_changes': [asdict(change) for change in critical_changes[-5:]],  # Last 5
            'recent_changes': [asdict(change) for change in recent_changes[-10:]],     # Last 10
        }
    
    def should_run_check(self) -> bool:
        """Check if it's time to run monitoring based on configured interval."""
        if not self.snapshots:
            return True  # Always run if no previous snapshots
        
        # Find the most recent snapshot
        latest_time = None
        for snapshot in self.snapshots:
            try:
                snapshot_time = datetime.fromisoformat(snapshot.timestamp)
                if latest_time is None or snapshot_time > latest_time:
                    latest_time = snapshot_time
            except ValueError:
                continue
        
        if latest_time is None:
            return True
        
        time_diff = datetime.now() - latest_time
        return time_diff.total_seconds() >= (self.config.check_interval_hours * 3600)


def create_default_monitor() -> PortalAPIMonitor:
    """Create a Portal API monitor with default configuration."""
    return PortalAPIMonitor()


class APIPayloadMonitor:
    """
    Lightweight API monitor - validates payloads and detects endpoint changes.
    Does NOT record data, only validates and warns.
    """
    
    def __init__(self):
        """Initialize monitor without data persistence."""
        self.known_endpoints = {
            '/arrendamento/api/emitirRecibo': {
                'method': 'POST',
                'required_fields': [
                    'numContrato', 'versaoContrato', 'nifEmitente', 'nomeEmitente',
                    'valor', 'tipoContrato', 'locadores', 'locatarios', 'imoveis',
                    'dataInicio', 'dataFim', 'dataRecebimento', 'tipoImportancia'
                ]
            },
            '/arrendamento/api/obterElementosContratosEmissaoRecibos/locador': {
                'method': 'GET',
                'required_fields': []
            },
            '/arrendamento/criarRecibo': {
                'method': 'GET',
                'required_fields': []
            }
        }
    
    def validate_api_call(self, endpoint: str, method: str, payload: Dict = None,
                         response_status: int = None, response_data: Any = None,
                         error: str = None, contract_id: str = None):
        """
        Validate API call and warn about issues.
        Does NOT persist data, only validates and logs warnings.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            payload: Request payload
            response_status: HTTP status code
            response_data: Response data
            error: Error message if failed
            contract_id: Contract ID for context
        """
        # Check if endpoint is known
        if endpoint not in self.known_endpoints:
            logger.warning(f" UNKNOWN ENDPOINT: {method} {endpoint}")
            logger.warning(f"   This endpoint is not in the known list - API may have changed!")
            return
        
        endpoint_info = self.known_endpoints[endpoint]
        
        # Check if method matches
        if method != endpoint_info['method']:
            logger.warning(f" METHOD CHANGED: {endpoint}")
            logger.warning(f"   Expected: {endpoint_info['method']}, Got: {method}")
        
        # Validate payload if present
        if payload and endpoint_info['required_fields']:
            missing = self._check_required_fields(endpoint, payload)
            if missing:
                logger.error(f"MISSING REQUIRED FIELDS in {endpoint}:")
                for field in missing:
                    logger.error(f"   • {field}")
                logger.error(f"   Contract ID: {contract_id}")
                logger.error(f"   This will likely cause submission to fail!")
        
        # Detect endpoint deprecation or errors
        if response_status and response_status == 404:
            logger.error(f"ENDPOINT NOT FOUND: {endpoint}")
            logger.error(f"   The API endpoint may have been removed or moved!")
        elif response_status and response_status == 410:
            logger.error(f"ENDPOINT DEPRECATED: {endpoint}")
            logger.error(f"   This endpoint is no longer supported!")
        elif response_status and response_status >= 500:
            logger.error(f"SERVER ERROR on {endpoint}: HTTP {response_status}")
            if error:
                logger.error(f"   Error: {error}")
    
    def _check_required_fields(self, endpoint: str, payload: Dict) -> List[str]:
        """Check if required fields are present in payload."""
        if endpoint not in self.known_endpoints:
            return []
        
        required_fields = self.known_endpoints[endpoint]['required_fields']
        missing = []
        
        # Check top-level fields
        for field in required_fields:
            if field not in payload or payload[field] is None:
                missing.append(field)
        
        # Check nested required fields for receipt submission
        if endpoint == '/arrendamento/api/emitirRecibo':
            # Check locadores NIFs
            if 'locadores' in payload and payload['locadores']:
                for i, locador in enumerate(payload['locadores']):
                    if 'nif' not in locador or locador['nif'] is None:
                        missing.append(f'locadores[{i}].nif')
            
            # Check locatarios NIFs
            if 'locatarios' in payload and payload['locatarios']:
                for i, locatario in enumerate(payload['locatarios']):
                    if 'nif' not in locatario or locatario['nif'] is None:
                        missing.append(f'locatarios[{i}].nif')
            
            # Check imoveis data
            if 'imoveis' in payload and payload['imoveis']:
                for i, imovel in enumerate(payload['imoveis']):
                    if 'morada' not in imovel or not imovel['morada']:
                        missing.append(f'imoveis[{i}].morada')
            elif 'imoveis' not in payload or not payload['imoveis']:
                missing.append('imoveis (array is empty or missing)')
        
        return missing


# For backward compatibility, use APIPayloadMonitor as default
APIMonitor = APIPayloadMonitor


if __name__ == "__main__":
    # Demo usage
    monitor = create_default_monitor()
    
    print(" Portal das Finanças API Monitor Demo")
    print("=" * 50)
    
    if monitor.should_run_check():
        print(" Running scheduled monitoring check...")
        snapshots, changes = monitor.monitor_all_pages()
        
        print(f" Captured {len(snapshots)} snapshots")
        print(f" Detected {len(changes)} changes")
        
        if changes:
            print("\n Recent Changes:")
            for change in changes:
                print(f"  {change.severity.upper()}: {change.description}")
    else:
        print("⏸️ No monitoring check needed at this time")
    
    # Generate report
    report = monitor.generate_monitoring_report()
    print(f"\n Monitoring Report:")
    print(f"  Total pages monitored: {report['total_pages_monitored']}")
    print(f"  Total changes detected: {report['total_changes_detected']}")
    print(f"  Critical changes: {report['critical_changes_total']}")
    print(f"  Recent changes (24h): {report['recent_changes_24h']}")
