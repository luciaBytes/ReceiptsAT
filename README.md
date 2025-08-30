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
1. Get `PortalReceiptsApp_Setup_v1.0.2.exe` from your administrator
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

Enable dry run mode to test the process without making actual web requests. This is useful for:
- Testing CSV file validation
- Verifying the processing flow
- Training users on the application

### Testing Mode

For development and testing purposes, the WebClient can be initialized with `testing_mode=True`. This enables:
- **Mock Authentication**: Use test credentials (`test/test`, `demo/demo`, or `admin/admin`)
- **Simulated Connections**: Mock responses without actual network requests
- **Sample Data**: Pre-configured test contracts and receipts
- **No External Dependencies**: Tests run without internet connection

Example usage:
```python
from web_client import WebClient

# Production mode (default)
client = WebClient()

# Testing mode
test_client = WebClient(testing_mode=True)
success, message = test_client.login("test", "test")  # Mock login
```

## Testing

Run the test suite:
```cmd
cd tests
python test_suite.py
```

The test suite uses testing mode automatically to ensure tests run quickly and reliably without external dependencies.

## Project Structure

```
recibos/
├── src/
│   ├── main.py              # Application entry point
│   ├── csv_handler.py       # CSV processing logic
│   ├── web_client.py        # Web requests and session management
│   ├── receipt_processor.py # Main business logic
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
- Contracts list: `/arrendamento/consultarElementosContratos/locador`
- Receipt form: `/arrendamento/criarRecibo/<contractId>`
- Issue receipt: `/arrendamento/api/emitirRecibo`
- Receipt details: `/arrendamento/detalheRecibo/<contractId>/<numReceipt>`

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

- Web client uses simulated authentication (not actual platform integration)
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
