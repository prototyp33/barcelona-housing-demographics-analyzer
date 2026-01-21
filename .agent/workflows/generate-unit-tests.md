---
description: Used for generating comprehensive unit tests for each data processing function
---

## Generate Unit Tests Workflow

Generate comprehensive unit tests for each data processing function:

1. **Test Structure**
   - Use pytest framework
   - Create fixtures for sample data
   - Follow AAA pattern (Arrange, Act, Assert)
   - Name tests descriptively: `test_extract_demographics_handles_missing_columns`

2. **Coverage Requirements**
   - Aim for ≥80% coverage for critical ETL code
   - Test happy path and edge cases
   - Test error handling (missing data, API failures)
   - Test data validation rules

3. **Mock External Dependencies**
   - Mock API calls with realistic responses
   - Mock database connections
   - Use `@pytest.fixture` for reusable test data

4. **Data Quality Tests**
   - Validate row counts match expectations
   - Check for null values in required fields
   - Verify data types and formats
   - Test foreign key relationships

5. **Run and Document**
   - Execute tests: `pytest tests/ -v --cov=src`
   - Generate coverage report
   - Document test scenarios in docstrings
