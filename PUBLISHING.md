# Publishing to PyPI

This guide explains how to publish the mcp-server-odoo package to PyPI.

## Prerequisites

1. Create a PyPI account at https://pypi.org/account/register/
2. Generate an API token:
   - Go to https://pypi.org/manage/account/token/
   - Create a new token with "Entire account" scope
   - Save the token securely

## Building the Package

The package has already been built and is ready in the `dist/` directory:
- `mcp_server_odoo-0.1.0-py3-none-any.whl` - Wheel distribution
- `mcp_server_odoo-0.1.0.tar.gz` - Source distribution

To rebuild if needed:
```bash
source venv/bin/activate
python -m build
```

## Publishing to PyPI

### Test PyPI (Recommended First)

1. Upload to Test PyPI first:
```bash
python -m twine upload --repository testpypi dist/*
```

2. Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps mcp-server-odoo
```

### Production PyPI

1. Upload to PyPI:
```bash
python -m twine upload dist/*
```

2. Enter your PyPI username and API token when prompted
   - Username: `__token__`
   - Password: Your API token (including the `pypi-` prefix)

## Version Management

Before publishing a new version:

1. Update version in `pyproject.toml`
2. Update CHANGELOG (if you have one)
3. Clean old builds: `rm -rf dist/`
4. Build new version: `python -m build`
5. Upload: `python -m twine upload dist/*`

## Automation with GitHub Actions

You can automate publishing with GitHub Actions. Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Add your PyPI API token as a GitHub secret named `PYPI_API_TOKEN`.