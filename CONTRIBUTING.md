# Contributing to SnapServe

Thank you for your interest in contributing to SnapServe! 🎉

## Development Setup

```bash
# Clone the repository
git clone https://github.com/gitstq/SnapServe.git
cd SnapServe

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies with dev extras
pip install -e ".[dev]"

# Install browser
snapserve --install-browser

# Run tests
pytest tests/ -v

# Start development server (with auto-reload)
snapserve --debug
```

## Commit Convention

We follow the [Angular Commit Convention](https://conventionalcommits.org/):

| Type | Description |
|------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation update |
| `refactor:` | Code refactoring |
| `test:` | Test addition/modification |
| `chore:` | Build/tooling changes |
| `perf:` | Performance improvement |

## Pull Request Process

1. Ensure all tests pass (`pytest tests/ -v`)
2. Update documentation if needed
3. Keep PRs focused on a single concern
4. Write descriptive PR title and description

## Issue Reporting

When reporting issues, please include:
- SnapServe version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error logs (if any)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
