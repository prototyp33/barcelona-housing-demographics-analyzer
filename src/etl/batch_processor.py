"""
Batch processing utilities for memory-efficient ETL operations.
"""
import gc
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

BATCH_SIZE = 10000  # Process 10k rows at a time


def insert_dataframe_in_batches(
    df: pd.DataFrame,
    table_name: str,
    conn,
    batch_size: int = BATCH_SIZE,
    if_exists: str = "append",
    clear_first: bool = False
) -> int:
    """
    Insert a DataFrame into SQLite in batches to avoid memory issues.
    
    Args:
        df: DataFrame to insert
        table_name: Target table name
        conn: SQLite connection
        batch_size: Number of rows per batch
        if_exists: 'append' or 'replace'
        clear_first: If True, delete all rows before inserting
        
    Returns:
        Total number of rows inserted
    """
    if df is None or df.empty:
        logger.debug(f"Skipping {table_name}: empty or None")
        return 0
    
    total_rows = len(df)
    logger.info(f"Inserting {total_rows:,} rows into {table_name} in batches of {batch_size:,}")
    
    # Disable foreign key checks temporarily
    conn.execute("PRAGMA foreign_keys=OFF")
    
    # Clear table if requested
    if clear_first:
        try:
            conn.execute(f"DELETE FROM {table_name}")
            logger.debug(f"Cleared existing data from {table_name}")
        except Exception as e:
            logger.warning(f"Could not clear {table_name}: {e}")
    
    # Process in batches
    rows_inserted = 0
    for i in range(0, total_rows, batch_size):
        batch = df.iloc[i:i + batch_size]
        
        # Use append for all batches after the first (if if_exists='replace')
        batch_if_exists = if_exists if i == 0 else "append"
        
        try:
            batch.to_sql(
                table_name,
                conn,
                if_exists=batch_if_exists,
                index=False,
                method='multi',  # Use multi-row INSERT for better performance
                chunksize=1000   # SQLite chunk size
            )
            rows_inserted += len(batch)
            
            # Log progress
            if (i + batch_size) % (batch_size * 5) == 0 or (i + batch_size) >= total_rows:
                logger.info(f"  Progress: {rows_inserted:,}/{total_rows:,} rows ({100*rows_inserted/total_rows:.1f}%)")
            
            # Clear batch from memory
            del batch
            gc.collect()
            
        except Exception as e:
            logger.error(f"Error inserting batch {i}-{i+batch_size} into {table_name}: {e}")
            raise
    
    # Re-enable foreign key checks
    conn.execute("PRAGMA foreign_keys=ON")
    
    logger.info(f"✓ Completed {table_name}: {rows_inserted:,} rows inserted")
    return rows_inserted
    
    # Process in batches
    rows_inserted = 0
    for i in range(0, total_rows, batch_size):
        batch = df.iloc[i:i + batch_size]
        
        # Use append for all batches after the first (if if_exists='replace')
        batch_if_exists = if_exists if i == 0 else "append"
        
        try:
            batch.to_sql(
                table_name,
                conn,
                if_exists=batch_if_exists,
                index=False,
                method='multi',  # Use multi-row INSERT for better performance
                chunksize=1000   # SQLite chunk size
            )
            rows_inserted += len(batch)
            
            # Log progress
            if (i + batch_size) % (batch_size * 5) == 0 or (i + batch_size) >= total_rows:
                logger.info(f"  Progress: {rows_inserted:,}/{total_rows:,} rows ({100*rows_inserted/total_rows:.1f}%)")
            
            # Clear batch from memory
            del batch
            gc.collect()
            
        except Exception as e:
            logger.error(f"Error inserting batch {i}-{i+batch_size} into {table_name}: {e}")
            raise
    
    logger.info(f"✓ Completed {table_name}: {rows_inserted:,} rows inserted")
    return rows_inserted


def process_large_csv_in_chunks(
    file_path,
    processing_func,
    chunksize: int = 50000,
    **kwargs
):
    """
    Process a large CSV file in chunks to avoid loading entire file into memory.
    
    Args:
        file_path: Path to CSV file
        processing_func: Function to apply to each chunk
        chunksize: Number of rows per chunk
        **kwargs: Additional arguments to pass to processing_func
        
    Returns:
        Combined result from all chunks
    """
    logger.info(f"Processing {file_path} in chunks of {chunksize:,}")
    
    results = []
    chunk_num = 0
    
    try:
        for chunk in pd.read_csv(file_path, chunksize=chunksize, low_memory=False):
            chunk_num += 1
            logger.debug(f"Processing chunk {chunk_num} ({len(chunk):,} rows)")
            
            # Apply processing function
            result = processing_func(chunk, **kwargs)
            
            if result is not None and not (isinstance(result, pd.DataFrame) and result.empty):
                results.append(result)
            
            # Clear chunk from memory
            del chunk
            gc.collect()
        
        # Combine results
        if results:
            if isinstance(results[0], pd.DataFrame):
                combined = pd.concat(results, ignore_index=True)
                logger.info(f"Combined {len(results)} chunks into {len(combined):,} rows")
                return combined
            else:
                return results
        else:
            logger.warning("No results from chunk processing")
            return pd.DataFrame() if isinstance(results, list) else None
            
    except Exception as e:
        logger.error(f"Error processing chunks from {file_path}: {e}")
        raise


def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    
    Args:
        df: DataFrame to optimize
        
    Returns:
        Optimized DataFrame
    """
    if df is None or df.empty:
        return df
    
    start_mem = df.memory_usage(deep=True).sum() / 1024**2
    
    # Downcast integers
    int_cols = df.select_dtypes(include=['int64']).columns
    for col in int_cols:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    
    # Downcast floats
    float_cols = df.select_dtypes(include=['float64']).columns
    for col in float_cols:
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    end_mem = df.memory_usage(deep=True).sum() / 1024**2
    reduction = 100 * (start_mem - end_mem) / start_mem
    
    if reduction > 5:  # Only log if significant reduction
        logger.debug(f"Memory optimized: {start_mem:.2f}MB → {end_mem:.2f}MB ({reduction:.1f}% reduction)")
    
    return df
