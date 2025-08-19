# Development Scripts

This directory contains development and utility scripts for the Portal das Finanças Receipts application.

## Files

### Development Tools
- **`run_app.bat`** - Run the application directly from source code (development mode)
- **`run_tests.py`** - Execute the test suite
- **`build_gui.bat`** - Launch GUI-based build tool (auto-py-to-exe)

## Usage

### Running the Application (Development)
```bash
scripts\run_app.bat
```
Runs the application directly from Python source without building.

### Running Tests
```bash
python scripts\run_tests.py
```
Executes the complete test suite.

### GUI Build Tool
```bash
scripts\build_gui.bat
```
Launches auto-py-to-exe GUI for interactive build configuration.

## Production Building

For production builds, use the main build system:
```bash
.\build_all.bat
```

This creates professional installers and distribution packages in the `releases/` directory.
