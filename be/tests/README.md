# Quick Reference Card

## TL;DR - Get Started in 2 Minutes

### 1. Get Token
```bash
# Register (if registration is open)
curl -X POST https://dadn.dungne.io.vn/auth/register \
  -H "Content-Type: application/json" \
  -d '{"fullName":"Integration test", "email":"test@example.com","password":"your-password"}'

# Then login
curl -X POST https://dadn.dungne.io.vn/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"your-password"}'
# Copy the `access_token` from response
```

### 2. Set Token
```bash
export TEST_AUTH_TOKEN="eyJhbGci..."
```

### 3. Run Tests
```bash
# All tests
pytest be/tests/ -v

# Alert tests only
pytest be/tests/test_alert_routes.py -v

# Prediction tests only
pytest be/tests/test_prediction_routes.py -v

# No token needed - just unauthenticated tests
pytest be/tests/ -v -k "test_no_auth"
```

---

## Common Commands

### Run All Tests
```bash
export TEST_AUTH_TOKEN="your-token"
pytest be/tests/ -v
```

### Run Specific Test File
```bash
pytest be/tests/test_alert_routes.py -v
```

### Run Specific Test Class
```bash
pytest be/tests/test_alert_routes.py::TestGetAlerts -v
```

### Run Specific Test
```bash
pytest be/tests/test_alert_routes.py::TestGetAlerts::test_no_auth_returns_401 -v
```

### Run with Detailed Output
```bash
pytest be/tests/ -vv --tb=long
```

### Run with Live Output (print statements)
```bash
pytest be/tests/ -v -s
```

### Run Tests in Parallel
```bash
pip install pytest-xdist
pytest be/tests/ -n auto -v
```

### Run Tests Against Different Backend
```bash
export TEST_BACKEND_URL="http://localhost:5000"
export TEST_AUTH_TOKEN="your-token"
pytest be/tests/ -v
```

### Stop on First Failure
```bash
pytest be/tests/ -x -v
```

### Run Only Tests Matching Pattern
```bash
pytest be/tests/ -v -k "alert"
```

### Run Tests Excluding Pattern
```bash
pytest be/tests/ -v -k "not validator"
```

---

## Test Files Overview

| File | Tests | Needs Token | Purpose |
|------|-------|-----------|---------|
| test_alert_routes.py | 16 | Some | Alert API endpoints |
| test_prediction_routes.py | 25 | Some | Prediction API endpoints |
| test_alert_service.py | 9 | Yes | Alert system behavior |
| test_ai_model_service.py | 12 | No | AI model behavior |
| test_sensor_health_service.py | 13 | No | Sensor health detection |
| test_prediction_validators.py | 12 | No | Data validation logic |

---

## Troubleshooting

### "TEST_AUTH_TOKEN not set"
```bash
export TEST_AUTH_TOKEN="your-token-here"
```

### "401 Unauthorized"
Token expired. Get a new one by logging in.

### "503 Service Unavailable"
Backend is down. Try again later or check status.

### "Connection timeout"
Backend unreachable. Check your internet connection or try:
```bash
curl https://dadn.dungne.io.vn/prediction/test-db
```

### Tests pass locally but fail in CI/CD
Make sure TEST_AUTH_TOKEN is set as a secret in your CI/CD system.

---

## Environment Variables

```bash
# Required for authenticated tests
TEST_AUTH_TOKEN=your-jwt-token

# Optional - defaults to https://dadn.dungne.io.vn
TEST_BACKEND_URL=https://dadn.dungne.io.vn
```

### Set in .env file
Create `be/.env`:
```
TEST_AUTH_TOKEN=your-token
TEST_BACKEND_URL=https://dadn.dungne.io.vn
```

Then load with python-dotenv:
```bash
pip install python-dotenv
pytest be/tests/ -v
```

---

## Tips & Tricks

### 1. Make test token available for entire session
```bash
export TEST_AUTH_TOKEN="your-token"
# Now run any pytest command without re-exporting
```

### 2. Create an alias for quick testing
```bash
alias pytest-dadn='TEST_AUTH_TOKEN="$TOKEN" pytest be/tests/ -v'
# Usage: pytest-dadn (after setting TOKEN variable)
```

### 3. View only failures
```bash
pytest be/tests/ -v --lf  # last failed
pytest be/tests/ -v --ff  # failed first
```

### 4. Generate HTML report
```bash
pip install pytest-html
pytest be/tests/ --html=report.html
# Opens in browser: open report.html
```

### 5. Measure test duration
```bash
pytest be/tests/ -v --durations=10
```

### 6. See test coverage (if coverage.py installed)
```bash
pip install pytest-cov
pytest be/tests/ --cov=app --cov-report=html
```

---

## Expected Test Results

### ✅ All Passing
```
16 passed in 5.23s
```

### ⚠️ Some Tests Skipped (Token Not Set)
```
5 passed, 11 skipped in 2.15s
```

### ❌ Failures (Check Token and Backend)
```
2 failed, 14 passed in 8.42s
```

---

## Python Installation Check

```bash
python --version  # Need Python 3.7+

# Check pytest installed
pytest --version

# Install dependencies
pip install requests pytest
```

---

## More Information

- Full guide: [INTEGRATION_TESTING.md](INTEGRATION_TESTING.md)
- Test summary: [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)
- Backend API: [../API_CONTRACT.md](../API_CONTRACT.md)
