# 🚀 Quick Start Guide - AI Manus Testing

## 📋 Current Status

**Test Coverage**: 20.93% (Baseline)  
**Target**: >90%  
**Tests Created**: 160+ test cases  
**Status**: Infrastructure complete, tests ready to enable

---

## ⚡ Quick Commands

### Run All Tests
```bash
# Inside backend container
cd /app && bash run_comprehensive_tests.sh
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/ -v --cov=app

# Integration tests only
pytest tests/integration/ -v --cov=app

# Specific test file
pytest tests/unit/test_token_service.py -v

# With detailed output
pytest -vvv --tb=long
```

### View Coverage Report
```bash
# Generate HTML report
pytest tests/ --cov=app --cov-report=html

# Open in browser (from host)
xdg-open backend/htmlcov/index.html  # Linux
open backend/htmlcov/index.html      # macOS

# Terminal report
coverage report -m
```

### From Docker (Outside Container)
```bash
# Run tests
docker exec webapp-backend-1 bash -c "cd /app && pytest tests/ --cov=app"

# View coverage
docker exec webapp-backend-1 bash -c "cd /app && coverage report"

# Copy HTML report to host
docker cp webapp-backend-1:/app/htmlcov ./coverage-report
```

---

## 📁 Test Files Created

### Unit Tests
- ✅ `tests/unit/test_token_service.py` (49 tests)
- ✅ `tests/unit/test_auth_service.py` (35+ tests)
- ✅ `tests/unit/test_session_service.py` (30+ tests)
- ✅ `tests/unit/test_middleware.py` (20+ tests)
- ✅ `tests/unit/test_models.py` (25+ tests)

### Integration Tests
- ✅ `tests/integration/test_api_routes.py` (30+ tests)

### Configuration
- ✅ `pytest.ini` - Test configuration
- ✅ `.coveragerc` - Coverage settings
- ✅ `run_comprehensive_tests.sh` - Automated runner

### Documentation
- ✅ `TEST_COVERAGE_PLAN.md` - Strategic plan
- ✅ `TESTING_COVERAGE_REPORT.md` - Comprehensive report
- ✅ `QUICK_START_TESTING.md` - This guide

---

## 🔧 Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app.core.exceptions'`

**Solution**:
```python
# Wrong
from app.core.exceptions import UnauthorizedError

# Correct
from app.application.errors.exceptions import UnauthorizedError
```

### Async Test Failures

**Problem**: "async def functions are not natively supported"

**Solution**:
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Or add to pytest.ini
[pytest]
asyncio_mode = auto
```

### Database Connection Issues

**Solution**: Use mocked repositories
```python
@pytest.fixture
def mock_user_repository():
    repo = AsyncMock()
    repo.find_by_email = AsyncMock(return_value=None)
    return repo
```

---

## 📊 Coverage Targets

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| Services | 0% | 90% | 🔴 Critical |
| Models | 15% | 90% | 🔴 Critical |
| Middleware | 0% | 85% | 🟡 High |
| Routes/APIs | 0% | 85% | 🟡 High |
| Infrastructure | 0% | 70% | 🟠 Medium |
| **Overall** | **20.93%** | **>90%** | **🎯 Goal** |

---

## 🎯 Next Steps

### Immediate (Today)
1. Fix import issues in test files
2. Enable pytest-asyncio
3. Run unit tests successfully

### Short-term (This Week)
1. Mock external services (DB, Redis, Stripe)
2. Enable service layer tests
3. Add model tests
4. Target: 50% coverage

### Long-term (This Month)
1. Complete infrastructure testing
2. Add E2E tests
3. CI/CD integration
4. Target: >90% coverage

---

## 💡 Pro Tips

### Writing Tests

```python
# Good: Test specific behavior
def test_user_login_with_valid_credentials():
    # Arrange
    user = create_test_user()
    # Act
    result = auth_service.login(user.email, "correct_password")
    # Assert
    assert result.success is True

# Good: Use descriptive names
def test_billing_middleware_blocks_when_subscription_expired():
    # ...

# Good: Mock external dependencies
@patch('app.external.stripe.client')
def test_payment_processing(mock_stripe):
    mock_stripe.charge.return_value = {"status": "success"}
    # ...
```

### Coverage Best Practices

1. **Focus on critical paths first**
   - Authentication
   - Payment processing
   - Data validation

2. **Test edge cases**
   - Empty inputs
   - Invalid data
   - Boundary conditions

3. **Mock external services**
   - Database calls
   - API requests
   - File operations

4. **Use fixtures**
   - Reuse test data
   - Setup/teardown
   - Isolate tests

---

## 📚 Resources

### Internal Documentation
- `TEST_COVERAGE_PLAN.md` - Detailed strategy
- `TESTING_COVERAGE_REPORT.md` - Full analysis
- `htmlcov/index.html` - Visual coverage report

### Pytest Resources
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Guide](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

### Example Tests
Look at existing tests for patterns:
- `tests/unit/test_webdev_tools.py` - Good examples
- `tests/unit/test_mcp_integration.py` - Async patterns
- `tests/conftest.py` - Fixtures

---

## 🔍 Quick Diagnostics

### Check Test Discovery
```bash
pytest --collect-only
```

### Run Failed Tests Only
```bash
pytest --lf  # Last failed
pytest --ff  # Failed first
```

### Debug Mode
```bash
pytest -vv --tb=long --capture=no
```

### Coverage by Module
```bash
coverage report --include="app/application/*"
coverage report --include="app/domain/models/*"
```

---

## ✅ Success Criteria

- [ ] All tests pass (0 failures)
- [ ] Coverage >90% overall
- [ ] All critical modules >85%
- [ ] No blocking import errors
- [ ] Documentation updated
- [ ] CI/CD pipeline includes tests

---

## 📞 Support

**Issues with tests?**
1. Check `TESTING_COVERAGE_REPORT.md` for known issues
2. Review existing test patterns in `tests/unit/`
3. Ensure all dependencies installed (`pytest`, `pytest-cov`, `pytest-asyncio`)

**Coverage questions?**
1. Run `coverage report -m` for missing lines
2. Check `htmlcov/index.html` for visual analysis
3. Review `TEST_COVERAGE_PLAN.md` for strategy

---

**Last Updated**: 2025-12-26  
**Version**: 1.0  
**Maintainer**: AI Manus Team
