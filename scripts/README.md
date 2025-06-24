# Scripts

This directory contains utility scripts for documentation maintenance and validation.

## validate_mintlify_docs.py

Comprehensive documentation validation script that checks for:

- **Broken internal links** - Links pointing to non-existent files
- **Missing images** - Image references pointing to non-existent files
- **Self-referencing redirects** - Redirects where source equals destination
- **Navigation-redirect conflicts** - Conflicts between navigation and redirects
- **Invalid redirects** - Redirects with empty source or destination
- **Missing navigation files** - Navigation entries pointing to non-existent files
- **Missing redirect destinations** - Redirect destinations pointing to non-existent files

### Usage

```bash
# Full validation (recommended)
python scripts/validate_mintlify_docs.py . --validate-redirects --verbose

# Check only links
python scripts/validate_mintlify_docs.py . --links-only

# Check only images
python scripts/validate_mintlify_docs.py . --images-only

# Check only redirects and navigation
python scripts/validate_mintlify_docs.py . --validate-redirects
```

### CI Integration

This script is automatically run by GitHub Actions on every pull request to ensure documentation quality.

## merge_docs_configs.py

Script for merging multiple documentation configurations, typically used for handling different versions or branches of documentation.

### Usage

```bash
python scripts/merge_docs_configs.py [options]
```

### Dependencies

Both scripts require:
- Python 3.7+
- No external dependencies (uses only Python standard library)
