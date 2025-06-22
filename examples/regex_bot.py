"""
Regex Bot Example

Demonstrates regex pattern matching for natural language processing.
"""

from imessage_bot_framework import Bot
from imessage_bot_framework.decorators import regex, contains
import re

bot = Bot("Regex Bot", debug=True)

@bot.on_message
@regex(r"(\d+)\s*([+\-*/])\s*(\d+)")
def calculator(message, a, op, b):
    """Calculator using regex pattern matching."""
    try:
        a, b = int(a), int(b)
        if op == '+': 
            result = a + b
        elif op == '-': 
            result = a - b
        elif op == '*': 
            result = a * b
        elif op == '/': 
            if b == 0:
                return "Cannot divide by zero!"
            result = a / b
        else:
            return "Unknown operator"
        
        return f"{a} {op} {b} = {result}"
    except ValueError:
        return "Invalid numbers"

@bot.on_message
@regex(r"remind me (?:to )?(.+?) in (\d+) (minute|minutes|hour|hours|day|days)", re.IGNORECASE)
def reminder_parser(message, task, amount, unit):
    """Parse reminder requests."""
    return f"I'll remind you to '{task}' in {amount} {unit}! (Feature coming soon)"

@bot.on_message
@regex(r"what(?:'s| is) the weather (?:in |for )?(.+)", re.IGNORECASE)
def weather_request(message, location):
    """Parse weather requests."""
    return f"Weather for {location}: Sunny, 72°F (This is a demo response)"

@bot.on_message
@regex(r"convert (\d+(?:\.\d+)?) (.*?) to (.*)", re.IGNORECASE)
def unit_converter(message, amount, from_unit, to_unit):
    """Parse unit conversion requests."""
    return f"Converting {amount} {from_unit} to {to_unit}: (Conversion feature coming soon)"

@bot.on_message
@regex(r"(?:my name is|i'm|i am) ([a-zA-Z]+)", re.IGNORECASE)
def name_introduction(message, name):
    """Detect name introductions."""
    return f"Nice to meet you, {name}! I'll remember that."

@bot.on_message
@regex(r"(\d{1,2}):(\d{2})\s*(am|pm)?", re.IGNORECASE)
def time_parser(message, hour, minute, ampm):
    """Parse time mentions."""
    ampm = ampm or ""
    return f"I see you mentioned the time {hour}:{minute} {ampm}"

@bot.on_message
@contains("pizza")
def pizza_mention(message):
    """Respond to pizza mentions."""
    return "Did someone say pizza? 🍕 I love pizza!"

@bot.on_message
@contains("thank")
def thank_you_response(message):
    """Respond to thank you messages."""
    return "You're welcome! 😊"

@bot.on_message
@regex(r"(?:call|phone|contact) (.+)", re.IGNORECASE)
def contact_request(message, person):
    """Parse contact requests."""
    return f"You want to contact {person}. I can't actually call them, but that's a good idea!"

@bot.on_message
@regex(r"(?:search|google|look up) (.+)", re.IGNORECASE)
def search_request(message, query):
    """Parse search requests."""
    return f"You want to search for '{query}'. Here's a demo result: Very interesting topic!"

@bot.on_message
def fallback_handler(message):
    """Fallback for unmatched messages."""
    if message.text.startswith("!"):
        return "I didn't understand that command. Try sending some natural language!"
    elif "?" in message.text:
        return "That's a great question! I'm still learning how to answer questions."
    elif len(message.text.split()) > 10:
        return "That's quite a long message! I'm still learning to process complex text."
    return None  # Don't respond to everything

if __name__ == "__main__":
    print("Starting Regex Bot...")
    print("Try these patterns:")
    print("• Math: '5 + 3' or '10 * 2'")
    print("• Reminders: 'remind me to call mom in 2 hours'")
    print("• Weather: 'what's the weather in New York'")
    print("• Conversions: 'convert 5 feet to meters'")
    print("• Introductions: 'my name is John'")
    print("• Or just mention 'pizza'!")
    bot.run() 