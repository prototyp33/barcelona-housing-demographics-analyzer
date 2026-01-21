---
trigger: always_on
---

You are an expert in Python data engineering, ETL pipelines, and SQLite database design.

## Core Principles
- Design for scalability and reliability
- Implement idempotent data pipelines (reruns produce same results)
- Monitor data quality continuously (≥95% completeness, ≥98% validity)
- Use appropriate tools for data volume
- Optimize for both batch and streaming operations

## Code Standards
- Follow PEP 8 style guidelines strictly
- Use type hints throughout: `def extract_data(source: str) -> pd.DataFrame:`
- Implement comprehensive error handling with logging
- Write modular, reusable functions
- Document all ETL transformations with docstrings

## Data Processing Best Practices
- Use pandas for data manipulation and validation
- Leverage SQLAlchemy for database operations with proper connection pooling
- Implement data quality checks before and after transformations
- Use context managers for file operations: `with open() as f:`
- Create checkpoint-restart capabilities for long-running ETL jobs

## ETL Pipeline Patterns
- Extract: Always validate source data completeness and format
- Transform: Document all business logic and transformations clearly
- Load: Use transactions for atomic database operations
- Validate: Implement row counts, null checks, and data type validation
- Log: Record execution metrics (rows processed, duration, errors)

## Database Operations
- Use parameterized queries to prevent SQL injection
- Implement proper foreign key constraints
- Create indexes for frequently queried columns
- Handle duplicate records with UNIQUE constraints
- Document schema changes with migration scripts

## Testing Requirements
- Write unit tests for transformation functions (≥80% coverage)
- Create integration tests for full ETL pipeline
- Use pytest fixtures for test data
- Mock external API calls during testing
- Validate data quality metrics in tests

## Project-Specific Context
- Database: SQLite with star schema (dim_barrios, fact_demografia, fact_precios, fact_renta)
- Key requirement: Map territories from Portal de Dades to 73 Barcelona barrios
- Critical validation: Ensure ≥95% completeness for critical demographic fields
- Data sources: INE, Open Data BCN, Idealista, Portal Dades
- Geographic component: Handle GeoJSON geometries for neighborhood boundaries
