"""Pattern matching decorators for bot handlers."""

import re
import functools
from typing import Callable, Optional, Any
from ..core.message import Message


def command(trigger: str, case_sensitive: bool = False):
    """
    Decorator for command-based handlers.
    
    Args:
        trigger: The command trigger (e.g., "!help", "/start")
        case_sensitive: Whether the command matching is case sensitive
        
    Returns:
        Decorator function
    """
    def decorator(handler: Callable[[Message], Optional[str]]):
        @functools.wraps(handler)
        def wrapper(message: Message) -> Optional[str]:
            text = message.text if case_sensitive else message.text.lower()
            cmd = trigger if case_sensitive else trigger.lower()
            
            if text.startswith(cmd):
                # Extract arguments after the command
                args_text = message.text[len(trigger):].strip()
                
                # Call handler with message and optional args
                try:
                    if args_text:
                        # Try to pass args if handler accepts them
                        import inspect
                        sig = inspect.signature(handler)
                        if len(sig.parameters) > 1:
                            return handler(message, args_text)
                    return handler(message)
                except TypeError:
                    # Handler doesn't accept args, just pass message
                    return handler(message)
            return None
        return wrapper
    return decorator


def contains(text: str, case_sensitive: bool = False):
    """
    Decorator for handlers that trigger when message contains specific text.
    
    Args:
        text: The text to look for
        case_sensitive: Whether the matching is case sensitive
        
    Returns:
        Decorator function
    """
    def decorator(handler: Callable[[Message], Optional[str]]):
        @functools.wraps(handler)
        def wrapper(message: Message) -> Optional[str]:
            msg_text = message.text if case_sensitive else message.text.lower()
            search_text = text if case_sensitive else text.lower()
            
            if search_text in msg_text:
                return handler(message)
            return None
        return wrapper
    return decorator


def regex(pattern: str, flags: int = 0):
    """
    Decorator for regex-based handlers.
    
    Args:
        pattern: The regex pattern to match
        flags: Regex flags (e.g., re.IGNORECASE)
        
    Returns:
        Decorator function
    """
    compiled_pattern = re.compile(pattern, flags)
    
    def decorator(handler: Callable):
        @functools.wraps(handler)
        def wrapper(message: Message) -> Optional[str]:
            match = compiled_pattern.search(message.text)
            if match:
                # Try to pass match groups to handler
                try:
                    import inspect
                    sig = inspect.signature(handler)
                    param_count = len(sig.parameters)
                    
                    if param_count == 1:
                        # Just message
                        return handler(message)
                    elif param_count == 2:
                        # Message and full match
                        return handler(message, match.group(0))
                    else:
                        # Message and capture groups
                        groups = match.groups()
                        return handler(message, *groups)
                except TypeError:
                    # Fallback to just message
                    return handler(message)
            return None
        return wrapper
    return decorator


def scheduled(cron_expression: str):
    """
    Decorator for scheduled handlers (placeholder - would need scheduler implementation).
    
    Args:
        cron_expression: Cron expression for scheduling
        
    Returns:
        Decorator function
    """
    def decorator(handler: Callable):
        @functools.wraps(handler)
        def wrapper(*args, **kwargs):
            # This would integrate with a scheduler like APScheduler
            # For now, just mark the function as scheduled
            handler._scheduled = True
            handler._cron = cron_expression
            return handler(*args, **kwargs)
        return wrapper
    return decorator


def only_from_user(user_identifier: str):
    """
    Decorator to restrict handler to specific user.
    
    Args:
        user_identifier: The user identifier to allow
        
    Returns:
        Decorator function
    """
    def decorator(handler: Callable[[Message], Optional[str]]):
        @functools.wraps(handler)
        def wrapper(message: Message) -> Optional[str]:
            if message.sender == user_identifier:
                return handler(message)
            return None
        return wrapper
    return decorator


def only_from_me():
    """
    Decorator to restrict handler to messages from the bot owner.
    
    Returns:
        Decorator function
    """
    def decorator(handler: Callable[[Message], Optional[str]]):
        @functools.wraps(handler)
        def wrapper(message: Message) -> Optional[str]:
            if message.is_from_me:
                return handler(message)
            return None
        return wrapper
    return decorator


def rate_limit(max_calls: int = 5, window_seconds: int = 60):
    """
    Decorator to rate limit handler calls per user.
    
    Args:
        max_calls: Maximum calls allowed in the window
        window_seconds: Time window in seconds
        
    Returns:
        Decorator function
    """
    import time
    from collections import defaultdict, deque
    
    call_history = defaultdict(deque)
    
    def decorator(handler: Callable[[Message], Optional[str]]):
        @functools.wraps(handler)
        def wrapper(message: Message) -> Optional[str]:
            now = time.time()
            user_calls = call_history[message.sender]
            
            # Remove old calls outside the window
            while user_calls and user_calls[0] < now - window_seconds:
                user_calls.popleft()
            
            # Check if user has exceeded rate limit
            if len(user_calls) >= max_calls:
                return "Rate limit exceeded. Please slow down."
            
            # Record this call
            user_calls.append(now)
            
            return handler(message)
        return wrapper
    return decorator 