import time
import functools
import logging
from typing import Type, Union, List, Callable, Any

logger = logging.getLogger(__name__)

def retry_action(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception
):
    """
    Decorator to retry a function call if it raises specific exceptions.

    Args:
        max_retries (int): Maximum number of retries before giving up. Default is 3.
        delay (float): Initial delay between retries in seconds. Default is 1.0.
        backoff_factor (float): Multiplier applied to delay after each failure. Default is 2.0.
        exceptions (Union[Type[Exception], List[Type[Exception]]]): Exception(s) to catch and retry on. Default is Exception.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Tentativa {attempt}/{max_retries} falhou em '{func.__name__}': {type(e).__name__}: {e}. "
                            f"Tentando novamente em {current_delay:.2f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"Todas as {max_retries} tentativas falharam em '{func.__name__}'. "
                            f"Erro final: {e}"
                        )
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator
