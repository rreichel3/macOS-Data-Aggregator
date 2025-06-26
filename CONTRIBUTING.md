# Contributing to SDEF Aggregator

Thank you for your interest in contributing to the SDEF Aggregator project!

## How to Contribute

### Reporting Issues

If you encounter any issues or have suggestions for improvements:

1. Check existing [Issues](../../issues) to see if it's already reported
2. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - macOS version and system details
   - Any relevant error messages

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test your changes on macOS
5. Commit with clear messages
6. Push to your fork
7. Create a Pull Request

### Development Guidelines

- **Python Code**: Follow PEP 8 style guidelines
- **Shell Scripts**: Use shellcheck for validation
- **Documentation**: Update README.md for any functional changes
- **Testing**: Test on multiple macOS versions if possible

### Areas for Contribution

- **Platform Support**: Extending to other Unix-like systems
- **Performance**: Optimizing file discovery and processing
- **Features**: Adding new output formats or filtering options
- **Documentation**: Improving guides and examples
- **CI/CD**: Enhancing GitHub Actions workflows

### Testing

Before submitting changes:

1. Test the Python script: `sudo python3 collect_sdef_files.py`
2. Test the shell script: `sudo ./collect_sdef_files.sh`
3. Verify file organization and naming
4. Check that README instructions are accurate

### Code Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your changes will be merged
4. Your contribution will be acknowledged in releases

## Questions?

Feel free to open an issue for any questions about contributing!
