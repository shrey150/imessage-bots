"""
Command Bot Example

Demonstrates various command patterns and decorators.
"""

from imessage_bot_framework import Bot, State
from imessage_bot_framework.decorators import command, only_from_me, rate_limit
import random
import time

# Create bot and state
bot = Bot("Command Bot", debug=True)
state = State("command_bot_state.json")

@bot.on_message
@command("!hello")
def hello_command(message):
    """Simple greeting command."""
    greetings = ["Hello!", "Hi there!", "Hey!", "Greetings!", "Howdy!"]
    return random.choice(greetings)

@bot.on_message
@command("!time")
def time_command(message):
    """Get current time."""
    return f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}"

@bot.on_message
@command("!count")
def count_command(message):
    """Increment user's counter."""
    count = state.increment(f"counter_{message.sender}")
    return f"Your count: {count}"

@bot.on_message
@command("!reset")
def reset_command(message):
    """Reset user's counter."""
    state.set(f"counter_{message.sender}", 0)
    return "Counter reset to 0!"

@bot.on_message
@command("!stats")
def stats_command(message):
    """Show bot statistics."""
    all_keys = state.get_all_keys()
    counter_keys = [k for k in all_keys if k.startswith("counter_")]
    total_counts = sum(state.get(k, 0) for k in counter_keys)
    
    return f"📊 Bot Stats:\n• Users: {len(counter_keys)}\n• Total counts: {total_counts}"

@bot.on_message
@command("!roll")
def dice_command(message, args):
    """Roll dice. Usage: !roll or !roll 20"""
    try:
        sides = int(args) if args else 6
        if sides < 2 or sides > 100:
            return "Dice must have 2-100 sides!"
        result = random.randint(1, sides)
        return f"🎲 Rolled a {result} (1-{sides})"
    except ValueError:
        return "Usage: !roll [number of sides]"

@bot.on_message
@command("!flip")
def coin_flip(message):
    """Flip a coin."""
    result = random.choice(["Heads", "Tails"])
    emoji = "🔴" if result == "Heads" else "🔵"
    return f"{emoji} {result}!"

@bot.on_message
@command("!help")
def help_command(message):
    """Show available commands."""
    commands = [
        "!hello - Get a greeting",
        "!time - Get current time", 
        "!count - Increment your counter",
        "!reset - Reset your counter",
        "!stats - Show bot statistics",
        "!roll [sides] - Roll dice",
        "!flip - Flip a coin",
        "!help - Show this help"
    ]
    return "Available commands:\n" + "\n".join(commands)

@bot.on_message
@command("!admin")
@only_from_me()
def admin_command(message, args):
    """Admin-only command."""
    if args == "shutdown":
        return "Shutting down... (just kidding!)"
    elif args == "status":
        return "Bot is running normally"
    else:
        return "Admin commands: shutdown, status"

@bot.on_message
@command("!spam")
@rate_limit(max_calls=3, window_seconds=60)
def limited_command(message):
    """Rate-limited command."""
    return "This command is rate-limited to 3 times per minute!"

if __name__ == "__main__":
    print("Starting Command Bot...")
    print("Try these commands: !hello, !time, !count, !help")
    bot.run() 