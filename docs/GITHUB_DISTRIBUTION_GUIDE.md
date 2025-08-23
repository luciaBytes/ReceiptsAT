# GitHub Distribution Guide

This guide covers how to set up your repository for professional distribution on GitHub, including releases, documentation, and automation.

## Repository Setup

### 1. Repository Structure
Your repository should be organized as follows:
```
portal-receipts-app/
├── .github/
│   ├── workflows/
│   │   ├── build-release.yml      # Automated builds
│   │   └── test.yml               # CI testing
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── pull_request_template.md
├── assets/                        # Icons, screenshots, etc.
├── build/                        # Build scripts and configuration
├── docs/                         # Documentation
├── releases/                     # Generated installers
├── src/                          # Source code
├── tests/                        # Test files
├── .gitignore
├── LICENSE
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── requirements.txt
```

### 2. Essential Files

#### .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Windows
Thumbs.db
Desktop.ini

# Build artifacts
build/dist/
build/build/
*.spec
releases/*.exe

# Logs
logs/
*.log

# Credentials
credentials
.env

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
```

## GitHub Actions Workflow

### Automated Build and Release
Create `.github/workflows/build-release.yml`:

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'
  release:
    types: [created]

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Install Inno Setup
      run: |
        choco install innosetup
    
    - name: Build application
      run: |
        ./build_all.bat
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: windows-installer
        path: releases/*.exe
    
    - name: Release
      uses: softprops/action-gh-release@v1
      if: startsWith(github.ref, 'refs/tags/')
      with:
        files: releases/*.exe
        name: Portal das Finanças Receipts ${{ github.ref_name }}
        body: |
          ## Changes
          See CHANGELOG.md for detailed changes.
          
          ## Installation
          1. Download the installer below
          2. Run as administrator
          3. Follow the setup wizard
          
          ## System Requirements
          - Windows 10/11 (64-bit)
          - No additional dependencies required
        draft: false
        prerelease: false
```

### Continuous Integration
Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
```

## Release Management

### 1. Version Management
Update version in these files:
- `build/version_info.txt`
- `build/installer_script.iss`
- `build/receipts_app.spec`
- `docs/CHANGELOG.md`

### 2. Creating Releases

#### Manual Release Process
1. Update version numbers in all files
2. Update CHANGELOG.md with new features/fixes
3. Test the application thoroughly
4. Run full build: `build_all.bat`
5. Test the installer
6. Create Git tag: `git tag v1.0.0`
7. Push tag: `git push origin v1.0.0`
8. Create GitHub release with installer

#### Automated Release Process
1. Update version numbers
2. Update CHANGELOG.md
3. Commit changes
4. Create and push tag
5. GitHub Actions will automatically build and release

### 3. Release Templates

#### GitHub Release Template
```markdown
## Portal das Finanças Receipts v1.0.0

### New Features
- Feature 1 description
- Feature 2 description

### Bug Fixes
- Fix 1 description
- Fix 2 description

### Improvements
- Improvement 1 description
- Improvement 2 description

### Installation
1. Download `PortalReceiptsApp_Setup_v1.0.0.exe` below
2. Run the installer as administrator
3. Follow the setup wizard
4. Launch from Start Menu or desktop shortcut

### System Requirements
- Windows 10 or Windows 11 (64-bit)
- Internet connection for portal access
- 50MB free disk space

### Support
For issues or questions:
- Create an issue on GitHub
- Check the documentation in the repository
- Email: support@example.com

### Checksums
- SHA256: `[auto-generated]`
```

## Documentation Strategy

### 1. README.md Enhancement
```markdown
# Portal das Finanças Receipts

[![Build Status](https://github.com/username/portal-receipts/workflows/Tests/badge.svg)](https://github.com/username/portal-receipts/actions)
[![Downloads](https://img.shields.io/github/downloads/username/portal-receipts/total.svg)](https://github.com/username/portal-receipts/releases)
[![Latest Release](https://img.shields.io/github/release/username/portal-receipts.svg)](https://github.com/username/portal-receipts/releases/latest)

Automated rent receipt issuance through Portuguese Tax Authority portal.

## Features
- Automated login and navigation
- Batch receipt generation
- CSV export of receipts
- Multi-language support (Portuguese/English)
- Professional Windows installer

## Quick Start
1. Download the latest installer from [Releases](https://github.com/username/portal-receipts/releases)
2. Run the installer as administrator
3. Launch the application
4. Configure your portal credentials
5. Start generating receipts

## Documentation
- [Installation Guide](docs/USER_INSTALLATION_GUIDE.md)
- [Build Guide](docs/BUILD_GUIDE.md)
- [Distribution Guide](docs/DISTRIBUTION_GUIDE.md)
- [Changelog](CHANGELOG.md)

## Support
- [Issue Tracker](https://github.com/username/portal-receipts/issues)
- [Discussions](https://github.com/username/portal-receipts/discussions)
- [Wiki](https://github.com/username/portal-receipts/wiki)
```

### 2. Contributing Guidelines
Create `CONTRIBUTING.md`:

```markdown
# Contributing to Portal das Finanças Receipts

## Development Setup
1. Clone the repository
2. Install Python 3.13+
3. Install dependencies: `pip install -r requirements.txt`
4. Install development tools: `pip install pytest black flake8`

## Testing
- Run tests: `pytest tests/`
- Run with coverage: `pytest tests/ --cov=src`
- Format code: `black src/ tests/`
- Lint code: `flake8 src/ tests/`

## Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass
6. Submit a pull request

## Code Style
- Follow PEP 8
- Use Black for formatting
- Add type hints where possible
- Write descriptive commit messages
```

## Marketing and Visibility

### 1. Repository Topics
Add these topics to your GitHub repository:
- `python`
- `tkinter`
- `windows-application`
- `automation`
- `taxes`
- `portugal`
- `receipts`
- `desktop-app`

### 2. Social Proof
- Add badges for build status, downloads, version
- Include screenshots in README
- Write detailed release notes
- Respond to issues promptly
- Engage with the community

### 3. SEO Optimization
- Use descriptive repository name
- Write clear, keyword-rich description
- Include relevant topics/tags
- Maintain active contribution graph
- Link to related projects

## Security Considerations

### 1. Sensitive Data
- Never commit credentials
- Use environment variables for secrets
- Add comprehensive .gitignore
- Regular security audits

### 2. Code Signing (Optional)
For professional distribution:
1. Obtain code signing certificate
2. Sign the executable before creating installer
3. Sign the installer itself
4. Include certificate information in releases

## Next Steps

1. **Set up repository structure**: Create directories and essential files
2. **Configure GitHub Actions**: Set up automated builds and testing
3. **Create initial release**: Tag v1.0.0 and create first release
4. **Add documentation**: Complete README, guides, and wiki
5. **Community engagement**: Enable discussions, create templates
6. **Marketing**: Share on relevant platforms and communities

This comprehensive GitHub distribution strategy will help you create a professional, maintainable, and discoverable open-source project.
```
