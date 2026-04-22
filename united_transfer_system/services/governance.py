from functools import wraps
from fastapi import HTTPException
import logging

def fail_closed_operation(func):
    """
    Decorator to ensure operations fail closed.
    If any security, finance, or audit step fails, the whole operation is blocked.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Fail-Closed Triggered: {func.__name__} failed with {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Sovereign Execution Error: Fail-Closed")
    return wrapper

def fail_closed_async_operation(func):
    """
    Async version of fail_closed_operation.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Fail-Closed Triggered (Async): {func.__name__} failed with {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Sovereign Execution Error: Fail-Closed")
    return wrapper
