# Tests Troubleshooting Guide

## Issue: Pytest Blocks or Hangs

If pytest appears to be blocking or hanging, try the following solutions:

### Solution 1: Run with Verbose Output and Timeout
```bash
# Install pytest-timeout for automatic timeout
pip install pytest-timeout

# Run with timeout (kills test after 30 seconds)
pytest tests/ -v --timeout=30
```

### Solution 2: Run Tests One at a Time
```bash
# Run each test file separately
pytest tests/test_categories.py -v
pytest tests/test_products.py -v
pytest tests/test_stock.py -v

# Or run a specific test
pytest tests/test_categories.py::test_create_category -v
```

### Solution 3: Clear Cache and Reinstall
```bash
# Remove pytest cache
rm -rf .pytest_cache __pycache__ tests/__pycache__

# Remove and recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v
```

### Solution 4: Check for Background Processes
```bash
# Make sure no other instances are running
ps aux | grep pytest
ps aux | grep uvicorn

# Kill any hanging processes
pkill -f pytest
pkill -f uvicorn
```

### Solution 5: Use -x Flag to Stop on First Failure
```bash
# This is already in pytest.ini, but you can also use it explicitly
pytest tests/ -v -x --tb=short
```

### Solution 6: Disable Asyncio if Causing Issues
```bash
# Run with asyncio disabled temporarily
pytest tests/ -v --asyncio-mode=strict
```

### Solution 7: Check Database Connections
The tests use SQLite in-memory database. If you're having issues:

```bash
# Ensure no PostgreSQL connections are active
# The TESTING flag should prevent this, but verify:
export TESTING=true
pytest tests/ -v
```

### Solution 8: Run in Subprocess with Timeout
```bash
# Use timeout command (Linux/macOS)
timeout 30 pytest tests/ -v

# Or on Windows (PowerShell)
Start-Process pytest -ArgumentList "tests/ -v" -Wait -NoNewWindow -TimeoutSec 30
```

### Common Issues

#### Issue: Tests hang at collection
**Cause**: Import errors or circular dependencies
**Solution**: Run with collection only
```bash
pytest tests/ --collect-only
```

#### Issue: Tests hang during execution
**Cause**: Waiting for database or network connection
**Solution**: Verify TESTING flag is set
```python
# In conftest.py, this should be present:
settings.TESTING = True
os.environ["TESTING"] = "true"
```

#### Issue: Ctrl+C doesn't stop pytest
**Cause**: Signal handling issue
**Solution**: Use SIGKILL
```bash
# Find the process
ps aux | grep pytest

# Kill with SIGKILL
kill -9 <PID>
```

### Debugging Hanging Tests

Add print statements to see where it hangs:

```python
# In conftest.py
print("Starting test setup...")

@pytest.fixture(scope="function")
def db_session():
    print("Creating database session...")
    Base.metadata.create_all(bind=engine)
    print("Database created")
    # ... rest of fixture
```

Or use pytest's live logging:

```bash
pytest tests/ -v --log-cli-level=DEBUG
```

### Expected Test Output

When tests run successfully, you should see:
```
18 passed in ~0.4s
```

All 18 tests should complete in less than 1 second on most systems.

### Environment Variables

Make sure these are set correctly:
- `TESTING=true` (set automatically by conftest.py)
- No `DATABASE_URL` pointing to real PostgreSQL (should use SQLite for tests)
- No `RABBITMQ_URL` (should be skipped during tests)

### Getting Help

If tests continue to hang:
1. Check the last test that was running before hang
2. Run that specific test in isolation
3. Check system resources (RAM, CPU)
4. Verify all dependencies are correctly installed
5. Try running on a different Python version (3.11 recommended)
