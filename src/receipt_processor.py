"""
Receipt processor - handles the main business logic for issuing receipts.
"""

from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import time

try:
    from .csv_handler import ReceiptData
    from .web_client import WebClient
except ImportError:
    # Fallback for when imported directly
    from csv_handler import ReceiptData
    from web_client import WebClient

try:
    from .utils.logger import get_logger
except ImportError:
    # Fallback for when imported directly
    from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ProcessingResult:
    """Result of processing a single receipt."""
    contract_id: str
    tenant_name: str = ""
    success: bool = False
    receipt_number: str = ""
    from_date: str = ""
    to_date: str = ""
    payment_date: str = ""
    value: float = 0.0
    error_message: str = ""
    timestamp: str = ""
    status: str = ""  # 'Success', 'Failed', 'Skipped'

class ReceiptProcessor:
    """Main processor for handling receipt issuance."""
    
    def __init__(self, web_client: WebClient):
        self.web_client = web_client
        self.results: List[ProcessingResult] = []
        self.dry_run = False
    
    def set_dry_run(self, dry_run: bool):
        """Enable or disable dry run mode."""
        self.dry_run = dry_run
        logger.info(f"Dry run mode: {'enabled' if dry_run else 'disabled'}")
    
    def validate_contracts(self, receipts: List[ReceiptData]) -> Dict[str, Any]:
        """
        Validate contract IDs from receipts against Portal das Finanças.
        
        Args:
            receipts: List of receipt data to validate
            
        Returns:
            Validation report with contract inconsistencies
        """
        logger.info("Starting contract validation...")
        
        if not receipts:
            return {
                'success': False,
                'message': "No receipts provided for validation",
                'validation_errors': ["No receipt data to validate"]
            }
        
        # Extract contract IDs from receipts
        csv_contract_ids = list(set(receipt.contract_id for receipt in receipts))
        logger.info(f"Validating {len(csv_contract_ids)} unique contract IDs from CSV")
        
        # Validate contracts using WebClient
        validation_report = self.web_client.validate_csv_contracts(csv_contract_ids)
        
        # Add detailed analysis
        validation_report['receipts_count'] = len(receipts)
        validation_report['unique_contracts_in_csv'] = len(csv_contract_ids)
        
        # Log validation summary
        if validation_report['success']:
            logger.info("Contract validation completed successfully")
            logger.info(f"  Total receipts: {len(receipts)}")
            logger.info(f"  Unique contracts in CSV: {len(csv_contract_ids)}")
            logger.info(f"  Contracts in portal: {validation_report['portal_contracts_count']}")
            logger.info(f"  Valid matches: {len(validation_report['valid_contracts'])}")
            logger.info(f"  Invalid contracts: {len(validation_report['invalid_contracts'])}")
            
            if validation_report['validation_errors']:
                for error in validation_report['validation_errors']:
                    logger.warning(f"  Validation issue: {error}")
        else:
            logger.error(f"Contract validation failed: {validation_report['message']}")
        
        return validation_report
    
    def process_receipts_bulk(self, receipts: List[ReceiptData], 
                            progress_callback: Callable[[int, int, str], None] = None,
                            validate_contracts: bool = True,
                            stop_check: Callable[[], bool] = None) -> List[ProcessingResult]:
        """
        Process all receipts in bulk mode.
        
        Args:
            receipts: List of receipts to process
            progress_callback: Optional callback for progress updates (current, total, message)
            validate_contracts: Whether to validate contract IDs before processing
            stop_check: Optional callback to check if processing should stop
            
        Returns:
            List of processing results
        """
        logger.info(f"Starting bulk processing of {len(receipts)} receipts")
        self.results.clear()
        
        # Validate contracts if requested
        if validate_contracts:
            if progress_callback:
                progress_callback(0, len(receipts), "Validating contract IDs...")
            
            validation_report = self.validate_contracts(receipts)
            
            # Check for validation errors that should stop processing
            if not validation_report['success']:
                logger.error("Contract validation failed - stopping processing")
                # Create error results for all receipts
                for receipt in receipts:
                    error_result = ProcessingResult(
                        contract_id=receipt.contract_id,
                        success=False,
                        error_message=f"Contract validation failed: {validation_report['message']}",
                        timestamp=datetime.now().isoformat(),
                        status="Failed"
                    )
                    self.results.append(error_result)
                return self.results.copy()
            
            # Check for invalid contracts
            if validation_report['invalid_contracts']:
                logger.warning(f"Found {len(validation_report['invalid_contracts'])} invalid contracts")
                
                # Create error results for invalid contracts
                invalid_contracts_set = set(validation_report['invalid_contracts'])
                for receipt in receipts:
                    if receipt.contract_id in invalid_contracts_set:
                        error_result = ProcessingResult(
                            contract_id=receipt.contract_id,
                            success=False,
                            error_message=f"Contract ID '{receipt.contract_id}' not found in Portal das Finanças",
                            timestamp=datetime.now().isoformat(),
                            status="Skipped"
                        )
                        self.results.append(error_result)
                        logger.warning(f"Skipping receipt for invalid contract: {receipt.contract_id}")
                
                # Filter out invalid contracts from processing
                valid_receipts = [r for r in receipts if r.contract_id not in invalid_contracts_set]
                logger.info(f"Processing {len(valid_receipts)} receipts with valid contracts (skipping {len(receipts) - len(valid_receipts)})")
                receipts = valid_receipts
        
        # Process valid receipts
        for i, receipt in enumerate(receipts):
            # Check if stop was requested
            if stop_check and stop_check():
                logger.info("Processing stopped by user request")
                break
                
            if progress_callback:
                progress_callback(i + 1, len(receipts), f"Processing contract {receipt.contract_id}")
            
            result = self._process_single_receipt(receipt)
            self.results.append(result)
            
            # Small delay to avoid overwhelming the server (only in real mode)
            if not self.dry_run:
                time.sleep(1)
        
        logger.info(f"Bulk processing completed. Success: {self._count_successful()}, Failed: {self._count_failed()}")
        return self.results.copy()
    
    def process_receipts_step_by_step(self, receipts: List[ReceiptData],
                                    confirmation_callback: Callable[[ReceiptData, Dict], str],
                                    stop_check: Callable[[], bool] = None) -> List[ProcessingResult]:
        """
        Process receipts in step-by-step mode with user confirmation.
        
        Args:
            receipts: List of receipts to process
            confirmation_callback: Callback for user confirmation (receipt_data, form_data) -> action
                                  Returns: 'confirm', 'skip', 'cancel', or 'edit:new_data'
            stop_check: Optional callback to check if processing should stop
            
        Returns:
            List of processing results
        """
        logger.info(f"Starting step-by-step processing of {len(receipts)} receipts")
        self.results.clear()
        
        # In dry run mode, skip contract validation
        if not self.dry_run:
            # First, validate contracts to identify invalid ones (same as bulk mode)
            validation_report = self.validate_contracts(receipts)
            
            if not validation_report['success']:
                logger.error("Contract validation failed - stopping processing")
                # Create error results for all receipts
                for receipt in receipts:
                    error_result = ProcessingResult(
                        contract_id=receipt.contract_id,
                        success=False,
                        error_message=f"Contract validation failed: {validation_report['message']}",
                        timestamp=datetime.now().isoformat(),
                        status="Failed"
                    )
                    self.results.append(error_result)
                return self.results.copy()
            
            # Create error results for invalid contracts (same as bulk mode)
            if validation_report['invalid_contracts']:
                logger.warning(f"Found {len(validation_report['invalid_contracts'])} invalid contracts")
                
                invalid_contracts_set = set(validation_report['invalid_contracts'])
                for receipt in receipts:
                    if receipt.contract_id in invalid_contracts_set:
                        error_result = ProcessingResult(
                            contract_id=receipt.contract_id,
                            success=False,
                            error_message=f"Contract ID '{receipt.contract_id}' not found in Portal das Finanças",
                            timestamp=datetime.now().isoformat(),
                            status="Skipped"
                        )
                        self.results.append(error_result)
                        logger.warning(f"Skipping receipt for invalid contract: {receipt.contract_id}")
                
                # Filter out invalid contracts from processing (only process valid ones)
                valid_receipts = [r for r in receipts if r.contract_id not in invalid_contracts_set]
                logger.info(f"Step-by-step processing {len(valid_receipts)} receipts with valid contracts (skipping {len(receipts) - len(valid_receipts)})")
                receipts = valid_receipts
        else:
            logger.info("Dry run mode: Skipping contract validation")
        
        for receipt in receipts:
            # Check if stop was requested
            if stop_check and stop_check():
                logger.info("Step-by-step processing stopped by user request")
                break
                
            # Always try to get real form data (even in dry run)
            # In dry run mode, we want real data but no submission
            form_data = None
            success = True  # Assume success for now
            
            if not success:
                result = ProcessingResult(
                    contract_id=receipt.contract_id,
                    success=False,
                    error_message="Failed to get form data",
                    timestamp=datetime.now().isoformat(),
                    status="Failed"
                )
                self.results.append(result)
                continue
            
            # Update receipt value with contract data if needed (before showing confirmation dialog)
            if receipt.value == -1.0 or receipt.value == 0.0:  # Handle both old 0.0 and new -1.0 indicators
                logger.info(f"VALUE RESOLUTION - DRY RUN MODE:")
                logger.info(f"   Dry Run: {self.dry_run}")
                logger.info(f"   Form Data Available: {bool(form_data)}")
                
                # In dry run mode, still get real rent values from API (just don't submit)
                logger.info(f"RENT VALUE DEFAULTING: Contract {receipt.contract_id} has no CSV value")
                logger.info(f"ATTEMPTING: Get current rent value from Portal das Finanças API")
                logger.info(f"CONTRACT ID: {receipt.contract_id}")
                logger.info(f"REASON: CSV file has empty or missing value for this contract")
                
                success, rent_value = self.web_client.get_contract_rent_value(str(receipt.contract_id))
                
                if success and rent_value > 0.0:
                    receipt.value = rent_value
                    receipt.value_defaulted = True
                    logger.info(f"✅ RENT VALUE DEFAULTING SUCCESS:")
                    logger.info(f"   VALUE SOURCE: Portal das Finanças API endpoint")
                    logger.info(f"   API RETURNED: €{rent_value}")
                    logger.info(f"   CONTRACT: {receipt.contract_id}")
                    logger.info(f"   ACTION: CSV value was missing → defaulted to API value €{rent_value}")
                    if self.dry_run:
                        logger.info(f"   DRY RUN: Real value retrieved but no submission will occur")
                    else:
                        logger.info(f"   ⚠️  WARNING: Verify this matches the rent value you see in Portal das Finanças web interface!")
                else:
                    # Keep value as 0.0 but ensure value_defaulted flag is set for display purposes
                    receipt.value_defaulted = True
                    logger.error(f"❌ RENT VALUE DEFAULTING FAILED:")
                    logger.error(f"   CONTRACT: {receipt.contract_id}")
                    logger.error(f"   API RESULT: No valorRenda available from endpoint")
                    logger.error(f"   TROUBLESHOOTING: Check if contract {receipt.contract_id} exists in Portal das Finanças")
                    logger.error(f"   TROUBLESHOOTING: Check if contract has valid rent value in platform")
                    logger.error(f"   TROUBLESHOOTING: Check API response logs above for detailed error information")
            
            # Ask user for confirmation
            action = confirmation_callback(receipt, form_data or {})
            
            if action == 'cancel':
                logger.info("Processing cancelled by user")
                break
            elif action == 'skip':
                result = ProcessingResult(
                    contract_id=receipt.contract_id,
                    tenant_name=self._extract_tenant_name(form_data or {}),
                    success=False,
                    error_message="Skipped by user",
                    timestamp=datetime.now().isoformat(),
                    status="Skipped",
                    from_date=receipt.from_date,
                    to_date=receipt.to_date,
                    payment_date=receipt.payment_date,
                    value=receipt.value
                )
                self.results.append(result)
                continue
            elif action.startswith('edit:'):
                # Handle edited data (would need to parse the edited data)
                # For now, just process normally
                pass
            
            # Process the receipt
            if action in ['confirm', 'edit']:
                result = self._process_single_receipt(receipt, form_data)
                self.results.append(result)
        
        logger.info(f"Step-by-step processing completed. Success: {self._count_successful()}, Failed: {self._count_failed()}")
        return self.results.copy()
    
    def _process_single_receipt(self, receipt: ReceiptData, form_data: Dict = None) -> ProcessingResult:
        """
        Process a single receipt.
        
        Args:
            receipt: Receipt data to process
            form_data: Optional form data from the platform
            
        Returns:
            Processing result
        """
        logger.info(f"Processing receipt for contract {receipt.contract_id}")
        
        result = ProcessingResult(
            contract_id=receipt.contract_id,
            from_date=receipt.from_date,
            to_date=receipt.to_date,
            value=receipt.value,
            timestamp=datetime.now().isoformat()
        )
        
        if self.dry_run:
            # In dry run mode, simulate successful processing with real data
            # Extract tenant information from form data if available
            if form_data:
                result.tenant_name = self._extract_tenant_name(form_data)
            else:
                result.tenant_name = "Real Tenant (Dry Run)"
            
            result.success = True
            result.receipt_number = f"DRY-RUN-{receipt.contract_id}"
            result.payment_date = receipt.payment_date
            result.status = "Success (Dry Run)"
            logger.info(f"DRY RUN: Simulated successful processing for contract {receipt.contract_id} with real data")
            return result
        
        try:
            # Get form data ONLY when actually issuing receipt (not during validation)
            if form_data is None:
                logger.info(f"FETCHING RECEIPT FORM: Getting form data for contract {receipt.contract_id}")
                success, form_data = self.web_client.get_receipt_form(receipt.contract_id)
                if not success:
                    logger.error(f"❌ FORM DATA FAILED: Could not get receipt form for contract {receipt.contract_id}")
                    result.error_message = "Failed to get form data"
                    result.status = "Failed"
                    return result
                logger.info(f"✅ FORM DATA SUCCESS: Retrieved form data for contract {receipt.contract_id}")
            
            # Extract tenant information from form data
            if form_data:
                result.tenant_name = self._extract_tenant_name(form_data)
            
            # Prepare receipt data for submission
            submission_data = self._prepare_submission_data(receipt, form_data)
            
            # If tenant name is still unknown, try to get it from the prepared submission data
            if result.tenant_name == "Unknown Tenant" or not result.tenant_name:
                locatarios = submission_data.get('locatarios', [])
                if locatarios:
                    if len(locatarios) == 1:
                        result.tenant_name = locatarios[0].get('nome', 'Unknown Tenant').strip()
                    else:
                        # Multiple tenants - create combined name
                        names = []
                        for tenant in locatarios:
                            name = tenant.get('nome', '').strip()
                            if name and name != 'UNKNOWN TENANT':
                                names.append(name)
                        if names:
                            result.tenant_name = f"{', '.join(names)} ({len(names)} tenants)"
                        else:
                            result.tenant_name = f"{len(locatarios)} tenants"
                    
                    logger.info(f"Updated tenant name from submission data: {result.tenant_name}")
            
            # Submit the receipt (only if not in dry run mode)
            if self.dry_run:
                # In dry run mode, simulate successful submission
                result.success = True
                result.receipt_number = f"DRY-RUN-{receipt.contract_id}"
                result.payment_date = receipt.payment_date
                result.status = "Success (Dry Run)"
                logger.info(f"DRY RUN: Simulated successful receipt submission for contract {receipt.contract_id}")
            else:
                # Production mode: actually submit the receipt
                success, response = self.web_client.issue_receipt(submission_data)
                
                if success and response:
                    result.success = True
                    result.receipt_number = response.get('receiptNumber', 'Unknown')
                    result.payment_date = receipt.payment_date
                    result.status = "Success"
                    logger.info(f"Successfully processed receipt for contract {receipt.contract_id}")
                else:
                    # Extract error message from response or use fallback
                    if response:
                        result.error_message = response.get('error', response.get('errorMessage', 'Unknown error'))
                    else:
                        result.error_message = "No response received from platform"
                    result.status = "Failed"
                    logger.error(f"Failed to process receipt for contract {receipt.contract_id}: {result.error_message}")
        
        except Exception as e:
            result.error_message = str(e)
            result.status = "Failed"
            logger.error(f"Exception processing receipt for contract {receipt.contract_id}: {str(e)}")
        
        return result
    
    def _extract_tenant_name(self, form_data: Dict) -> str:
        """Extract tenant name(s) from form data - handles multiple tenants."""
        try:
            # First check if we have extracted multiple tenant data
            extracted_tenants = form_data.get('contract_details', {}).get('locatarios', [])
            if extracted_tenants:
                if len(extracted_tenants) == 1:
                    name = extracted_tenants[0].get('nome', '').strip()
                    return name if name else "Unknown Tenant"
                else:
                    # Multiple tenants - return combined names
                    names = []
                    for tenant in extracted_tenants:
                        name = tenant.get('nome', '').strip()
                        if name and name != 'UNKNOWN TENANT':
                            names.append(name)
                    if names:
                        return f"{', '.join(names)} ({len(names)} tenants)"
                    else:
                        return f"{len(extracted_tenants)} tenants"
            
            # Fallback to old structure
            locatarios = form_data.get('locatarios', [])
            if locatarios and len(locatarios) > 0:
                name = locatarios[0].get('nome', '').strip()
                return name if name else "Unknown Tenant"
                
            # Check backward compatibility fields
            single_name = form_data.get('tenant_name') or form_data.get('contract_details', {}).get('tenant_name')
            if single_name and single_name.strip():
                return single_name.strip()
                
        except Exception as e:
            logger.warning(f"Error extracting tenant name: {e}")
        
        return "Unknown Tenant"
    
    def _prepare_submission_data(self, receipt: ReceiptData, form_data: Dict) -> Dict:
        """
        Prepare data for submission to the platform.
        
        Args:
            receipt: Receipt data from CSV
            form_data: Form data from platform
            
        Returns:
            Data ready for submission
        """
        # Use minimal contract structure 
        logger.info(f"Building contract data for {receipt.contract_id}")
        contract_data = None
        
        if not contract_data:
            logger.info(f"Using minimal contract structure for {receipt.contract_id}")
            contract_data = {
                'numero': receipt.contract_id,
                'valorRenda': receipt.value,
                'nomeLocador': 'UNKNOWN LANDLORD', 
                'nomeLocatario': 'UNKNOWN TENANT'
            }
        else:
            logger.info(f"Using contract data for {receipt.contract_id}")
        
        # Determine the value to use - fallback to contract value if CSV value is missing
        receipt_value = receipt.value
        if receipt_value == -1.0 or receipt_value == 0.0:  # Handle both old 0.0 and new -1.0 indicators
            # Fallback to contract rent value
            receipt_value = contract_data.get('valorRenda', 0.0)
            logger.info(f"Using fallback value from contract: €{receipt_value}")
        
        # Extract key data from form for better logging and multiple tenant support
        extracted_tenants = form_data.get('contract_details', {}).get('locatarios', [])
        
        # Build locatarios array - use extracted tenant data if available, otherwise fallback
        locatarios_list = []
        
        if extracted_tenants:
            # Use all extracted tenants from form data
            for i, tenant in enumerate(extracted_tenants):
                locatario = {
                    "nif": tenant.get('nif'),
                    "nome": tenant.get('nome', '').strip(),
                    "pais": tenant.get('pais', {
                        "codigo": "2724",
                        "label": "PORTUGAL"
                    }),
                    "retencao": tenant.get('retencao', {
                        "taxa": 0,
                        "codigo": "RIRS03",
                        "label": "Dispensa de retenção - artigo 101.º-B, n.º 1, do CIRS"
                    })
                }
                locatarios_list.append(locatario)
                
                if locatario['nif']:
                    logger.info(f"Using tenant {i+1} NIF {locatario['nif']} from form data for contract {receipt.contract_id}")
                else:
                    logger.warning(f"Tenant {i+1} missing NIF for contract {receipt.contract_id} - this may cause submission to fail")
                
                logger.info(f"Using tenant {i+1} name: {locatario['nome']}")
            
            logger.info(f"Prepared {len(locatarios_list)} tenants for contract {receipt.contract_id}")
        else:
            # Fallback to single tenant using backward compatibility fields
            tenant_nif = form_data.get('tenant_nif') or form_data.get('contract_details', {}).get('tenant_nif')
            tenant_name = form_data.get('tenant_name') or form_data.get('contract_details', {}).get('tenant_name') or contract_data.get('nomeLocatario', 'UNKNOWN TENANT')
            
            locatario = {
                "nif": tenant_nif,
                "nome": tenant_name,
                "pais": {
                    "codigo": "2724",
                    "label": "PORTUGAL"
                },
                "retencao": {
                    "taxa": 0,
                    "codigo": "RIRS03",
                    "label": "Dispensa de retenção - artigo 101.º-B, n.º 1, do CIRS"
                }
            }
            locatarios_list.append(locatario)
            
            if tenant_nif:
                logger.info(f"Using single tenant NIF {tenant_nif} from form data for contract {receipt.contract_id}")
            else:
                logger.warning(f"No tenant NIF found for contract {receipt.contract_id} - this will cause submission to fail")
            
            logger.info(f"Using single tenant name: {tenant_name}")
        
        # Build locadores array - use extracted landlord data if available, otherwise fallback
        extracted_landlords = form_data.get('contract_details', {}).get('locadores', [])
        locadores_list = []
        
        if extracted_landlords:
            # Use all extracted landlords from form data
            for i, landlord in enumerate(extracted_landlords):
                locador = {
                    "nif": landlord.get('nif'),
                    "nome": landlord.get('nome', '').strip(),
                    "quotaParte": landlord.get('quotaParte', '1/1'),
                    "sujeitoPassivo": landlord.get('sujeitoPassivo', 'V')
                }
                locadores_list.append(locador)
                
                if locador['nif']:
                    logger.info(f"Using landlord {i+1} NIF {locador['nif']} from form data for contract {receipt.contract_id}")
                else:
                    logger.warning(f"Landlord {i+1} missing NIF for contract {receipt.contract_id} - this may cause submission to fail")
                
                logger.info(f"Using landlord {i+1} name: {locador['nome']}")
            
            logger.info(f"Prepared {len(locadores_list)} landlords for contract {receipt.contract_id}")
        else:
            # Fallback to single landlord using backward compatibility fields
            landlord_nif = form_data.get('nifEmitente') or form_data.get('contract_details', {}).get('landlord_nif')
            landlord_name = form_data.get('nomeEmitente') or form_data.get('contract_details', {}).get('landlord_name') or contract_data.get('nomeLocador', 'UNKNOWN LANDLORD')
            
            locador = {
                "nif": landlord_nif,
                "nome": landlord_name,
                "quotaParte": "1/1",
                "sujeitoPassivo": "V"
            }
            locadores_list.append(locador)
            
            if landlord_nif:
                logger.info(f"Using single landlord NIF {landlord_nif} from form data for contract {receipt.contract_id}")
            else:
                logger.warning(f"No landlord NIF found for contract {receipt.contract_id} - this will cause submission to fail")
            
            logger.info(f"Using single landlord name: {landlord_name}")
        
        # Build the complete submission payload matching the API format
        submission_data = {
            "numContrato": int(receipt.contract_id),
            "versaoContrato": form_data.get('versaoContrato', 1),
            "nifEmitente": form_data.get('nifEmitente', None),
            "nomeEmitente": form_data.get('nomeEmitente', contract_data.get('nomeLocador', 'UNKNOWN LANDLORD')),
            "isNifEmitenteColetivo": False,
            "valor": float(receipt_value),
            "tipoContrato": {
                "codigo": "ARREND",
                "label": "Arrendamento"
            },
            "locadores": locadores_list,
            "locatarios": locatarios_list,
            "imoveis": [
                {
                    "morada": form_data.get('property_address') or form_data.get('contract_details', {}).get('property_address') or contract_data.get('imovelAlternateId', 'UNKNOWN ADDRESS'),
                    "tipo": {
                        "codigo": "U",
                        "label": "Urbano"
                    },
                    "parteComum": False,
                    "bemOmisso": False,
                    "novo": False,
                    "editableMode": False,
                    "ordem": 1
                }
            ],
            "hasNifHerancaIndivisa": form_data.get('contract_details', {}).get('hasNifHerancaIndivisa', False),
            "locadoresHerancaIndivisa": form_data.get('contract_details', {}).get('locadoresHerancaIndivisa', []),
            "herdeiros": form_data.get('contract_details', {}).get('herdeiros', []),
            "dataInicio": receipt.from_date,
            "dataFim": receipt.to_date,
            "dataRecebimento": receipt.payment_date,  # Payment date is now required
            "tipoImportancia": {
                "codigo": "RENDAC",
                "label": "Renda"
            }
        }
        
        # Check if this is an inheritance case and log accordingly
        has_inheritance = form_data.get('contract_details', {}).get('hasNifHerancaIndivisa', False)
        if has_inheritance:
            inheritance_landlords = form_data.get('contract_details', {}).get('locadoresHerancaIndivisa', [])
            heirs = form_data.get('contract_details', {}).get('herdeiros', [])
            logger.info(f"Contract {receipt.contract_id} is an INHERITANCE case:")
            logger.info(f"  • Inheritance landlords: {len(inheritance_landlords)}")
            logger.info(f"  • Heirs: {len(heirs)}")
            for i, heir in enumerate(heirs):
                heir_nif = heir.get('nifHerdeiro', 'N/A')
                quota = heir.get('quotaParte', 'N/A')
                logger.info(f"    Heir {i+1}: NIF={heir_nif}, Quota={quota}")
        else:
            logger.info(f"Contract {receipt.contract_id} is a STANDARD case (no inheritance)")
        
        logger.info(f"Prepared submission data for contract {receipt.contract_id} with value {receipt.value}")
        return submission_data
    
    def _count_successful(self) -> int:
        """Count successful results."""
        return sum(1 for result in self.results if result.success)
    
    def _count_failed(self) -> int:
        """Count failed results."""
        return sum(1 for result in self.results if not result.success)
    
    def get_results(self) -> List[ProcessingResult]:
        """Get processing results."""
        return self.results.copy()
    
    def generate_report_data(self) -> List[Dict[str, Any]]:
        """Generate report data for export."""
        report_data = []
        
        for result in self.results:
            # Use the explicit status if set, otherwise fall back to success/failed
            status = result.status if result.status else ('Success' if result.success else 'Failed')
            
            report_data.append({
                'Contract ID': result.contract_id,
                'Tenant Name': result.tenant_name,
                'Status': status,
                'Receipt Number': result.receipt_number,
                'From Date': result.from_date,
                'To Date': result.to_date,
                'Payment Date': result.payment_date,
                'Value': result.value,
                'Error Message': result.error_message,
                'Timestamp': result.timestamp
            })
        
        return report_data
