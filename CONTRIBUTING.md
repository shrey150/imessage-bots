# Contributing to iMessage Bot Framework

Thank you for your interest in contributing to the iMessage Bot Framework! We welcome contributions from everyone.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/imessage-bot-framework.git
   cd imessage-bot-framework
   ```

2. **Install Poetry** (if you haven't already)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Activate the virtual environment**
   ```bash
   poetry shell
   ```

## Development Workflow

### Running Tests

```bash
# Run the SDK tests
poetry run python test_sdk.py

# Run with pytest (when available)
poetry run pytest
```

### Code Formatting

We use Black for code formatting and isort for import sorting:

```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Check formatting
poetry run black --check .
```

### Type Checking

We use mypy for type checking:

```bash
poetry run mypy imessage_bot_framework/
```

### Linting

We use flake8 for linting:

```bash
poetry run flake8 imessage_bot_framework/
```

## Testing Your Changes

1. **Test the CLI tool**
   ```bash
   poetry run imessage-bot create "Test Bot" --directory /tmp
   cd "/tmp/Test Bot"
   poetry install
   ```

2. **Test the examples**
   ```bash
   poetry run python examples/echo_bot.py
   poetry run python examples/command_bot.py
   ```

3. **Run the full test suite**
   ```bash
   poetry run python test_sdk.py
   ```

## Submitting Changes

1. **Fork the repository** on GitHub

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and commit them:
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

4. **Run the tests** to ensure everything works:
   ```bash
   poetry run python test_sdk.py
   poetry run black --check .
   poetry run flake8 imessage_bot_framework/
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## Code Style Guidelines

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions small and focused
- Use descriptive variable and function names

## Areas for Contribution

### High Priority
- **Documentation**: Improve README, add more examples
- **Testing**: Add comprehensive unit tests
- **Error Handling**: Improve error messages and handling
- **Performance**: Optimize webhook processing and state management

### Medium Priority
- **Plugins**: Create plugins for common use cases (AI, databases, etc.)
- **CLI Improvements**: Add more CLI commands and options
- **Middleware**: Add built-in middleware for common patterns
- **Examples**: Create more example bots

### Low Priority
- **Web Dashboard**: Admin interface for bot management
- **Metrics**: Add built-in metrics and monitoring
- **Docker**: Official Docker images
- **CI/CD**: GitHub Actions for automated testing

## Reporting Issues

When reporting issues, please include:

1. **Environment information**:
   - Python version
   - Poetry version
   - Operating system
   - BlueBubbles version

2. **Steps to reproduce** the issue

3. **Expected behavior** vs **actual behavior**

4. **Code samples** that demonstrate the issue

5. **Error messages** or logs (if any)

## Questions?

If you have questions about contributing, feel free to:

- Open an issue on GitHub
- Start a discussion in the GitHub Discussions tab
- Reach out to the maintainers

## Code of Conduct

Please be respectful and constructive in all interactions. We want to maintain a welcoming community for everyone.

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License. 