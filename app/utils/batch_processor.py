"""Batch processing utilities."""
from typing import List, TypeVar, Callable, Awaitable
import asyncio
from tqdm import tqdm

T = TypeVar("T")
R = TypeVar("R")


async def process_batch_async(
    items: List[T],
    processor: Callable[[List[T]], Awaitable[List[R]]],
    batch_size: int = 100,
    description: str = "Processing",
) -> List[R]:
    """
    Process items in batches asynchronously.
    
    Args:
        items: List of items to process
        processor: Async function that processes a batch and returns results
        batch_size: Number of items per batch
        description: Description for progress bar
    
    Returns:
        List of all results
    """
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    with tqdm(total=len(items), desc=description) as pbar:
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_results = await processor(batch)
            results.extend(batch_results)
            pbar.update(len(batch))
    
    return results


def process_batch_sync(
    items: List[T],
    processor: Callable[[List[T]], List[R]],
    batch_size: int = 100,
    description: str = "Processing",
) -> List[R]:
    """
    Process items in batches synchronously.
    
    Args:
        items: List of items to process
        processor: Function that processes a batch and returns results
        batch_size: Number of items per batch
        description: Description for progress bar
    
    Returns:
        List of all results
    """
    results = []
    
    with tqdm(total=len(items), desc=description) as pbar:
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)
            pbar.update(len(batch))
    
    return results
