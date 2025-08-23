# GitHub Actions Workflow Configuration

This directory contains the following GitHub Actions workflows:

## Workflows Overview

### 1. `pr-tests.yml` - Pull Request Testing
**Trigger**: When a PR is opened, updated, or reopened targeting `main`
**Purpose**: Run unit tests only for PRs
**Actions**:
- Run all 61 unit tests
- Comment test results on the PR
- Upload test artifacts

### 2. `ci.yml` - Continuous Integration 
**Trigger**: Push to `main` or `release/*` branches, PRs to these branches
**Purpose**: Comprehensive testing for main development
**Actions**:
- Run unit tests
- Upload test results and logs

### 3. `release.yml` - Release Automation
**Trigger**: Push to `main` branch
**Purpose**: Automated versioning and release creation
**Actions**:
- Check if version was manually changed in PR
- Auto-bump patch version if not changed
- Run unit tests
- Build Windows executable and installer
- Create release branch (`release/vX.Y.Z`)
- Create GitHub release with tag
- Upload installer and release package

### 4. `release-branch.yml` - Release Branch Management
**Trigger**: Push/PR to `release/*` branches
**Purpose**: Testing and building on release branches
**Actions**:
- Run unit tests
- Build application (on push)
- Upload build artifacts

## Version Management

The workflows automatically handle version management:

1. **Manual Version Change**: If you manually update `.version` in a PR, that version will be used
2. **Auto Patch Bump**: If no version change detected, patch version is automatically incremented
3. **Release Creation**: Each merge to main creates:
   - New release branch: `release/vX.Y.Z`
   - Git tag: `vX.Y.Z`
   - GitHub release with built artifacts

## Required Setup

### Repository Settings
1. Enable GitHub Actions in repository settings
2. Ensure `GITHUB_TOKEN` has necessary permissions:
   - Contents: write (for creating releases)
   - Pull requests: write (for commenting)
   - Actions: write (for workflow runs)

### Branch Protection (Recommended)
1. Protect `main` branch
2. Require PR reviews
3. Require status checks (unit tests) to pass
4. Require up-to-date branches

### File Requirements
- `requirements.txt` - Python dependencies
- `.version` - Current version (e.g., "1.0.0")
- `scripts/run_tests.py` - Test runner script
- `build_all.bat` - Build script for Windows

## Workflow Outputs

### On PR Creation/Update:
- Unit tests run and results posted as comment
- Test artifacts uploaded for 7 days

### On Merge to Main:
- Version auto-incremented (if not manually changed)
- Full build process (executable + installer)
- Release branch created
- GitHub release created with:
  - Windows installer (.exe)
  - Complete release package (.zip)
  - Auto-generated release notes

### On Release Branch:
- Unit tests run
- Build artifacts created and stored

## Usage Examples

### Creating a Release with Manual Version
1. Update `.version` to desired version (e.g., "2.0.0")
2. Create PR with changes
3. Merge to main → Release created with version 2.0.0

### Automatic Patch Release
1. Make any changes (no version update)
2. Create PR with changes  
3. Merge to main → Version auto-bumped (e.g., 1.0.0 → 1.0.1)

### Hotfix on Release Branch
1. Checkout release branch: `git checkout release/v1.0.0`
2. Make fixes and push
3. Tests run automatically
4. Create PR back to main when ready
