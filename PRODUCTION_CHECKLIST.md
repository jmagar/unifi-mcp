# Production Readiness Checklist

This checklist ensures the UniFi MCP Server is properly configured and secured for production deployment.

## ✅ Pre-Deployment Checklist

### Environment Configuration

- [ ] **Environment Variables Set**
  - [ ] `UNIFI_CONTROLLER_URL` - Full URL with port (https://IP:443 or https://IP:8443)
  - [ ] `UNIFI_USERNAME` - Local admin account (not UniFi Cloud)
  - [ ] `UNIFI_PASSWORD` - Strong, unique password
  - [ ] `UNIFI_VERIFY_SSL` - Set to `true` for production with valid certs
  - [ ] `UNIFI_IS_UDM_PRO` - Set appropriately for your controller type

- [ ] **Server Configuration**
  - [ ] `UNIFI_LOCAL_MCP_HOST` - Set to appropriate bind address (0.0.0.0 or specific IP)
  - [ ] `UNIFI_LOCAL_MCP_PORT` - Port number (default 8001)
  - [ ] `UNIFI_LOCAL_MCP_LOG_LEVEL` - Set to INFO or WARNING for production
  - [ ] Log file paths configured appropriately

### Security

- [ ] **SSL/TLS Configuration**
  - [ ] Valid SSL certificates installed on UniFi controller (if using SSL verification)
  - [ ] `UNIFI_VERIFY_SSL=true` enabled for production
  - [ ] Self-signed certificates removed (or properly validated)

- [ ] **Credentials Management**
  - [ ] Strong, unique password for controller account
  - [ ] Password rotation policy established
  - [ ] `.env` file is NOT committed to git (verify with `git status`)
  - [ ] Environment variables stored securely (not in code)
  - [ ] MFA enabled on UniFi controller (if supported)

- [ ] **Network Security**
  - [ ] Firewall rules restrict access to authorized IPs/networks
  - [ ] Server deployed on management VLAN
  - [ ] Network segmentation in place
  - [ ] No public internet exposure (unless explicitly required and secured)

- [ ] **Container Security** (if using Docker)
  - [ ] Running as non-root user (verified in Dockerfile)
  - [ ] Resource limits configured (memory, CPU)
  - [ ] Security scanning performed on container image
  - [ ] Latest base image used (`python:3.11-slim`)

### Code Quality

- [ ] **Linting & Type Checking**
  - [ ] `ruff check .` passes with no errors
  - [ ] `mypy unifi_mcp` shows no critical issues
  - [ ] All tests pass: `pytest`

- [ ] **Dependencies**
  - [ ] All dependencies up to date
  - [ ] No known security vulnerabilities (checked with `gh-advisory-database`)
  - [ ] `fastmcp>=2.13.0` (fixes critical CVE)

### Monitoring & Logging

- [ ] **Logging**
  - [ ] Log level set appropriately (INFO or WARNING)
  - [ ] Log rotation configured (ClearingFileHandler with 10MB limit)
  - [ ] Logs monitored for errors and security events
  - [ ] Centralized logging configured (if applicable)

- [ ] **Health Checks**
  - [ ] Health endpoint accessible: `http://localhost:8001/health`
  - [ ] Monitoring system configured to check health
  - [ ] Alerts configured for service failures
  - [ ] Response time monitoring enabled

- [ ] **Metrics**
  - [ ] Application metrics collected (if applicable)
  - [ ] Performance baselines established
  - [ ] Resource utilization monitored (CPU, memory, network)

### Backup & Recovery

- [ ] **Configuration Backup**
  - [ ] `.env` file backed up securely (encrypted)
  - [ ] Configuration documented
  - [ ] Recovery procedures documented
  - [ ] Backup restoration tested

- [ ] **Disaster Recovery**
  - [ ] Recovery time objective (RTO) defined
  - [ ] Recovery point objective (RPO) defined
  - [ ] Disaster recovery plan documented
  - [ ] DR plan tested

### Testing

- [ ] **Functional Testing**
  - [ ] All tools tested in staging environment
  - [ ] Device operations verified
  - [ ] Client operations verified
  - [ ] Network configuration access verified
  - [ ] Monitoring and statistics verified

- [ ] **Integration Testing**
  - [ ] UniFi controller connectivity verified
  - [ ] Authentication tested
  - [ ] Error handling tested
  - [ ] Timeout behavior verified
  - [ ] Retry logic tested

- [ ] **Load Testing**
  - [ ] Expected load tested
  - [ ] Performance metrics acceptable
  - [ ] Resource usage within limits
  - [ ] No memory leaks observed

### Documentation

- [ ] **Deployment Documentation**
  - [ ] Installation steps documented
  - [ ] Configuration guide available
  - [ ] Troubleshooting guide created
  - [ ] Known issues documented

- [ ] **Operations Documentation**
  - [ ] Monitoring procedures documented
  - [ ] Maintenance procedures documented
  - [ ] Incident response plan created
  - [ ] Escalation paths defined

- [ ] **Security Documentation**
  - [ ] Security policy reviewed (SECURITY.md)
  - [ ] Security best practices documented
  - [ ] Vulnerability response procedures defined
  - [ ] Security contacts listed

## 🚀 Deployment Steps

### 1. Verify Environment

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Install dependencies
pip install -e .

# Run linters
ruff check .
mypy unifi_mcp

# Run tests
pytest
```

### 2. Configure Application

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env  # or your preferred editor

# Verify configuration is not tracked
git status | grep .env  # Should show nothing
```

### 3. Test Connectivity

```bash
# Test UniFi controller connection
curl -k https://YOUR_CONTROLLER_IP:443/

# Start server in test mode
python3 -m unifi_mcp.main

# Test health endpoint
curl http://localhost:8001/health
```

### 4. Deploy

#### Option A: Direct Python

```bash
# Start server
./run.sh

# Verify running
curl http://localhost:8001/health

# Check logs
./run.sh logs
```

#### Option B: Docker

```bash
# Build image
docker build -t unifi-mcp:latest .

# Run container
docker-compose up -d

# Verify running
docker-compose ps
docker logs unifi-mcp

# Check health
curl http://localhost:8001/health
```

### 5. Post-Deployment Verification

```bash
# Verify service is running
curl http://localhost:8001/health

# Test a simple operation
curl -X POST http://localhost:8001/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "get_sites"}}'

# Monitor logs for errors
tail -f /path/to/logs/unifi-mcp.log
```

## 🔧 Post-Deployment

### Monitoring

- [ ] Health checks passing
- [ ] No errors in logs
- [ ] Resource usage normal
- [ ] Response times acceptable

### Security Audit

- [ ] Review access logs
- [ ] Verify no unauthorized access
- [ ] Check for suspicious activity
- [ ] Validate security controls

### Documentation Update

- [ ] Document actual deployment configuration
- [ ] Update runbooks with any deviations
- [ ] Document any issues encountered
- [ ] Share deployment notes with team

## 📋 Ongoing Maintenance

### Daily
- Monitor health checks
- Review error logs
- Check resource usage

### Weekly
- Review security logs
- Verify backup completion
- Check for dependency updates

### Monthly
- Security audit
- Performance review
- Documentation review
- Disaster recovery drill

### Quarterly
- Full security assessment
- Load testing
- Configuration review
- Update dependencies

## ⚠️ Known Limitations

1. **Self-Signed Certificates**: Default configuration disables SSL verification for self-signed certificates
2. **Local Network Only**: Designed for trusted local networks, not public internet
3. **Controller Authentication**: Requires local controller credentials, not UniFi Cloud SSO
4. **Test Failures**: Some formatter tests have timezone dependencies (non-blocking)

## 🆘 Troubleshooting

### Common Issues

**Issue**: Authentication fails
- **Solution**: Verify credentials, check controller URL, ensure controller is accessible

**Issue**: SSL verification errors
- **Solution**: Set `UNIFI_VERIFY_SSL=false` for self-signed certs, or install valid certs

**Issue**: Connection timeouts
- **Solution**: Check network connectivity, verify firewall rules, increase timeout

**Issue**: No data returned
- **Solution**: Verify site name is correct, check controller permissions, review logs

## 📞 Support

- Review [README.md](README.md) for usage documentation
- Check [SECURITY.md](SECURITY.md) for security best practices
- See [CHANGELOG.md](CHANGELOG.md) for recent changes
- Report issues on GitHub: https://github.com/jmagar/unifi-mcp/issues

---

**Production Ready**: ✅ Complete this checklist before deploying to production.
