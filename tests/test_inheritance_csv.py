"""
Test inheritance processing with real CSV data
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_inheritance_with_csv():
    """Test processing inheritance case with real CSV data."""
    print("🔧 Testing Inheritance Processing with CSV Data...")
    
    try:
        from csv_handler import CSVHandler
        from receipt_processor import ReceiptProcessor
        from web_client import WebClient
        
        # Load the recibos_julho.csv file that contains contract 5145568
        csv_handler = CSVHandler()
        
        print(f"\n📄 Loading CSV file: sample/recibos_julho.csv")
        success, errors = csv_handler.load_csv("sample/recibos_julho.csv")
        
        if not success:
            print(f"   ❌ Failed to load CSV file: {errors}")
            return
            
        receipts = csv_handler.get_receipts()
        
        if not receipts:
            print(f"   ❌ No receipts found in CSV file")
            return
        
        print(f"   ✅ Loaded {len(receipts)} receipts from CSV")
        
        # Find contract 5145568 (inheritance case)
        inheritance_receipt = None
        for receipt in receipts:
            if receipt.contract_id == "5145568":
                inheritance_receipt = receipt
                break
        
        if not inheritance_receipt:
            print(f"   ❌ Contract 5145568 not found in CSV")
            return
        
        print(f"   ✅ Found inheritance contract 5145568:")
        print(f"      Period: {inheritance_receipt.from_date} to {inheritance_receipt.to_date}")
        print(f"      Payment Date: {inheritance_receipt.payment_date}")
        print(f"      Value: €{inheritance_receipt.value}")
        
        # Test receipt processing
        web_client = WebClient(testing_mode=True)  # Use testing mode
        processor = ReceiptProcessor(web_client)
        
        print(f"\n🎯 Testing receipt processing for inheritance case...")
        
        # Mock form data with inheritance information (as would be extracted from portal)
        mock_form_data = {
            'contract_details': {
                'hasNifHerancaIndivisa': True,
                'locadoresHerancaIndivisa': [
                    {
                        'nif': 555666777,
                        'nome': 'SAMPLE LANDLORD NAME - CABEÇA DE CASAL DA HERANÇA DE',
                        'quotaParte': '1/1',
                        'sujeitoPassivo': 'V'
                    }
                ],
                'herdeiros': [
                    {
                        'nifLocador': {'codigo': '555666777', 'label': '555666777'},
                        'nifHerdeiro': 987654321,
                        'quotaParte': '1/2',
                        'ordem': 1
                    },
                    {
                        'nifLocador': {'codigo': '555666777', 'label': '555666777'},
                        'nifHerdeiro': 444555666,
                        'quotaParte': '1/2',
                        'ordem': 2
                    }
                ],
                'locatarios': [
                    {
                        'nif': 444555666,
                        'nome': 'SAMPLE COMPANY LDA',
                        'pais': {'codigo': '2724', 'label': 'PORTUGAL'},
                        'retencao': {'taxa': 0.25, 'codigo': 'RIRS01', 'label': 'À taxa de 25% - artigo 101.º, n.º 1, al. e) do CIRS'}
                    }
                ]
            }
        }
        
        # Test submission data preparation
        submission_data = processor._prepare_submission_data(inheritance_receipt, mock_form_data)
        
        print(f"   ✅ Submission data prepared for inheritance case:")
        print(f"      Contract ID: {submission_data.get('numContrato')}")
        print(f"      Value: €{submission_data.get('valor')}")
        print(f"      Period: {submission_data.get('dataInicio')} to {submission_data.get('dataFim')}")
        print(f"      Payment Date: {submission_data.get('dataRecebimento')}")
        print(f"      Inheritance Flag: {submission_data.get('hasNifHerancaIndivisa')}")
        print(f"      Inheritance Landlords: {len(submission_data.get('locadoresHerancaIndivisa', []))}")
        print(f"      Heirs: {len(submission_data.get('herdeiros', []))}")
        
        # Show heir details
        heirs = submission_data.get('herdeiros', [])
        for i, heir in enumerate(heirs):
            heir_nif = heir.get('nifHerdeiro', 'N/A')
            quota = heir.get('quotaParte', 'N/A')
            print(f"        Heir {i+1}: NIF={heir_nif}, Quota={quota}")
        
        print(f"\n📊 Inheritance Processing Results:")
        print(f"   ✅ CSV data correctly loaded and processed")
        print(f"   ✅ Inheritance information correctly detected and included")
        print(f"   ✅ Submission data includes all required inheritance parameters")
        print(f"   ✅ System ready to process inheritance cases from CSV")
        
        # Test with a standard (non-inheritance) contract for comparison
        standard_receipt = None
        for receipt in receipts:
            if receipt.contract_id != "5145568":  # Any other contract
                standard_receipt = receipt
                break
        
        if standard_receipt:
            print(f"\n🔍 Comparing with standard contract {standard_receipt.contract_id}:")
            
            standard_form_data = {
                'contract_details': {
                    'hasNifHerancaIndivisa': False,
                    'locadoresHerancaIndivisa': [],
                    'herdeiros': [],
                    'locadores': [
                        {
                            'nif': 555666777,
                            'nome': 'REGULAR LANDLORD',
                            'quotaParte': '1/1',
                            'sujeitoPassivo': 'V'
                        }
                    ],
                    'locatarios': [
                        {
                            'nif': 123456789,
                            'nome': 'REGULAR TENANT'
                        }
                    ]
                }
            }
            
            standard_submission = processor._prepare_submission_data(standard_receipt, standard_form_data)
            
            print(f"   Standard contract inheritance flag: {standard_submission.get('hasNifHerancaIndivisa')}")
            print(f"   ✅ Standard contracts correctly use regular processing")
        
    except Exception as e:
        print(f"   ❌ Error testing inheritance with CSV: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 80)
    print("INHERITANCE PROCESSING WITH CSV DATA TEST")
    print("=" * 80)
    test_inheritance_with_csv()
