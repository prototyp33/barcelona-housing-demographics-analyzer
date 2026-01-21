---
description: Orchestrates the end-to-end integration of a new data provider (e.g., IDESCAT) into the existing ETL pipeline.
---

## Add New Data Source Workflow

Follow these steps to integrate a new data source into the ETL pipeline:

1. **Create Extractor Class**
   - Create `src/extraction/{source_name}.py`
   - Inherit from BaseExtractor
   - Implement `extract()` method with proper error handling
   - Add rate limiting and retry logic
   - Register extracted data in manifest.json

2. **Add Unit Tests**
   - Create `tests/test_{source_name}.py`
   - Mock API responses
   - Test data normalization
   - Test error handling scenarios
   - Verify manifest registration

3. **Update ETL Pipeline**
   - Modify `src/processing.py` to process new data type
   - Add data validation functions
   - Implement territory mapping if needed
   - Handle duplicate records appropriately

4. **Create QA Notebook**
   - Create `notebooks/{source_name}_qa.ipynb`
   - Visualize temporal coverage
   - Check data distribution and outliers
   - Verify mapping to dim_barrios
   - Document data quality metrics

5. **Update Documentation**
   - Add source details to `docs/sources/{source_name}.md`
   - Document API endpoints and parameters
   - Note any rate limits or authentication requirements
   - Include example usage

6. **Run Validation**
   - Execute full ETL pipeline: `python scripts/process_and_load.py`
   - Verify data loaded correctly with ≥95% completeness
   - Check foreign key integrity
   - Run full test suite: `pytest tests/ -v`
