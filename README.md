# Receipts Processor

A Windows application for automating the issuance of rent receipts for multiple tenants by interacting with the Portuguese Tax Authority platform via Autenticação.Gov.

## Features

- **Autenticação.Gov Integration**: Connects to the official Portuguese government authentication system
- **CSV Processing**: Load and validate receipt data from CSV files
- **Secure Authentication**: Uses Autenticação.Gov for secure government service access
- **Dual Processing Modes**: Bulk processing or step-by-step with user confirmation
- **Dry Run Mode**: Test the process without making actual requests
- **GUI Interface**: User-friendly Windows application
- **Comprehensive Logging**: Detailed logging and error reporting
- **Report Generation**: Export processing results to CSV

## Requirements

- Python 3.8 or higher
- Windows OS
- Valid Autenticação.Gov account (Portuguese government digital identity)
- Dependencies listed in `requirements.txt`

## Installation

### For End Users (Recommended)
Download and run the Windows installer:
1. Get `PortalReceiptsApp_Setup_v1.1.7.exe` from your administrator
2. Run the installer and follow the wizard
3. Launch from Start Menu → Portal das Finanças Receipts
4. No Python installation required!

See `USER_INSTALLATION_GUIDE.md` for detailed instructions.

### For Developers
1. Clone or download the project
2. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

## Building the Executable

### Quick Build
```cmd
# Complete build process (executable + installer)
build_complete.bat
```

### Manual Build
```cmd
# Build the executable only
build_app.bat

# Create Windows installer
build_installer.bat
```

For detailed build instructions, see `BUILD_GUIDE.md`.

## Usage

### Running the Application

```cmd
cd src
python main.py
```

### Authentication

Use your Autenticação.Gov credentials:
- **Username**: Citizen Card number, email address, or NIF (Tax ID)
- **Password**: Your Autenticação.Gov password

**Important**: This application connects to the official Portuguese government authentication system (https://www.acesso.gov.pt/v2/login). Your credentials are transmitted securely using HTTPS.

### CSV File Format

The CSV file should contain the following columns:
- `contractId`: Contract identifier
- `fromDate`: Start date (YYYY-MM-DD format)
- `toDate`: End date (YYYY-MM-DD format)
- `receiptType`: Type of receipt (e.g., "rent")
- `value`: Receipt value (numeric)

Example:
```csv
contractId,fromDate,toDate,receiptType,value
123456,2024-01-01,2024-01-31,rent,100.00
789012,2024-02-01,2024-02-29,rent,
```

### Processing Modes

1. **Bulk Mode**: Processes all receipts automatically
2. **Step-by-Step Mode**: Shows each receipt for user confirmation before processing

### Dry Run Mode

Enable dry run mode to test the process without making actual receipt submissions. This is useful for:
- Testing CSV file validation
- Verifying the processing flow  
- Training users on the application
- Getting real contract data for testing purposes

Dry run mode uses real API calls to retrieve contract information and rent values, but blocks the actual receipt submission step.

## Testing

Run the test suite:
```cmd
cd tests
python test_suite.py
```

The test suite includes comprehensive testing of:
- Authentication workflows
- CSV processing and validation
- Receipt processing logic
- GUI functionality
- Error handling
- Dry run capabilities

## Project Structure

```
recibos/
├── src/
│   ├── main.py              # Application entry point
│   ├── csv_handler.py       # CSV processing logic
│   ├── web_client.py        # Web requests and session management
│   ├── receipt_processor.py # Main business logic with dry run support
│   ├── gui/
│   │   ├── main_window.py   # GUI implementation
│   │   └── __init__.py
│   └── utils/
│       ├── logger.py        # Logging utilities
│       └── __init__.py
├── tests/
│   └── test_suite.py        # Test cases
├── logs/                    # Log files (created at runtime)
├── sample/
│   └── sample_receipts.csv  # Sample CSV data
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration

The application uses the following endpoints (configured in `web_client.py`):
- Base URL: `https://imoveis.portaldasfinancas.gov.pt`
- **Authentication**: `https://www.acesso.gov.pt/v2/loginForm?partID=SICI&path=/arrendamento/consultarElementosContratos/locador`
- **Primary Contracts API**: `/arrendamento/api/obterElementosContratosEmissaoRecibos/locador` (JSON with `valorRenda`)
  - **Parameters**: `?contractId={contract_id}` (optional - when omitted, returns all contracts)
- **Fallback Contracts List**: `/arrendamento/consultarElementosContratos/locador` (HTML parsing)
- **Receipt Form**: `/arrendamento/criarRecibo/<contractId>` (GET - loads form with contract details)
- **Issue Receipt**: `/arrendamento/api/emitirRecibo` (POST - submits receipt data)
- **Receipt Details**: `/arrendamento/detalheRecibo/<contractId>/<numReceipt>` (GET - retrieves issued receipt details)

**Endpoint Details:**
- **Authentication endpoint**: Redirects to Autenticação.Gov with proper partID and return path
- **Primary contracts API**: Returns JSON data including `valorRenda` (rent amount) used for value defaulting
- **Fallback contracts list**: Provides HTML that requires parsing when the API fails
- **Receipt form endpoint**: Loads the receipt creation form with contract details and embedded JavaScript data
- **Issue receipt endpoint**: POST endpoint that accepts receipt data and creates the receipt
- **Receipt details endpoint**: Retrieves details of issued receipts including PDF links (future implementation)
- All endpoints require proper authentication via Autenticação.Gov session

## Logging

The application creates detailed logs in the `logs/` directory with:
- Authentication attempts and results
- CSV validation results
- Processing progress and results
- Error messages and stack traces

## Security Notes

- This version does NOT implement the security features specified in the requirements
- Credentials are handled in memory only
- Session management is basic
- For production use, implement proper credential storage and session security

## Known Limitations

- Step-by-step mode auto-confirms all receipts (GUI confirmation dialog not implemented)
- No actual PDF download functionality

## Distribution

This application includes:
- **Professional Windows installer** - No Python required for end users
- **Complete documentation** - Build guides and user instructions
- **Automated build scripts** - Easy executable creation process

See `DISTRIBUTION_GUIDE.md` for deployment options.

## Development

To extend or modify the application:

1. **Adding new validation rules**: Modify `csv_handler.py`
2. **Changing web requests**: Update `web_client.py`
3. **Modifying processing logic**: Edit `receipt_processor.py`
4. **GUI changes**: Update `gui/main_window.py`
5. **Adding tests**: Extend `tests/test_suite.py`

## Support

For issues or questions, check the log files in the `logs/` directory for detailed error information.
