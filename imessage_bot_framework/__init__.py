"""
iMessage Bot Framework

A simple, flexible framework for building iMessage bots.
"""

__version__ = "0.1.0"
__author__ = "iMessage Bot Framework Team"

from .core.bot import Bot
from .core.message import Message
from .core.chat import Chat
from .state.state import State

# Make core components available at package level
__all__ = [
    "Bot",
    "Message", 
    "Chat",
    "State"
] 