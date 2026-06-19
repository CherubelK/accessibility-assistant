"""Shared timing decorator for nodes.

Diagnosing why a request was slow (vision call vs. Ollama swapping models
in/out of RAM vs. something else) previously meant manually polling CPU
usage and guessing. Printing how long each node actually took makes that
immediate instead.
"""

import functools
import time


def timed_node(name: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(state):
            start = time.time()
            try:
                return func(state)
            finally:
                print(f"[{name}] took {time.time() - start:.1f}s")
        return wrapper
    return decorator
