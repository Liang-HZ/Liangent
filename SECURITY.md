# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within Liangent, please:

1. **Do NOT** open a public issue
2. Email the maintainers directly (or use GitHub's private security advisory feature)
3. Provide detailed information about the vulnerability

We take security seriously and will respond within 48 hours.

## Security Features

Liangent includes built-in security measures:

### Python Sandbox
- AST-based code validation before execution
- Restricted module imports (whitelist)
- Blocked dangerous built-in functions
- Process isolation with timeout

### Shell Sandbox
- Command whitelist enforcement
- Dangerous pattern blocking (`;`, `&`, backticks, `$(`)
- Path traversal prevention

## Best Practices for Users

1. Always run Liangent in a controlled environment
2. Review custom tools before registering them
3. Keep Liangent updated to the latest version
4. Use environment variables for sensitive API keys
