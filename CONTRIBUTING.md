# Contributing to Liangent

Thank you for your interest in contributing to Liangent! 🎉

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/YOUR_USERNAME/liangent/issues)
2. If not, create a new issue using the **Bug Report** template
3. Include:
   - Python version and OS
   - Steps to reproduce
   - Expected vs actual behavior
   - Error logs (if any)

### Suggesting Features

1. Check existing [Issues](https://github.com/YOUR_USERNAME/liangent/issues) for similar suggestions
2. Create a new issue using the **Feature Request** template
3. Describe the use case and expected behavior

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `pytest tests/`
5. Commit with clear messages: `git commit -m "feat: add new feature"`
6. Push and create a Pull Request

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style (formatting, no logic change)
- `refactor:` Code refactoring
- `test:` Adding/updating tests
- `chore:` Maintenance tasks

### Code Style

- Follow PEP 8
- Use type hints where possible
- Write Google-style docstrings for public functions
- Keep functions focused and small

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/liangent.git
cd liangent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Questions?

Feel free to open an issue or start a discussion. We're happy to help!
