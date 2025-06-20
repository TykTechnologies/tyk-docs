# Documentation Validation

This repository includes automated documentation validation to ensure quality and consistency.

## CI/CD Validation

### GitHub Actions
- **Trigger**: Every pull request to any branch
- **Validation**: Comprehensive documentation checks
- **Status**: Required check (blocks merge if validation fails)

### What Gets Validated
- ✅ **Broken internal links** - All internal links point to existing files
- ✅ **Missing images** - All image references point to existing files
- ✅ **Self-referencing redirects** - No redirects where source equals destination
- ✅ **Navigation-redirect conflicts** - No conflicts between navigation and redirects
- ✅ **Invalid redirects** - No redirects with empty source or destination
- ✅ **Missing navigation files** - All navigation entries point to existing files
- ✅ **Missing redirect destinations** - All redirect destinations point to existing files

## Local Validation

You can run validation locally before creating a PR:

```bash
# Full validation (recommended)
python scripts/check_broken_links.py . --validate-redirects --verbose

# Check only links
python scripts/check_broken_links.py . --links-only

# Check only images
python scripts/check_broken_links.py . --images-only

# Check only redirects and navigation
python scripts/check_broken_links.py . --validate-redirects
```

## Setting Up Branch Protection

To make validation required:

1. Go to **Settings** → **Branches** in your GitHub repository
2. Add a branch protection rule for your target branches (e.g., `main`, `deploy`)
3. Enable **"Require status checks to pass before merging"**
4. Select **"Validate Documentation / validate"** as a required check
5. Enable **"Require branches to be up to date before merging"**

## Validation Script

The `scripts/check_broken_links.py` script provides comprehensive documentation validation:

- **No external dependencies** - Uses only Python standard library
- **Fast execution** - Typically completes in under 1 minute
- **Clear reporting** - Detailed error messages with file locations
- **Exit codes** - Returns non-zero exit code if issues found (perfect for CI)

## Troubleshooting

### Common Issues

1. **Broken internal links**: Update the link path or add a redirect
2. **Missing images**: Add the image file or update the image path
3. **Navigation issues**: Ensure all navigation entries point to existing files
4. **Redirect problems**: Check redirect sources and destinations are valid

### Getting Help

If validation fails:
1. Check the GitHub Actions log for detailed error messages
2. Run validation locally to debug issues
3. Fix the reported issues and push updates to your PR
