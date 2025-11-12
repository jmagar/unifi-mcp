# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in UniFi MCP Server, please report it by:

1. **Do NOT** create a public GitHub issue
2. Email the maintainers at the email listed in the repository
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We will respond to security reports within 48 hours and provide a timeline for fixes.

## Security Practices

### Authentication & Credentials

- **No hardcoded credentials**: All credentials are loaded from environment variables
- **Password protection**: Passwords are never logged or exposed in error messages
- **Session management**: Proper async context managers ensure sessions are cleaned up
- **CSRF protection**: CSRF tokens are extracted and used for UniFi OS devices

### Input Validation

- **MAC address validation**: All MAC addresses are validated against a regex pattern
- **No injection vulnerabilities**: No SQL, shell, or command execution from user input
- **Normalized inputs**: All MAC addresses are normalized to a consistent format

### SSL/TLS

- **Configurable SSL verification**: `UNIFI_VERIFY_SSL` environment variable controls certificate verification
- **Default safe for self-signed**: Defaults to `false` since most UniFi controllers use self-signed certificates
- **Production recommendation**: Enable SSL verification with valid certificates in production

### Logging

- **No sensitive data**: Passwords and tokens are never logged
- **Error sanitization**: Error messages don't leak implementation details
- **Log rotation**: ClearingFileHandler prevents unbounded log growth (10MB limit)

### Docker Security

- **Non-root user**: Container runs as unprivileged `unifi` user
- **Minimal base image**: Uses `python:3.11-slim` for smaller attack surface
- **Health checks**: Built-in health check endpoint for monitoring
- **Volume isolation**: Logs are stored in dedicated volumes

### Dependencies

- **Regular updates**: Dependencies are kept up to date
- **Version pinning**: Production dependencies use minimum version constraints
- **Vulnerability scanning**: Dependencies are checked against GitHub Advisory Database

### Network Security

- **No external dependencies**: All communication is with the local UniFi controller
- **HTTPS only**: All controller communication uses HTTPS
- **Timeout protection**: 30-second timeouts prevent hanging connections
- **Retry logic**: Automatic retry on authentication failures (401)

## Known Limitations

1. **Self-signed certificates**: Default configuration disables SSL verification for self-signed certificates commonly used by UniFi controllers
2. **Local network**: Designed for use on trusted local networks, not public internet exposure
3. **Controller authentication**: Requires local controller credentials, not UniFi Cloud SSO

## Security Updates

Security fixes are released as soon as possible after verification. Check the [CHANGELOG](CHANGELOG.md) for security-related updates.

## Dependency Vulnerabilities

### Fixed in Latest Release

- **fastmcp < 2.13.0**: Confused Deputy Account Takeover vulnerability - FIXED in 2.13.0+
  - Severity: High
  - Impact: Auth integration vulnerability
  - Resolution: Updated to `fastmcp>=2.13.0` in pyproject.toml

## Best Practices for Deployment

1. **Environment isolation**: Use Docker containers for isolation
2. **Network segmentation**: Deploy on management VLAN with firewall rules
3. **Credential rotation**: Rotate controller credentials regularly
4. **Monitoring**: Enable health checks and monitor logs for suspicious activity
5. **Updates**: Keep the server and dependencies updated
6. **SSL certificates**: Use valid SSL certificates in production when possible
7. **Access control**: Restrict network access to authorized users/systems only
8. **Backup**: Secure backup of configuration (excluding credentials)

## Security Checklist for Production

- [ ] Valid SSL certificates installed on UniFi controller
- [ ] `UNIFI_VERIFY_SSL=true` in production environment
- [ ] Strong, unique controller password
- [ ] Docker container deployed with resource limits
- [ ] Network access restricted by firewall
- [ ] Health monitoring enabled
- [ ] Log monitoring configured
- [ ] Regular dependency updates scheduled
- [ ] Backup strategy implemented
- [ ] Incident response plan documented
