# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.16] - 2024-12-24

### Added
- Initial public release
- Python sandbox with AST-based security validation
- Shell sandbox with whitelist/blacklist control
- `@tool` decorator for custom tool registration
- Native Function Calling support for compatible models
- Prompt-based fallback mode for any LLM
- SQLite persistent storage for sessions and logs
- `min_tool_use` / `max_tool_use` constraints
- CLI commands: `liangent init`, `liangent chat`, `liangent start`
- Serverless handler for Aliyun Function Compute
- Multi-language README (English & Chinese)

### Fixed
- Cross-platform subprocess execution for Python sandbox (Windows, macOS, Linux)

### Security
- Process isolation with timeout protection
- Blacklisted dangerous built-in functions
- Shell command whitelist enforcement

[Unreleased]: https://github.com/YOUR_USERNAME/liangent/compare/v0.0.16...HEAD
[0.0.16]: https://github.com/YOUR_USERNAME/liangent/releases/tag/v0.0.16
