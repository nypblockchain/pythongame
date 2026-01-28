"""
Python Syntax Card Game - Game Logic
Contains card definitions, deck management, validation rules, and game state.
"""

import random
import ast
from typing import Optional, Dict, List, Any, Tuple

# =============================================================================
# CARD CATEGORIES
# =============================================================================

CATEGORIES = {
    'LOOP': 'Loop keywords like for, while',
    'VARIABLE': 'Variable names like x, i, n, item',
    'KEYWORD': 'Python keywords like in, if, else, def, return',
    'FUNCTION': 'Built-in functions like range, print, len, input',
    'VALUE': 'Values like 1, 10, True, False, strings',
    'OPERATOR': 'Operators like +, -, ==, and, or, <, >',
    'SYNTAX_OPEN': 'Opening parenthesis (',
    'SYNTAX_CLOSE': 'Closing parenthesis )',
    'SYNTAX_COLON': 'Colon :',
    'SYNTAX_COMMA': 'Comma , for separating arguments',
    'SPECIAL': 'Special action cards',
    'START': 'Virtual category for game start'
}

# =============================================================================
# CARD DEFINITIONS
# Each card has: category, points, can_follow (list of categories it can follow)
# Optional: effect (for special cards), count (copies in deck)
# =============================================================================

CARDS = {
    # -------------------------------------------------------------------------
    # LOOP CARDS (Uncommon - 2 points)
    # -------------------------------------------------------------------------
    "for": {
        "category": "LOOP",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 2,
        "description": "For loop - iterates over a sequence",
        "python_tip": "The 'for' loop iterates over each item in a sequence (like a list, string, or range). It's perfect when you know exactly what you want to loop through.",
        "example": "for i in range(5):\n    print(i)  # Prints 0, 1, 2, 3, 4"
    },
    "while": {
        "category": "LOOP",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 1,
        "description": "While loop - repeats while condition is true",
        "python_tip": "The 'while' loop keeps running as long as its condition is True. Be careful to avoid infinite loops by ensuring the condition eventually becomes False!",
        "example": "count = 0\nwhile count < 3:\n    print(count)\n    count += 1"
    },

    # -------------------------------------------------------------------------
    # VARIABLE CARDS (Common - 1 point)
    # -------------------------------------------------------------------------
    "x": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["START", "LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_COLON", "SYNTAX_COMMA", "VALUE", "FUNCTION"],
        "count": 2,
        "description": "Common variable name",
        "python_tip": "Variables store data for later use. 'x' is commonly used as a generic variable name, especially in math expressions and simple examples.",
        "example": "x = 10\nprint(x * 2)  # Prints 20"
    },
    "i": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["START", "LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_COLON", "SYNTAX_COMMA", "VALUE", "FUNCTION"],
        "count": 3,
        "description": "Iterator variable",
        "python_tip": "The variable 'i' is traditionally used as a loop counter or index. It stands for 'index' or 'iterator' and is very common in for loops.",
        "example": "for i in range(3):\n    print(f'Iteration {i}')"
    },
    "n": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["START", "LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_COLON", "SYNTAX_COMMA", "VALUE", "FUNCTION"],
        "count": 2,
        "description": "Number variable",
        "python_tip": "The variable 'n' typically represents a number or count. It's commonly used for the size of something or as a parameter in algorithms.",
        "example": "n = 5\nfor i in range(n):\n    print(i)"
    },
    "item": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["START", "LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_COLON", "SYNTAX_COMMA", "VALUE", "FUNCTION"],
        "count": 2,
        "description": "Item in a collection",
        "python_tip": "When iterating through a collection, 'item' is a descriptive name for each element. Using meaningful names makes code more readable!",
        "example": "fruits = ['apple', 'banana']\nfor item in fruits:\n    print(item)"
    },
    "result": {
        "category": "VARIABLE",
        "points": 1,
        "can_follow": ["START", "LOOP", "KEYWORD", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_COLON", "SYNTAX_COMMA", "VALUE", "FUNCTION"],
        "count": 2,
        "description": "Result variable",
        "python_tip": "The 'result' variable stores the output of a calculation or operation. It's good practice to use descriptive names like this!",
        "example": "result = 0\nfor i in range(5):\n    result += i\nprint(result)  # Prints 10"
    },

    # -------------------------------------------------------------------------
    # KEYWORD CARDS (Uncommon - 2 points)
    # -------------------------------------------------------------------------
    "in": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["VARIABLE"],
        "count": 3,
        "description": "Membership test / iteration",
        "python_tip": "The 'in' keyword has two uses: checking if something exists in a collection, or iterating through items in a for loop.",
        "example": "# Membership test:\nif 'a' in 'apple':\n    print('Found!')\n\n# Iteration:\nfor x in [1, 2, 3]:\n    print(x)"
    },
    "if": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 2,
        "description": "Conditional statement",
        "python_tip": "The 'if' statement runs code only when a condition is True. It's the foundation of decision-making in programming!",
        "example": "age = 18\nif age >= 18:\n    print('You can vote!')"
    },
    "else": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["SYNTAX_COLON"],
        "count": 1,
        "description": "Alternative branch",
        "python_tip": "The 'else' block runs when the 'if' condition is False. It provides an alternative path for your code.",
        "example": "age = 15\nif age >= 18:\n    print('Adult')\nelse:\n    print('Minor')"
    },
    "elif": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["SYNTAX_COLON"],
        "count": 1,
        "description": "Else-if branch",
        "python_tip": "Short for 'else if', 'elif' lets you check multiple conditions in sequence. Only the first True condition's block runs.",
        "example": "score = 85\nif score >= 90:\n    print('A')\nelif score >= 80:\n    print('B')\nelse:\n    print('C')"
    },
    "not": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 1,
        "description": "Logical negation",
        "python_tip": "The 'not' operator flips a boolean value: True becomes False, and False becomes True. Useful for checking opposite conditions!",
        "example": "is_raining = False\nif not is_raining:\n    print('Go outside!')"
    },

    # -------------------------------------------------------------------------
    # RARE KEYWORD CARDS (Rare - 3 points)
    # -------------------------------------------------------------------------
    "def": {
        "category": "KEYWORD",
        "points": 3,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 1,
        "description": "Function definition",
        "python_tip": "The 'def' keyword defines a reusable function. Functions help organize code and avoid repetition. Always give functions descriptive names!",
        "example": "def greet(name):\n    return f'Hello, {name}!'\n\nprint(greet('World'))"
    },
    "return": {
        "category": "KEYWORD",
        "points": 3,
        "can_follow": ["SYNTAX_COLON", "START"],
        "count": 1,
        "description": "Return statement",
        "python_tip": "The 'return' statement sends a value back from a function. Without it, functions return None by default.",
        "example": "def add(a, b):\n    return a + b\n\nresult = add(3, 5)  # result = 8"
    },
    "break": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 2,
        "description": "Exit loop early",
        "python_tip": "The 'break' statement immediately exits the innermost loop. Great for stopping when you find what you're looking for!",
        "example": "for i in range(10):\n    if i == 5:\n        break  # Exit loop\n    print(i)  # Prints 0-4"
    },
    "continue": {
        "category": "KEYWORD",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 2,
        "description": "Skip to next iteration",
        "python_tip": "The 'continue' statement skips the rest of the current loop iteration and moves to the next one.",
        "example": "for i in range(5):\n    if i == 2:\n        continue  # Skip 2\n    print(i)  # Prints 0, 1, 3, 4"
    },
    "pass": {
        "category": "KEYWORD",
        "points": 1,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 2,
        "description": "Do nothing placeholder",
        "python_tip": "The 'pass' statement does nothing - it's a placeholder for empty code blocks. Useful when defining functions or classes you'll fill in later.",
        "example": "def todo_function():\n    pass  # Implement later\n\nif x > 0:\n    pass  # Handle this case later"
    },

    # -------------------------------------------------------------------------
    # FUNCTION CARDS (Uncommon - 2 points)
    # -------------------------------------------------------------------------
    "range": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_COMMA"],
        "count": 3,
        "description": "Generate number sequence",
        "python_tip": "range() generates a sequence of numbers. range(5) gives 0-4, range(1, 6) gives 1-5, and range(0, 10, 2) gives even numbers 0-8.",
        "example": "# Count from 0 to 4\nfor i in range(5):\n    print(i)\n\n# Count from 1 to 10 by 2s\nfor i in range(1, 11, 2):\n    print(i)  # 1, 3, 5, 7, 9"
    },
    "print": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["START", "SYNTAX_COLON"],
        "count": 2,
        "description": "Output to console",
        "python_tip": "print() displays output to the screen. You can print multiple items separated by commas, and use f-strings for formatted output.",
        "example": "name = 'Alice'\nage = 25\nprint('Hello, World!')\nprint(f'{name} is {age} years old')"
    },
    "len": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 1,
        "description": "Get length of sequence",
        "python_tip": "len() returns the number of items in a collection (list, string, dict, etc.). Essential for loops and validation!",
        "example": "text = 'Hello'\nnumbers = [1, 2, 3, 4, 5]\n\nprint(len(text))     # 5\nprint(len(numbers))  # 5"
    },
    "input": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 1,
        "description": "Get user input",
        "python_tip": "input() pauses the program and waits for the user to type something. It always returns a string, so convert if you need a number!",
        "example": "name = input('What is your name? ')\nage = int(input('How old are you? '))\nprint(f'Hi {name}, you are {age}!')"
    },
    "int": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 1,
        "description": "Convert to integer",
        "python_tip": "int() converts a value to a whole number (integer). Useful for converting user input or truncating decimals.",
        "example": "text = '42'\nnum = int(text)  # Now it's a number\n\ndecimal = 3.7\nwhole = int(decimal)  # 3 (truncates, doesn't round)"
    },
    "str": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 1,
        "description": "Convert to string",
        "python_tip": "str() converts any value to a string (text). Needed when you want to concatenate numbers with text.",
        "example": "age = 25\nmessage = 'I am ' + str(age) + ' years old'\n# Or use f-strings:\nmessage = f'I am {age} years old'"
    },
    "max": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 1,
        "description": "Get maximum value",
        "python_tip": "max() returns the largest item in a sequence or among arguments. Works with numbers, strings, and more!",
        "example": "print(max(3, 7, 2))  # 7\nprint(max([1, 5, 3]))  # 5\nprint(max('apple', 'banana'))  # 'banana'"
    },
    "min": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 1,
        "description": "Get minimum value",
        "python_tip": "min() returns the smallest item in a sequence or among arguments. Works with numbers, strings, and more!",
        "example": "print(min(3, 7, 2))  # 2\nprint(min([1, 5, 3]))  # 1\nprint(min('apple', 'banana'))  # 'apple'"
    },
    "abs": {
        "category": "FUNCTION",
        "points": 2,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN"],
        "count": 1,
        "description": "Absolute value",
        "python_tip": "abs() returns the absolute (positive) value of a number. Useful for distances and differences!",
        "example": "print(abs(-5))  # 5\nprint(abs(5))   # 5\ndiff = abs(a - b)  # Always positive"
    },

    # -------------------------------------------------------------------------
    # VALUE CARDS (Common - 1 point)
    # -------------------------------------------------------------------------
    "0": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "SYNTAX_COMMA", "OPERATOR", "KEYWORD", "VARIABLE"],
        "count": 2,
        "description": "Number zero",
        "python_tip": "Zero is special in Python: it's 'falsy' (acts like False in conditions). Often used as starting value for counters and accumulators.",
        "example": "count = 0\nwhile count < 5:\n    count += 1\n\n# Zero is falsy\nif not 0:\n    print('Zero is falsy!')"
    },
    "1": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "SYNTAX_COMMA", "OPERATOR", "KEYWORD", "VARIABLE"],
        "count": 3,
        "description": "Number one",
        "python_tip": "The number 1 is commonly used for incrementing counters, starting ranges from 1, or as a 'truthy' value.",
        "example": "# Start counting from 1\nfor i in range(1, 6):\n    print(i)  # 1, 2, 3, 4, 5\n\n# Increment by 1\ncount += 1"
    },
    "10": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "SYNTAX_COMMA", "OPERATOR", "KEYWORD", "VARIABLE"],
        "count": 2,
        "description": "Number ten",
        "python_tip": "Ten is a common loop limit and useful for testing. In Python, integers have no size limit!",
        "example": "for i in range(10):\n    print(i)  # 0 through 9\n\nif score >= 10:\n    print('Double digits!')"
    },
    "5": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "SYNTAX_COMMA", "OPERATOR", "KEYWORD", "VARIABLE"],
        "count": 2,
        "description": "Number five",
        "python_tip": "Five is a common loop limit and appears frequently in examples. A handy middle value!",
        "example": "for i in range(5):\n    print(i)  # 0-4\n\nif x > 5:\n    print('Big number')"
    },
    "2": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "SYNTAX_COMMA", "OPERATOR", "KEYWORD", "VARIABLE"],
        "count": 2,
        "description": "Number two",
        "python_tip": "Two is useful for doubling, halving, and checking even/odd numbers with modulo!",
        "example": "double = x * 2\nhalf = x // 2\nis_even = (n % 2 == 0)"
    },
    "True": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_COMMA", "VARIABLE"],
        "count": 2,
        "description": "Boolean true",
        "python_tip": "True is a boolean value representing 'yes' or 'on'. Note the capital T! Used in conditions and flags.",
        "example": "is_running = True\n\nwhile is_running:\n    # Do something\n    if should_stop:\n        is_running = False"
    },
    "False": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_COMMA", "VARIABLE"],
        "count": 2,
        "description": "Boolean false",
        "python_tip": "False is a boolean value representing 'no' or 'off'. Note the capital F! Equivalent to 0 in numeric contexts.",
        "example": "game_over = False\n\nwhile not game_over:\n    # Play game\n    if lives == 0:\n        game_over = True"
    },
    "None": {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["KEYWORD", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_COMMA", "VARIABLE"],
        "count": 1,
        "description": "None value",
        "python_tip": "None represents 'nothing' or 'no value'. Functions without a return statement return None. Use 'is None' to check!",
        "example": "result = None\n\ndef maybe_find(items, target):\n    for item in items:\n        if item == target:\n            return item\n    return None  # Not found\n\nif result is None:\n    print('No result yet')"
    },
    '"hello"': {
        "category": "VALUE",
        "points": 1,
        "can_follow": ["SYNTAX_OPEN", "SYNTAX_COMMA", "OPERATOR", "KEYWORD", "VARIABLE"],
        "count": 2,
        "description": "String literal",
        "python_tip": "Strings are sequences of characters enclosed in quotes. You can use single ('') or double (\"\") quotes - they work the same!",
        "example": "greeting = \"hello\"\nprint(greeting.upper())  # HELLO\nprint(greeting[0])       # h\nprint(len(greeting))     # 5"
    },

    # -------------------------------------------------------------------------
    # OPERATOR CARDS (Common - 1 point)
    # -------------------------------------------------------------------------
    "+": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Addition",
        "python_tip": "The + operator adds numbers together. For strings, it concatenates (joins) them. For lists, it combines them!",
        "example": "# Numbers\nresult = 5 + 3  # 8\n\n# Strings\ngreeting = 'Hello' + ' World'  # 'Hello World'\n\n# Lists\ncombined = [1, 2] + [3, 4]  # [1, 2, 3, 4]"
    },
    "-": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Subtraction",
        "python_tip": "The - operator subtracts numbers. Can also be used as negative sign. Works with sets to find differences!",
        "example": "result = 10 - 3    # 7\nnegative = -5      # Negative number\n\n# Set difference\na = {1, 2, 3}\nb = {2, 3, 4}\nprint(a - b)  # {1}"
    },
    "*": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Multiplication",
        "python_tip": "The * operator multiplies numbers. For strings/lists, it repeats them! Also used for unpacking (*args).",
        "example": "result = 4 * 5  # 20\n\n# String repetition\nline = '-' * 10  # '----------'\n\n# List repetition\nzeros = [0] * 3  # [0, 0, 0]"
    },
    "/": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Division",
        "python_tip": "The / operator divides numbers and always returns a float. Use // for integer division (floor division).",
        "example": "result = 10 / 3   # 3.333...\nwhole = 10 // 3   # 3 (integer division)\n\n# Watch out for division by zero!\nif denominator != 0:\n    result = num / denominator"
    },
    "==": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Equality check",
        "python_tip": "The == operator checks if two values are equal. Don't confuse with = (assignment)! Returns True or False.",
        "example": "x = 5\nif x == 5:\n    print('x is 5!')  # This runs\n\n# Works with any type\nif name == 'Alice':\n    print('Hi Alice!')"
    },
    "!=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Not equal check",
        "python_tip": "The != operator checks if two values are NOT equal. Returns True if they differ, False if they're the same.",
        "example": "if password != 'secret':\n    print('Wrong password!')\n\nif status != 'done':\n    continue_processing()"
    },
    "<": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Less than",
        "python_tip": "The < operator checks if the left value is smaller than the right. Works with numbers, strings (alphabetically), and more!",
        "example": "if age < 18:\n    print('Minor')\n\n# String comparison (alphabetical)\nif 'apple' < 'banana':\n    print('apple comes first')  # True"
    },
    ">": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Greater than",
        "python_tip": "The > operator checks if the left value is larger than the right. Essential for comparisons and sorting logic!",
        "example": "if score > 100:\n    print('High score!')\n\n# Find maximum manually\nif a > b:\n    maximum = a\nelse:\n    maximum = b"
    },
    "<=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Less than or equal",
        "python_tip": "The <= operator checks if left is smaller OR equal to right. Useful for inclusive bounds in conditions.",
        "example": "if age <= 12:\n    print('Child ticket')\n\n# Inclusive range check\nif 1 <= x <= 10:\n    print('x is between 1 and 10')"
    },
    ">=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Greater than or equal",
        "python_tip": "The >= operator checks if left is larger OR equal to right. Common for minimum value checks!",
        "example": "if age >= 18:\n    print('You can vote!')\n\n# Ensure minimum\nif quantity >= 1:\n    process_order()"
    },
    "and": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Logical and",
        "python_tip": "The 'and' operator returns True only if BOTH conditions are True. Python short-circuits: if first is False, second isn't checked.",
        "example": "if age >= 18 and has_license:\n    print('Can drive!')\n\n# Both must be true\nif username and password:\n    login(username, password)"
    },
    "or": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 1,
        "description": "Logical or",
        "python_tip": "The 'or' operator returns True if EITHER condition is True. Short-circuits: if first is True, second isn't checked.",
        "example": "if is_admin or is_owner:\n    allow_access()\n\n# Default value pattern\nname = user_input or 'Anonymous'"
    },
    "=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VARIABLE"],
        "count": 3,
        "description": "Assignment",
        "python_tip": "The = operator assigns a value to a variable. The variable goes on the left, the value on the right. Not the same as ==!",
        "example": "x = 10           # Assign 10 to x\nname = 'Alice'   # Assign string to name\nresult = a + b   # Assign expression result"
    },
    "+=": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VARIABLE"],
        "count": 2,
        "description": "Add and assign",
        "python_tip": "The += operator adds to a variable and reassigns. x += 1 is shorthand for x = x + 1. Works with strings too!",
        "example": "count = 0\ncount += 1  # count is now 1\ncount += 5  # count is now 6\n\n# With strings\nmessage = 'Hello'\nmessage += ' World'  # 'Hello World'"
    },
    "%": {
        "category": "OPERATOR",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE", "FUNCTION"],
        "count": 2,
        "description": "Modulo (remainder)",
        "python_tip": "The % operator returns the remainder of division. Perfect for checking if a number is even (n % 2 == 0) or for cycling through values!",
        "example": "# Check if even\nif n % 2 == 0:\n    print('Even!')\n\n# Cycle 0, 1, 2, 0, 1, 2...\nindex = count % 3"
    },
    ",": {
        "category": "SYNTAX_COMMA",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 3,
        "description": "Comma separator",
        "python_tip": "Commas separate arguments in function calls, items in lists, and values in tuples. Essential for multi-argument functions!",
        "example": "range(1, 10)  # Start at 1, end before 10\nprint('Hello', 'World')  # Multiple args\npoint = (x, y)  # Tuple"
    },

    # -------------------------------------------------------------------------
    # SYNTAX CARDS (Common - 1 point)
    # -------------------------------------------------------------------------
    "(": {
        "category": "SYNTAX_OPEN",
        "points": 1,
        "can_follow": ["FUNCTION", "KEYWORD"],
        "count": 3,
        "description": "Open parenthesis",
        "python_tip": "Opening parentheses start function calls, group expressions, or define tuples. Every ( needs a matching )!",
        "example": "print('Hello')      # Function call\nresult = (a + b) * c  # Grouping\ncoords = (10, 20)     # Tuple"
    },
    ")": {
        "category": "SYNTAX_CLOSE",
        "points": 1,
        "can_follow": ["VALUE", "VARIABLE", "SYNTAX_CLOSE"],
        "count": 3,
        "description": "Close parenthesis",
        "python_tip": "Closing parentheses end function calls or grouped expressions. Must match each opening parenthesis!",
        "example": "len('hello')   # Closes len() call\n((a + b) * c)  # Multiple levels OK\nprint(sum([1, 2, 3]))  # Nested calls"
    },
    ":": {
        "category": "SYNTAX_COLON",
        "points": 1,
        "can_follow": ["SYNTAX_CLOSE", "VALUE", "VARIABLE", "KEYWORD"],
        "count": 4,
        "description": "Colon - ends statement",
        "python_tip": "The colon starts a new code block after if, for, while, def, class, etc. The next line must be indented!",
        "example": "if x > 0:        # Colon required!\n    print('Positive')\n\nfor i in range(5):\n    print(i)"
    },

    # -------------------------------------------------------------------------
    # SPECIAL CARDS (0 points - action effects)
    # -------------------------------------------------------------------------
    "Draw 2": {
        "category": "SPECIAL",
        "points": 0,
        "can_follow": ["START", "LOOP", "KEYWORD", "FUNCTION", "VALUE", 
                       "VARIABLE", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_CLOSE", 
                       "SYNTAX_COLON"],
        "count": 1,
        "effect": "draw_2",
        "description": "Force opponent to draw 2 cards",
        "python_tip": "Strategic card! Makes your opponent draw 2 cards from the deck. More cards can mean more options, but also more clutter!",
        "example": "# No Python equivalent - this is a game action!\n# Use strategically when opponent has few cards"
    },
    "Discard 2": {
        "category": "SPECIAL",
        "points": 0,
        "can_follow": ["START", "LOOP", "KEYWORD", "FUNCTION", "VALUE", 
                       "VARIABLE", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_CLOSE", 
                       "SYNTAX_COLON"],
        "count": 1,
        "effect": "discard_2",
        "description": "Force opponent to discard 2 random cards",
        "python_tip": "Powerful disruption! Forces opponent to randomly discard 2 cards. Could remove key cards they need!",
        "example": "# No Python equivalent - this is a game action!\n# Best used when opponent has valuable cards"
    },
    "Skip": {
        "category": "SPECIAL",
        "points": 0,
        "can_follow": ["START", "LOOP", "KEYWORD", "FUNCTION", "VALUE", 
                       "VARIABLE", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_CLOSE", 
                       "SYNTAX_COLON"],
        "count": 1,
        "effect": "skip",
        "description": "Skip opponent's turn",
        "python_tip": "Like 'continue' in a loop! Skips opponent's turn entirely, giving you another chance to play.",
        "example": "# Similar to 'continue' in loops:\nfor i in range(10):\n    if i % 2 == 0:\n        continue  # Skip even numbers\n    print(i)"
    },
    "Wild": {
        "category": "SPECIAL",
        "points": 0,
        "can_follow": ["START", "LOOP", "KEYWORD", "FUNCTION", "VALUE", 
                       "VARIABLE", "OPERATOR", "SYNTAX_OPEN", "SYNTAX_CLOSE", 
                       "SYNTAX_COLON"],
        "count": 2,
        "effect": "wild",
        "description": "Can be played as any category",
        "python_tip": "Like a wildcard import! This card bridges any syntax gap - play it when you're stuck, then any card can follow.",
        "example": "# Similar to flexible typing in Python:\nfrom typing import Any\n\ndef process(data: Any):  # Any type works!\n    pass"
    },
}

# =============================================================================
# DECK MANAGEMENT
# =============================================================================

def create_deck() -> List[str]:
    """
    Create a full deck of cards based on card definitions.
    Returns a list of card names (with duplicates based on count).
    """
    deck = []
    for card_name, card_data in CARDS.items():
        count = card_data.get("count", 1)
        deck.extend([card_name] * count)
    return deck


def shuffle_deck(deck: List[str]) -> List[str]:
    """Shuffle a deck of cards in place and return it."""
    random.shuffle(deck)
    return deck


def draw_cards(deck: List[str], num_cards: int) -> List[str]:
    """
    Draw cards from the top of the deck.
    Returns a list of drawn cards.
    """
    drawn = []
    for _ in range(min(num_cards, len(deck))):
        if deck:
            drawn.append(deck.pop())
    return drawn


# =============================================================================
# PYTHON CODE BUILDER AND VALIDATOR
# =============================================================================

def build_python_code(played_cards: List[str], pending_card: str = None, 
                      for_display: bool = False) -> str:
    """
    Build a Python code string from the sequence of played cards.
    
    Args:
        played_cards: List of cards already played
        pending_card: Optional card to add to the sequence for validation
        for_display: If True, format for display (no 'pass' placeholder, add cursor)
        
    Returns:
        A string representing the Python code built from the cards
    """
    # Combine cards with pending card if provided
    cards = list(played_cards)
    if pending_card:
        cards.append(pending_card)
    
    if not cards:
        return ""
    
    # Filter out special cards (they don't contribute to Python code)
    code_cards = [c for c in cards if c in CARDS and CARDS[c]["category"] != "SPECIAL"]
    
    if not code_cards:
        return ""
    
    # Keywords that start new statements (after colon)
    statement_starters = {"for", "while", "if", "elif", "else", "def", "class", 
                          "try", "except", "finally", "with", "return", "print"}
    
    # Track statement structure
    lines = []
    current_line = ""
    indent_level = 0
    in_paren = 0  # Track parenthesis nesting
    last_was_colon = False
    
    for i, card_name in enumerate(code_cards):
        card = CARDS.get(card_name, {})
        category = card.get("category", "")
        
        # Check if this card starts a new statement after a colon
        if last_was_colon and card_name in statement_starters:
            # Save current line and start new one with proper indent
            if current_line.strip():
                lines.append(("    " * (indent_level - 1)) + current_line.strip())
            current_line = ""
            last_was_colon = False
        
        # Handle spacing
        if current_line:
            prev_card = code_cards[i - 1] if i > 0 else None
            prev_card_data = CARDS.get(prev_card, {}) if prev_card else {}
            prev_category = prev_card_data.get("category", "")
            
            needs_space = True
            
            # No space after opening parenthesis
            if prev_category == "SYNTAX_OPEN":
                needs_space = False
            # No space before closing parenthesis
            if category == "SYNTAX_CLOSE":
                needs_space = False
            # No space before colon
            if category == "SYNTAX_COLON":
                needs_space = False
            # No space between function name and opening paren
            if prev_category == "FUNCTION" and category == "SYNTAX_OPEN":
                needs_space = False
            # No space after 'not' keyword when followed by a variable or value
            if prev_card == "not" and category in ["VARIABLE", "VALUE"]:
                needs_space = True  # Actually need space: "not x"
            # No space around some operators in certain contexts
            if prev_category == "KEYWORD" and category == "SYNTAX_OPEN":
                needs_space = False
            
            if needs_space:
                current_line += " "
        
        # Add the card text
        current_line += card_name
        
        # Track parenthesis nesting
        if category == "SYNTAX_OPEN":
            in_paren += 1
        elif category == "SYNTAX_CLOSE":
            in_paren = max(0, in_paren - 1)
        
        # Handle colon - ends a statement header
        if category == "SYNTAX_COLON":
            indent_level += 1
            last_was_colon = True
    
    # Add the final line
    if current_line.strip():
        if lines:
            # This is a continuation after a colon
            lines.append(("    " * indent_level) + current_line.strip())
        else:
            lines.append(current_line.strip())
    
    # Build the final code
    if not lines:
        return ""
    
    code = "\n".join(lines)
    
    # For validation: add 'pass' placeholder if code ends with colon
    if not for_display and code.rstrip().endswith(":"):
        code += "\n" + "    " * indent_level + "pass"
    
    return code


def build_python_code_formatted(played_cards: List[str]) -> Dict[str, Any]:
    """
    Build Python code with detailed formatting info for display.
    
    Returns a dictionary with:
    - code: The formatted Python code string
    - lines: List of code lines with metadata
    - structure: Information about the code structure
    """
    if not played_cards:
        return {
            "code": "",
            "lines": [],
            "structure": {"statements": 0, "has_loop": False, "has_condition": False}
        }
    
    # Filter out special cards
    code_cards = [c for c in played_cards if c in CARDS and CARDS[c]["category"] != "SPECIAL"]
    
    if not code_cards:
        return {
            "code": "",
            "lines": [],
            "structure": {"statements": 0, "has_loop": False, "has_condition": False}
        }
    
    # Build structured representation
    statement_starters = {"for", "while", "if", "elif", "else", "def", "class", 
                          "try", "except", "finally", "with", "return", "print"}
    loop_keywords = {"for", "while"}
    condition_keywords = {"if", "elif", "else"}
    
    lines = []
    current_tokens = []
    indent_level = 0
    in_paren = 0
    has_loop = False
    has_condition = False
    statement_count = 0
    
    for i, card_name in enumerate(code_cards):
        card = CARDS.get(card_name, {})
        category = card.get("category", "")
        
        # Track structure
        if card_name in loop_keywords:
            has_loop = True
        if card_name in condition_keywords:
            has_condition = True
        
        # Check if this starts a new statement
        if current_tokens and card_name in statement_starters and in_paren == 0:
            # Check if previous was a colon (new block)
            if current_tokens and current_tokens[-1]["card"] == ":":
                # Save current line
                lines.append({
                    "tokens": current_tokens,
                    "indent": max(0, indent_level - 1),
                    "is_header": True
                })
                current_tokens = []
                statement_count += 1
        
        # Determine spacing
        space_before = ""
        if current_tokens:
            prev = current_tokens[-1]
            prev_category = prev["category"]
            
            needs_space = True
            if prev_category == "SYNTAX_OPEN":
                needs_space = False
            elif category == "SYNTAX_CLOSE":
                needs_space = False
            elif category == "SYNTAX_COLON":
                needs_space = False
            elif prev_category == "FUNCTION" and category == "SYNTAX_OPEN":
                needs_space = False
            elif prev_category == "KEYWORD" and category == "SYNTAX_OPEN":
                needs_space = False
            
            if needs_space:
                space_before = " "
        
        # Add token
        current_tokens.append({
            "card": card_name,
            "category": category,
            "space_before": space_before
        })
        
        # Track parentheses
        if category == "SYNTAX_OPEN":
            in_paren += 1
        elif category == "SYNTAX_CLOSE":
            in_paren = max(0, in_paren - 1)
        
        # Handle colon
        if category == "SYNTAX_COLON":
            indent_level += 1
    
    # Add final line
    if current_tokens:
        is_header = current_tokens[-1]["card"] == ":"
        lines.append({
            "tokens": current_tokens,
            "indent": indent_level if not is_header else max(0, indent_level - 1),
            "is_header": is_header
        })
        statement_count += 1
    
    # Build code string
    code_lines = []
    for line in lines:
        indent = "    " * line["indent"]
        text = "".join(t["space_before"] + t["card"] for t in line["tokens"])
        code_lines.append(indent + text.strip())
    
    code = "\n".join(code_lines)
    
    return {
        "code": code,
        "lines": lines,
        "structure": {
            "statements": statement_count,
            "has_loop": has_loop,
            "has_condition": has_condition,
            "indent_level": indent_level,
            "in_parentheses": in_paren > 0
        }
    }


def validate_python_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate if the given code string is valid Python syntax using ast.parse().
    
    Args:
        code: The Python code string to validate
        
    Returns:
        A tuple of (is_valid, error_message)
        - is_valid: True if the code is valid Python, False otherwise
        - error_message: Empty string if valid, error description if invalid
    """
    if not code or not code.strip():
        return (True, "")  # Empty code is considered valid (game start)
    
    try:
        ast.parse(code)
        return (True, "")
    except SyntaxError as e:
        error_msg = str(e.msg) if hasattr(e, 'msg') else str(e)
        return (False, error_msg)
    except Exception as e:
        return (False, str(e))


def can_form_valid_python(played_cards: List[str], pending_card: str) -> Tuple[bool, str]:
    """
    STRICT validation: Check if adding the pending card would form valid Python.
    
    The code must be either:
    1. Completely valid Python (can run with ast.parse)
    2. A valid incomplete expression that can be completed to valid Python
    
    Args:
        played_cards: List of cards already played
        pending_card: The card to potentially add
        
    Returns:
        A tuple of (is_valid, reason)
    """
    if pending_card not in CARDS:
        return (False, "Unknown card")
    
    card_data = CARDS[pending_card]
    
    # Special cards don't affect Python code validity
    if card_data["category"] == "SPECIAL":
        return (True, "Special card - always valid")
    
    # Filter out special cards from played_cards for validation
    code_cards = [c for c in played_cards if c in CARDS and CARDS[c]["category"] != "SPECIAL"]
    
    # Build the code with the pending card
    code = build_python_code(played_cards, pending_card)
    
    if not code or not code.strip():
        return (True, "Starting code")
    
    # STRICT: Try to parse the code directly
    is_valid, error = validate_python_syntax(code)
    if is_valid:
        return (True, "Valid Python syntax")
    
    # For incomplete expressions, try to complete them in valid ways
    # Only allow if the code COULD become valid Python
    
    code_stripped = code.rstrip()
    
    # Pattern 1: Incomplete for loop - "for VAR" or "for VAR in"
    if code_stripped.startswith("for "):
        completions = [
            f"{code_stripped} in range(10):\n    pass",
            f"{code_stripped} range(10):\n    pass",
            f"{code_stripped}:\n    pass",
        ]
        for comp in completions:
            try:
                ast.parse(comp)
                return (True, "Valid for loop pattern")
            except:
                continue
    
    # Pattern 2: Incomplete while loop - "while EXPR"
    if code_stripped.startswith("while "):
        try:
            ast.parse(f"{code_stripped}:\n    pass")
            return (True, "Valid while loop pattern")
        except:
            pass
    
    # Pattern 3: Incomplete if/elif - "if EXPR" or "elif EXPR"
    if code_stripped.startswith("if ") or code_stripped.startswith("elif "):
        try:
            ast.parse(f"{code_stripped}:\n    pass")
            return (True, "Valid conditional pattern")
        except:
            pass
    
    # Pattern 4: Incomplete function call - missing closing paren
    open_parens = code_stripped.count("(")
    close_parens = code_stripped.count(")")
    if open_parens > close_parens:
        # Try adding closing parens
        missing = open_parens - close_parens
        completed = code_stripped + ")" * missing
        try:
            ast.parse(completed)
            return (True, "Valid function call pattern")
        except:
            # Try with colon for statements like for/while/if
            try:
                ast.parse(f"{completed}:\n    pass")
                return (True, "Valid statement pattern")
            except:
                pass
    
    # Pattern 5: Incomplete assignment - "VAR =" or "VAR = EXPR OP"
    if " = " in code_stripped or code_stripped.endswith(" ="):
        # Try completing with a simple value
        completions = [
            f"{code_stripped} 0",
            f"{code_stripped} True",
            f"{code_stripped} None",
            f"{code_stripped}0",
        ]
        for comp in completions:
            try:
                ast.parse(comp)
                return (True, "Valid assignment pattern")
            except:
                continue
    
    # Pattern 6: Expression with trailing operator
    if code_stripped.endswith(("+", "-", "*", "/", "<", ">", "==", "!=", "<=", ">=", " and", " or")):
        completions = [
            f"{code_stripped} 1",
            f"{code_stripped} True",
            f"{code_stripped} x",
        ]
        for comp in completions:
            try:
                ast.parse(comp)
                return (True, "Valid expression pattern")
            except:
                continue
    
    # Pattern 7: After 'in' keyword (for loop)
    if code_stripped.endswith(" in"):
        try:
            ast.parse(f"{code_stripped} range(10):\n    pass")
            return (True, "Valid 'in' pattern")
        except:
            pass
    
    # Pattern 8: def/class definition
    if code_stripped.startswith("def ") or code_stripped.startswith("class "):
        completions = [
            f"{code_stripped}():\n    pass",
            f"{code_stripped}:\n    pass",
        ]
        for comp in completions:
            try:
                ast.parse(comp)
                return (True, "Valid definition pattern")
            except:
                continue
    
    # Pattern 9: return statement
    if code_stripped.startswith("return"):
        try:
            ast.parse(f"def f():\n    {code_stripped}")
            return (True, "Valid return pattern")
        except:
            pass
    
    # Pattern 10: Multi-statement with proper indentation (after colon)
    if "\n" in code:
        # Already has newlines - validate as-is or with simple completion
        try:
            ast.parse(code)
            return (True, "Valid multi-line code")
        except:
            # Try completing the last line
            lines = code.split("\n")
            last_line = lines[-1].strip()
            
            # If last line looks like a statement start, try completing it
            completions = [
                code + " in range(10):\n    pass",
                code + ":\n    pass",
                code + "()",
            ]
            for comp in completions:
                try:
                    ast.parse(comp)
                    return (True, "Valid block statement")
                except:
                    continue
    
    # Pattern 11: Statement inside a block (code has colon, adding new statement)
    if ":" in code_stripped:
        # Find the header and body
        try:
            # Try wrapping the new part as a valid statement inside the block
            lines = code.split("\n")
            if len(lines) >= 1:
                # Take everything and try completing it
                completions = [
                    code + " in range(10):\n        pass",
                    code + ":\n        pass",
                    code + "(x)",
                ]
                for comp in completions:
                    try:
                        ast.parse(comp)
                        return (True, "Valid nested statement")
                    except:
                        continue
        except:
            pass
    
    # Pattern 12: Statement starters (for, while, if, etc.) - can start at beginning or inside blocks
    statement_starters = {
        "for": " i in range(10):\n        pass",
        "while": " True:\n        pass", 
        "if": " True:\n        pass",
        "elif": " True:\n        pass",
        "def": " f():\n        pass",
        "class": " C:\n        pass",
        "try": ":\n        pass\n    except:\n        pass",
        "except": ":\n        pass",
        "print": "(x)",
        "return": " None",
    }
    
    if pending_card in statement_starters:
        completion = statement_starters[pending_card]
        # Try completing the current code with this statement
        try:
            ast.parse(code + completion)
            return (True, f"Valid {pending_card} statement")
        except:
            pass
        
        # For nested statements, may need different indent
        if "\n" in code:
            # Already multi-line, try with extra indent
            try:
                ast.parse(code + completion.replace("\n        ", "\n            "))
                return (True, f"Valid nested {pending_card}")
            except:
                pass
    
    # Pattern 13: else/elif after if block
    if pending_card == "else":
        # else needs to be at same indent as matching if
        if "if " in code:
            try:
                # Try adding else at proper indent
                ast.parse(code + ":\n        pass")
                return (True, "Valid else clause")
            except:
                pass
    
    # STRICT: If we can't validate it, reject it
    return (False, f"Invalid Python syntax: {error}")


def get_syntax_validation_info(played_cards: List[str]) -> Dict[str, Any]:
    """
    Get detailed information about the current Python syntax state.
    
    Args:
        played_cards: List of cards already played
        
    Returns:
        A dictionary with syntax information:
        - code: The built Python code
        - is_valid: Whether the current code is valid Python
        - is_complete: Whether the code is syntactically complete
        - error: Error message if invalid
        - suggestions: List of card categories that could make sense next
    """
    code = build_python_code(played_cards)
    is_valid, error = validate_python_syntax(code)
    
    # Check if the code is complete (can stand alone)
    is_complete = is_valid and not (
        code.count("(") > code.count(")") or
        code.rstrip().endswith((":", "+", "-", "*", "/", "=", "==", "!=", "<", ">", " in", " and", " or"))
    )
    
    # Generate suggestions for what could follow
    suggestions = []
    if not code:
        suggestions = ["LOOP", "KEYWORD", "FUNCTION", "VARIABLE"]
    elif code.rstrip().endswith(":"):
        suggestions = ["LOOP", "KEYWORD", "FUNCTION", "VARIABLE"]  # New statement
    elif code.count("(") > code.count(")"):
        suggestions = ["VALUE", "VARIABLE", "FUNCTION", "SYNTAX_CLOSE"]
    elif code.rstrip().endswith(" in"):
        suggestions = ["FUNCTION", "VARIABLE", "VALUE"]
    else:
        # Default suggestions based on last card
        last_non_special = None
        for card in reversed(played_cards):
            if card in CARDS and CARDS[card]["category"] != "SPECIAL":
                last_non_special = card
                break
        
        if last_non_special:
            last_category = CARDS[last_non_special]["category"]
            if last_category == "LOOP":
                suggestions = ["VARIABLE"]
            elif last_category == "VARIABLE":
                suggestions = ["KEYWORD", "OPERATOR", "SYNTAX_COLON"]
            elif last_category == "KEYWORD":
                suggestions = ["VARIABLE", "VALUE", "FUNCTION", "SYNTAX_OPEN"]
            elif last_category == "FUNCTION":
                suggestions = ["SYNTAX_OPEN"]
            elif last_category == "VALUE":
                suggestions = ["OPERATOR", "SYNTAX_CLOSE", "SYNTAX_COLON"]
            elif last_category == "OPERATOR":
                suggestions = ["VALUE", "VARIABLE", "FUNCTION"]
            elif last_category == "SYNTAX_OPEN":
                suggestions = ["VALUE", "VARIABLE", "FUNCTION"]
            elif last_category == "SYNTAX_CLOSE":
                suggestions = ["OPERATOR", "SYNTAX_COLON", "SYNTAX_CLOSE"]
    
    # Get formatted code for display
    formatted = build_python_code_formatted(played_cards)
    
    return {
        "code": code,
        "formatted_code": formatted["code"],
        "code_structure": formatted["structure"],
        "is_valid": is_valid,
        "is_complete": is_complete,
        "error": error,
        "suggestions": suggestions
    }


# =============================================================================
# CARD VALIDATION
# =============================================================================

def get_last_card_category(played_cards: List[str]) -> str:
    """
    Get the category of the last played card.
    Returns 'START' if no cards have been played.
    Colon acts as a statement boundary, so it returns 'START' to allow
    new statements to begin after a colon.
    """
    if not played_cards:
        return "START"
    
    last_card = played_cards[-1]
    
    # Colon acts as statement boundary - treat like start of new statement
    if last_card == ":":
        return "START"
    
    if last_card in CARDS:
        return CARDS[last_card]["category"]
    return "START"


def can_play_card(card_name: str, played_cards: List[str], last_was_wild: bool = False, 
                  open_paren_count: int = 0, use_flexible_validation: bool = True) -> bool:
    """
    Check if a card can be played given the current played cards.
    Returns True if the card can be played, False otherwise.
    
    STRICT VALIDATION: The resulting code must be valid Python syntax.
    Cards that would create invalid/nonsensical code are rejected.
    
    Args:
        card_name: The name of the card to play
        played_cards: List of cards already played
        last_was_wild: If True, validates with Python syntax (Wild bridges gaps)
        open_paren_count: Number of currently unbalanced open parentheses
        use_flexible_validation: If True, use strict Python syntax validation
    """
    if card_name not in CARDS:
        return False
    
    card = CARDS[card_name]
    
    # Special cards can be played anytime
    if card["category"] == "SPECIAL":
        return True
    
    # Validate parenthesis balance: ) can only be played if there's an open (
    if card_name == ")" and open_paren_count <= 0:
        return False
    
    # STRICT VALIDATION: Always check if result is valid Python
    # Category rules alone are not sufficient - code must make sense
    
    # First, quick category check (optimization)
    last_category = get_last_card_category(played_cards)
    can_follow = card.get("can_follow", [])
    
    # Check category rules
    category_valid = False
    if last_category == "START" and played_cards and played_cards[-1] == ":":
        if last_category in can_follow or "SYNTAX_COLON" in can_follow:
            category_valid = True
    elif last_category in can_follow:
        category_valid = True
    elif last_was_wild:
        category_valid = True  # Wild allows any category
    
    # Even if category is valid, MUST pass Python syntax check
    is_valid, reason = can_form_valid_python(played_cards, card_name)
    
    if not is_valid:
        return False  # Invalid Python - reject
    
    # If category rules pass AND Python is valid, allow
    if category_valid:
        return True
    
    # If only Python validation passes (not category), still allow
    # This enables flexible combinations that make valid Python
    return is_valid


def can_play_card_with_reason(card_name: str, played_cards: List[str], last_was_wild: bool = False,
                               open_paren_count: int = 0) -> Tuple[bool, str]:
    """
    Check if a card can be played and return the reason why or why not.
    
    STRICT VALIDATION: Must result in valid Python syntax.
    
    Args:
        card_name: The name of the card to play
        played_cards: List of cards already played
        last_was_wild: If True, validates with Python syntax
        open_paren_count: Number of currently unbalanced open parentheses
        
    Returns:
        A tuple of (can_play, reason)
    """
    if card_name not in CARDS:
        return (False, "Unknown card")
    
    card = CARDS[card_name]
    
    # Special cards can be played anytime
    if card["category"] == "SPECIAL":
        return (True, "Special cards can always be played")
    
    # Validate parenthesis balance
    if card_name == ")" and open_paren_count <= 0:
        return (False, "No open parenthesis to close")
    
    # STRICT: Always validate Python syntax
    is_valid, reason = can_form_valid_python(played_cards, card_name)
    
    if not is_valid:
        return (False, f"Invalid Python: {reason}")
    
    # Check category rules for better feedback message
    last_category = get_last_card_category(played_cards)
    can_follow_list = card.get("can_follow", [])
    
    if last_was_wild:
        return (True, "Wild card bridges syntax")
    
    if last_category == "START" and played_cards and played_cards[-1] == ":":
        if last_category in can_follow_list or "SYNTAX_COLON" in can_follow_list:
            return (True, "Valid after colon")
    
    if last_category in can_follow_list:
        last_card = played_cards[-1] if played_cards else "start"
        return (True, f"Valid after '{last_card}'")
    
    # Python validation passed even if category didn't match
    return (True, reason)


def can_insert_card_at_position(card_name: str, played_cards: List[str], position: int, 
                                  last_was_wild: bool = False) -> Tuple[bool, str]:
    """
    Check if a card can be inserted at a specific position in the sequence.
    
    For insertion at position X:
    - The card must be valid AFTER the card at position X-1 (or START if X=0)
    - The card at position X (which becomes X+1) must be valid AFTER the inserted card
    - The resulting full sequence must form valid Python
    
    Args:
        card_name: The card to insert
        played_cards: Current sequence of played cards
        position: Position to insert at (0 = beginning, len = end)
        last_was_wild: If True, category rules are relaxed
        
    Returns:
        Tuple of (can_insert, reason)
    """
    if card_name not in CARDS:
        return (False, "Unknown card")
    
    card_data = CARDS[card_name]
    
    # Special cards don't affect Python code - always valid
    if card_data["category"] == "SPECIAL":
        return (True, "Special cards can be played anytime")
    
    # Build the hypothetical new sequence
    new_sequence = played_cards[:position] + [card_name] + played_cards[position:]
    
    # Check 1: Card must be valid after what comes before it
    cards_before = played_cards[:position]
    if position == 0:
        # Inserting at start - card must be able to follow START
        if not last_was_wild and "START" not in card_data.get("can_follow", []):
            # Also check SYNTAX_COLON since START acts like post-colon
            if "SYNTAX_COLON" not in card_data.get("can_follow", []):
                return (False, f"'{card_name}' cannot start a sequence")
    else:
        # Check if card can follow the card before it
        card_before = played_cards[position - 1]
        if card_before in CARDS:
            before_category = CARDS[card_before]["category"]
            can_follow = card_data.get("can_follow", [])
            if not last_was_wild and before_category not in can_follow:
                # Special case: colon acts like START
                if card_before == ":" and "START" not in can_follow and "SYNTAX_COLON" not in can_follow:
                    return (False, f"'{card_name}' cannot follow '{card_before}'")
                elif card_before != ":":
                    return (False, f"'{card_name}' cannot follow '{card_before}'")
    
    # Check 2: If there's a card after, it must be valid after the inserted card
    if position < len(played_cards):
        card_after = played_cards[position]
        if card_after in CARDS and CARDS[card_after]["category"] != "SPECIAL":
            after_data = CARDS[card_after]
            inserted_category = card_data["category"]
            can_follow_after = after_data.get("can_follow", [])
            
            if inserted_category not in can_follow_after:
                return (False, f"'{card_after}' cannot follow '{card_name}'")
    
    # Check 3: Validate the resulting Python code
    is_valid, reason = can_form_valid_python(cards_before, card_name)
    if not is_valid:
        # Try validating the full new sequence
        code = build_python_code(new_sequence)
        syntax_valid, syntax_error = validate_python_syntax(code)
        if not syntax_valid:
            # Check if it's a valid incomplete pattern
            is_valid_pattern, pattern_reason = can_form_valid_python(
                played_cards[:position], card_name
            )
            if not is_valid_pattern:
                return (False, f"Would create invalid Python: {reason}")
    
    return (True, f"Valid insertion at position {position}")


def get_playable_cards_at_position(hand: List[str], played_cards: List[str], position: int,
                                    last_was_wild: bool = False) -> List[str]:
    """
    Get all cards from hand that can be legally inserted at a specific position.
    
    Args:
        hand: The player's hand
        played_cards: List of cards already played
        position: Position to insert at
        last_was_wild: If True, any card can follow (Wild was just played)
    """
    playable = []
    for card in hand:
        can_insert, _ = can_insert_card_at_position(card, played_cards, position, last_was_wild)
        if can_insert:
            playable.append(card)
    return playable


def get_playable_cards(hand: List[str], played_cards: List[str], last_was_wild: bool = False, open_paren_count: int = 0) -> List[str]:
    """
    Get all cards from hand that can be legally played (at the end).
    Returns a list of playable card names.
    
    Args:
        hand: The player's hand
        played_cards: List of cards already played
        last_was_wild: If True, any card can follow (Wild was just played)
        open_paren_count: Number of currently unbalanced open parentheses
    """
    # For end-of-sequence, use the insertion function with position = len
    return get_playable_cards_at_position(hand, played_cards, len(played_cards), last_was_wild)


def is_special_card(card_name: str) -> bool:
    """Check if a card is a special action card."""
    if card_name not in CARDS:
        return False
    return CARDS[card_name]["category"] == "SPECIAL"


def get_card_effect(card_name: str) -> Optional[str]:
    """Get the effect of a special card, or None if not a special card."""
    if card_name not in CARDS:
        return None
    return CARDS[card_name].get("effect")


def get_card_points(card_name: str) -> int:
    """Get the point value of a card."""
    if card_name not in CARDS:
        return 0
    return CARDS[card_name].get("points", 0)


def get_card_info(card_name: str) -> Optional[Dict[str, Any]]:
    """Get full information about a card."""
    return CARDS.get(card_name)


# =============================================================================
# GAME STATE CLASS
# =============================================================================

class GameState:
    """Manages the state of a game session."""
    
    # Game constants
    STARTING_HAND_SIZE = 7
    MAX_CONSECUTIVE_PASSES = 3
    POWER_INTERVAL = 5  # Power available every N turns
    
    # Available powers
    POWERS = {
        'peek': {
            'name': 'Peek',
            'description': "See opponent's top 3 cards for 5 seconds",
            'icon': '👁️'
        },
        'swap': {
            'name': 'Swap',
            'description': 'Exchange 2 cards from hand with deck',
            'icon': '🔄'
        },
        'mulligan': {
            'name': 'Mulligan',
            'description': 'Discard unplayable cards, draw same amount',
            'icon': '♻️'
        },
        'double_points': {
            'name': 'Double Points',
            'description': 'Next card played scores 2x points',
            'icon': '⚡'
        },
        'block': {
            'name': 'Block',
            'description': "Cancel opponent's next special card",
            'icon': '🛡️'
        }
    }
    
    def __init__(self, room_code: str):
        self.room_code = room_code
        self.players: List[str] = []
        self.player_names: Dict[str, str] = {}  # player_id: display_name
        self.hands: Dict[str, List[str]] = {}  # player_id: [cards]
        self.played_cards: List[str] = []
        self.scores: Dict[str, int] = {}  # player_id: score
        self.current_turn: int = 0  # Index in players list
        self.deck: List[str] = []
        self.game_started: bool = False
        self.game_over: bool = False
        self.winner: Optional[str] = None
        self.consecutive_passes: Dict[str, int] = {}  # player_id: pass_count
        self.last_action: Optional[Dict[str, Any]] = None
        self.turn_number: int = 0
        self.last_was_wild: bool = False  # Track if Wild card was just played
        self.open_paren_count: int = 0  # Track unbalanced parentheses
        
        # Power system
        self.power_available: Dict[str, bool] = {}  # player_id: has_power_ready
        self.active_effects: Dict[str, str] = {}    # player_id: active_effect_name
        self.turns_played: Dict[str, int] = {}      # player_id: turns_played_count
        self.power_used_this_turn: Dict[str, bool] = {}  # player_id: used_power_this_turn
        self.blocked_players: Dict[str, bool] = {}  # player_id: has_block_on_them
    
    def add_player(self, player_id: str, player_name: str = None) -> bool:
        """Add a player to the game. Returns True if successful."""
        if len(self.players) >= 2:
            return False
        if player_id in self.players:
            return False
        
        self.players.append(player_id)
        self.player_names[player_id] = player_name or f"Player {len(self.players)}"
        self.hands[player_id] = []
        self.scores[player_id] = 0
        self.consecutive_passes[player_id] = 0
        
        # Initialize power system for this player
        self.power_available[player_id] = False
        self.active_effects[player_id] = None
        self.turns_played[player_id] = 0
        self.power_used_this_turn[player_id] = False
        self.blocked_players[player_id] = False
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the game. Returns True if successful."""
        if player_id not in self.players:
            return False
        
        self.players.remove(player_id)
        self.hands.pop(player_id, None)
        self.scores.pop(player_id, None)
        self.player_names.pop(player_id, None)
        self.consecutive_passes.pop(player_id, None)
        
        # Clean up power system state
        self.power_available.pop(player_id, None)
        self.active_effects.pop(player_id, None)
        self.turns_played.pop(player_id, None)
        self.power_used_this_turn.pop(player_id, None)
        self.blocked_players.pop(player_id, None)
        return True
    
    def is_ready(self) -> bool:
        """Check if the game has 2 players and is ready to start."""
        return len(self.players) == 2
    
    def start_game(self) -> bool:
        """
        Initialize and start the game.
        Returns True if game started successfully.
        """
        if not self.is_ready():
            return False
        if self.game_started:
            return False
        
        # Create and shuffle the deck
        self.deck = shuffle_deck(create_deck())
        
        # Deal starting hands
        for player_id in self.players:
            self.hands[player_id] = draw_cards(self.deck, self.STARTING_HAND_SIZE)
        
        # Randomly determine who goes first
        self.current_turn = random.randint(0, 1)
        self.game_started = True
        self.turn_number = 1
        
        return True
    
    def get_current_player(self) -> Optional[str]:
        """Get the player ID of the current turn."""
        if not self.players:
            return None
        return self.players[self.current_turn]
    
    def get_opponent(self, player_id: str) -> Optional[str]:
        """Get the opponent's player ID."""
        if player_id not in self.players:
            return None
        for p in self.players:
            if p != player_id:
                return p
        return None
    
    def is_player_turn(self, player_id: str) -> bool:
        """Check if it's the specified player's turn."""
        return self.get_current_player() == player_id
    
    def next_turn(self) -> None:
        """Advance to the next player's turn."""
        # Get current player before advancing
        current_player = self.get_current_player()
        if current_player:
            # Increment turns played for current player
            self.turns_played[current_player] = self.turns_played.get(current_player, 0) + 1
            # Reset power used flag
            self.power_used_this_turn[current_player] = False
        
        # Advance to next player
        self.current_turn = (self.current_turn + 1) % 2
        self.turn_number += 1
        
        # Check if new current player should get a power
        new_current = self.get_current_player()
        if new_current:
            turns = self.turns_played.get(new_current, 0)
            # Power available every POWER_INTERVAL turns (5, 10, 15, etc.)
            if turns > 0 and turns % self.POWER_INTERVAL == 0:
                # Only grant if they don't already have one available
                if not self.power_available.get(new_current, False):
                    self.power_available[new_current] = True
    
    def play_card(self, player_id: str, card_name: str, position: int = None) -> Dict[str, Any]:
        """
        Attempt to play a card at a specific position.
        
        Args:
            player_id: The player attempting to play
            card_name: The name of the card to play
            position: Optional insertion position (index in played_cards). 
                      If None, appends to end.
        
        Returns a result dict with success status and any messages/effects.
        """
        result = {
            "success": False,
            "message": "",
            "effect": None,
            "points_earned": 0,
            "position": position
        }
        
        # Validate game state
        if not self.game_started:
            result["message"] = "Game has not started yet"
            return result
        
        if self.game_over:
            result["message"] = "Game is already over"
            return result
        
        if not self.is_player_turn(player_id):
            result["message"] = "It's not your turn"
            return result
        
        # Validate card is in player's hand
        if card_name not in self.hands.get(player_id, []):
            result["message"] = "You don't have that card"
            return result
        
        # Normalize position
        if position is None:
            position = len(self.played_cards)
        else:
            # Clamp position to valid range
            position = max(0, min(position, len(self.played_cards)))
        
        # Validate card can be played at the specified position
        can_insert, reason = can_insert_card_at_position(
            card_name, self.played_cards, position, self.last_was_wild
        )
        if not can_insert:
            result["message"] = reason
            return result
        
        result["position"] = position
        
        # Play the card
        self.hands[player_id].remove(card_name)
        self.consecutive_passes[player_id] = 0  # Reset pass counter
        
        # Handle special cards
        effect = get_card_effect(card_name)
        if effect:
            result["effect"] = effect
            
            # Check if player is blocked
            if self.blocked_players.get(player_id, False):
                # Cancel the special card effect
                self.blocked_players[player_id] = False
                result["message"] = f"Special card '{card_name}' was BLOCKED!"
                result["blocked"] = True
                # Reset wild flag for non-Wild special cards
                if effect != "wild":
                    self.last_was_wild = False
            else:
                effect_result = self._apply_special_effect(player_id, effect)
                result["message"] = effect_result["message"]
                # Note: _apply_special_effect sets last_was_wild for wild effect
        else:
            # Regular card - insert at specified position
            self.played_cards.insert(position, card_name)
            points = get_card_points(card_name)
            
            # Check for double points effect
            if self.active_effects.get(player_id) == 'double_points':
                points *= 2
                self.active_effects[player_id] = None  # Clear the effect
                result["double_points_used"] = True
            
            self.scores[player_id] += points
            result["points_earned"] = points
            
            # Build message based on insertion position
            if position == len(self.played_cards) - 1:
                result["message"] = f"Played '{card_name}' for {points} points"
            else:
                result["message"] = f"Inserted '{card_name}' at position {position} for {points} points"
            
            if result.get("double_points_used"):
                result["message"] += " (DOUBLE!)"
            # Reset wild flag after playing a regular card
            self.last_was_wild = False
            
            # Recalculate parenthesis balance after insertion
            self._recalculate_paren_count()
        
        # Record the action
        self.last_action = {
            "type": "play",
            "player": player_id,
            "card": card_name,
            "effect": effect,
            "position": position
        }
        
        # Check win conditions
        winner = self._check_win_conditions()
        if winner:
            self.game_over = True
            self.winner = winner
            result["message"] += f" | {self.player_names.get(winner, winner)} wins!"
        
        # Advance turn (unless skip effect was applied)
        if effect != "skip":
            self.next_turn()
        
        result["success"] = True
        return result
    
    def _recalculate_paren_count(self) -> None:
        """Recalculate the open parenthesis count from the played cards sequence."""
        self.open_paren_count = 0
        for card in self.played_cards:
            if card == "(":
                self.open_paren_count += 1
            elif card == ")":
                self.open_paren_count -= 1
    
    def _apply_special_effect(self, player_id: str, effect: str) -> Dict[str, str]:
        """Apply a special card effect. Returns result message."""
        opponent_id = self.get_opponent(player_id)
        
        if effect == "draw_2":
            self.last_was_wild = False  # Reset wild flag for non-Wild special cards
            if opponent_id and self.deck:
                drawn = draw_cards(self.deck, 2)
                self.hands[opponent_id].extend(drawn)
                return {"message": f"Opponent draws {len(drawn)} cards!"}
            return {"message": "Draw 2 played (deck empty)"}
        
        elif effect == "discard_2":
            self.last_was_wild = False  # Reset wild flag for non-Wild special cards
            if opponent_id and self.hands.get(opponent_id):
                opponent_hand = self.hands[opponent_id]
                num_discard = min(2, len(opponent_hand))
                discarded = random.sample(opponent_hand, num_discard)
                for card in discarded:
                    opponent_hand.remove(card)
                return {"message": f"Opponent discards {num_discard} cards!"}
            return {"message": "Discard 2 played (opponent has no cards)"}
        
        elif effect == "skip":
            self.last_was_wild = False  # Reset wild flag for non-Wild special cards
            return {"message": "Opponent's turn skipped!"}
        
        elif effect == "wild":
            # Wild card acts as a bridge - doesn't add to played cards
            # but sets flag so any card can follow
            self.last_was_wild = True
            return {"message": "Wild card played! Any card can follow."}
        
        return {"message": "Special effect applied"}
    
    def pass_turn(self, player_id: str) -> Dict[str, Any]:
        """
        Pass the turn (when no valid moves available).
        Returns result dict.
        """
        result = {
            "success": False,
            "message": "",
            "drew_card": None
        }
        
        if not self.game_started:
            result["message"] = "Game has not started yet"
            return result
        
        if self.game_over:
            result["message"] = "Game is already over"
            return result
        
        if not self.is_player_turn(player_id):
            result["message"] = "It's not your turn"
            return result
        
        # Check if player actually has no valid moves
        playable = get_playable_cards(self.hands.get(player_id, []), self.played_cards, self.last_was_wild, self.open_paren_count)
        if playable:
            result["message"] = "You have valid cards to play"
            return result
        
        # Draw a card if deck is not empty
        if self.deck:
            drawn = draw_cards(self.deck, 1)
            if drawn:
                self.hands[player_id].extend(drawn)
                result["drew_card"] = drawn[0]
                result["message"] = f"Drew a card: {drawn[0]}"
        
        # Increment pass counter
        self.consecutive_passes[player_id] += 1
        
        # Record action
        self.last_action = {
            "type": "pass",
            "player": player_id,
            "drew_card": result.get("drew_card")
        }
        
        # Check if player has passed too many times
        if self.consecutive_passes[player_id] >= self.MAX_CONSECUTIVE_PASSES:
            opponent_id = self.get_opponent(player_id)
            if opponent_id:
                self.game_over = True
                self.winner = opponent_id
                result["message"] += f" | {self.player_names.get(opponent_id, 'Opponent')} wins (opponent couldn't play)!"
        
        # Check other win conditions
        winner = self._check_win_conditions()
        if winner and not self.game_over:
            self.game_over = True
            self.winner = winner
        
        self.next_turn()
        result["success"] = True
        return result
    
    def use_power(self, player_id: str, power_name: str) -> Dict[str, Any]:
        """
        Use a special power.
        Returns result dict with success status and any data.
        """
        result = {
            "success": False,
            "message": "",
            "power": power_name,
            "data": {}
        }
        
        # Validate game state
        if not self.game_started:
            result["message"] = "Game has not started yet"
            return result
        
        if self.game_over:
            result["message"] = "Game is already over"
            return result
        
        if not self.is_player_turn(player_id):
            result["message"] = "It's not your turn"
            return result
        
        # Check if player has power available
        if not self.power_available.get(player_id, False):
            result["message"] = "No power available"
            return result
        
        # Check if already used power this turn
        if self.power_used_this_turn.get(player_id, False):
            result["message"] = "Already used a power this turn"
            return result
        
        # Validate power name
        if power_name not in self.POWERS:
            result["message"] = "Invalid power"
            return result
        
        opponent_id = self.get_opponent(player_id)
        
        # Apply the power effect
        if power_name == 'peek':
            # Show opponent's first 3 cards (from the top of their hand)
            if opponent_id and self.hands.get(opponent_id):
                opponent_hand = self.hands[opponent_id]
                peeked_cards = opponent_hand[:3]  # First 3 cards
                result["data"]["peeked_cards"] = peeked_cards
                result["message"] = f"Peeking at opponent's cards!"
            else:
                result["message"] = "Opponent has no cards to peek at"
                
        elif power_name == 'swap':
            # Exchange 2 cards from hand with deck
            player_hand = self.hands.get(player_id, [])
            if len(player_hand) >= 2 and len(self.deck) >= 2:
                # Pick 2 random cards from hand to swap
                import random
                cards_to_swap = random.sample(player_hand, 2)
                for card in cards_to_swap:
                    player_hand.remove(card)
                    self.deck.append(card)
                
                # Shuffle and draw 2 new cards
                random.shuffle(self.deck)
                new_cards = draw_cards(self.deck, 2)
                player_hand.extend(new_cards)
                
                result["data"]["swapped_out"] = cards_to_swap
                result["data"]["swapped_in"] = new_cards
                result["message"] = f"Swapped 2 cards with the deck!"
            else:
                result["message"] = "Not enough cards to swap"
                return result
                
        elif power_name == 'mulligan':
            # Discard unplayable cards, draw same amount
            player_hand = self.hands.get(player_id, [])
            playable = get_playable_cards(player_hand, self.played_cards, self.last_was_wild, self.open_paren_count)
            unplayable = [c for c in player_hand if c not in playable]
            
            if unplayable and self.deck:
                # Remove unplayable cards
                for card in unplayable:
                    player_hand.remove(card)
                
                # Draw same number of new cards
                new_cards = draw_cards(self.deck, len(unplayable))
                player_hand.extend(new_cards)
                
                result["data"]["discarded"] = unplayable
                result["data"]["drawn"] = new_cards
                result["message"] = f"Discarded {len(unplayable)} unplayable cards and drew new ones!"
            else:
                if not unplayable:
                    result["message"] = "All your cards are playable!"
                else:
                    result["message"] = "Deck is empty"
                return result
                
        elif power_name == 'double_points':
            # Next card scores 2x
            self.active_effects[player_id] = 'double_points'
            result["data"]["effect_active"] = True
            result["message"] = "Double Points activated! Next card scores 2x!"
            
        elif power_name == 'block':
            # Block opponent's next special card
            if opponent_id:
                self.blocked_players[opponent_id] = True
                result["data"]["blocked_player"] = opponent_id
                result["message"] = "Block activated! Opponent's next special card will be cancelled!"
            else:
                result["message"] = "No opponent to block"
                return result
        
        # Mark power as used
        self.power_available[player_id] = False
        self.power_used_this_turn[player_id] = True
        
        # Record action
        self.last_action = {
            "type": "power",
            "player": player_id,
            "power": power_name
        }
        
        result["success"] = True
        return result
    
    def _check_win_conditions(self) -> Optional[str]:
        """
        Check all win conditions.
        Returns the winner's player_id or None.
        
        Primary win condition: Deck depletes - highest score wins.
        Tie-breaker: Player with fewer cards in hand wins.
        """
        # Primary win condition: Deck is depleted
        if not self.deck:
            # Both players may still have cards - highest score wins
            scores = [(pid, self.scores.get(pid, 0)) for pid in self.players]
            scores.sort(key=lambda x: x[1], reverse=True)
            
            if scores[0][1] != scores[1][1]:
                # Not a tie - highest score wins
                return scores[0][0]
            
            # Tie-breaker: fewer cards in hand wins
            hand_sizes = [(pid, len(self.hands.get(pid, []))) for pid in self.players]
            hand_sizes.sort(key=lambda x: x[1])  # Sort ascending (fewer cards first)
            
            if hand_sizes[0][1] != hand_sizes[1][1]:
                # Different hand sizes - fewer cards wins
                return hand_sizes[0][0]
            
            # Perfect tie - first player in list wins (arbitrary but deterministic)
            return self.players[0]
        
        return None
    
    def get_game_state_for_player(self, player_id: str) -> Dict[str, Any]:
        """
        Get the game state formatted for a specific player.
        Hides opponent's actual cards.
        """
        opponent_id = self.get_opponent(player_id)
        
        # Calculate turns until next power
        turns_played = self.turns_played.get(player_id, 0)
        turns_until_power = self.POWER_INTERVAL - (turns_played % self.POWER_INTERVAL)
        if turns_until_power == self.POWER_INTERVAL and turns_played > 0:
            turns_until_power = 0  # Power is ready
        
        # Get syntax validation info for the current played cards
        syntax_info = get_syntax_validation_info(self.played_cards)
        
        return {
            "room_code": self.room_code,
            "game_started": self.game_started,
            "game_over": self.game_over,
            "winner": self.winner,
            "winner_name": self.player_names.get(self.winner) if self.winner else None,
            "turn_number": self.turn_number,
            "current_player": self.get_current_player(),
            "is_your_turn": self.is_player_turn(player_id),
            "your_hand": self.hands.get(player_id, []),
            "your_score": self.scores.get(player_id, 0),
            "opponent_card_count": len(self.hands.get(opponent_id, [])) if opponent_id else 0,
            "opponent_score": self.scores.get(opponent_id, 0) if opponent_id else 0,
            "opponent_name": self.player_names.get(opponent_id, "Opponent") if opponent_id else None,
            "your_name": self.player_names.get(player_id, "You"),
            "played_cards": self.played_cards.copy(),
            "last_played_card": self.played_cards[-1] if self.played_cards else None,
            "deck_remaining": len(self.deck),
            "playable_cards": get_playable_cards(self.hands.get(player_id, []), self.played_cards, self.last_was_wild, self.open_paren_count),
            "last_action": self.last_action,
            "players_ready": len(self.players),
            "last_was_wild": self.last_was_wild,
            "open_paren_count": self.open_paren_count,
            # Power system
            "power_available": self.power_available.get(player_id, False),
            "active_effect": self.active_effects.get(player_id),
            "turns_played": turns_played,
            "turns_until_power": turns_until_power,
            "is_blocked": self.blocked_players.get(player_id, False),
            "powers": self.POWERS,  # Send power definitions
            # Syntax validation info
            "syntax_info": {
                "python_code": syntax_info["code"],
                "formatted_code": syntax_info["formatted_code"],
                "code_structure": syntax_info["code_structure"],
                "is_valid_python": syntax_info["is_valid"],
                "is_complete": syntax_info["is_complete"],
                "syntax_error": syntax_info["error"],
                "suggested_categories": syntax_info["suggestions"]
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary (for debugging/admin)."""
        return {
            "room_code": self.room_code,
            "players": self.players,
            "player_names": self.player_names,
            "hands": self.hands,
            "played_cards": self.played_cards,
            "scores": self.scores,
            "current_turn": self.current_turn,
            "deck_size": len(self.deck),
            "game_started": self.game_started,
            "game_over": self.game_over,
            "winner": self.winner,
            "turn_number": self.turn_number,
            "last_was_wild": self.last_was_wild,
            "open_paren_count": self.open_paren_count,
            "power_available": self.power_available,
            "active_effects": self.active_effects,
            "turns_played": self.turns_played,
            "blocked_players": self.blocked_players
        }


# =============================================================================
# GAME ROOM MANAGEMENT
# =============================================================================

# Game rooms storage (in-memory)
game_rooms: Dict[str, GameState] = {}


def generate_room_code() -> str:
    """Generate a unique 6-character room code."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Removed confusing chars (I,O,0,1)
    while True:
        code = ''.join(random.choices(chars, k=6))
        if code not in game_rooms:
            return code


def create_room(room_code: str = None) -> GameState:
    """Create a new game room. Auto-generates code if not provided."""
    if room_code is None:
        room_code = generate_room_code()
    game_rooms[room_code] = GameState(room_code)
    return game_rooms[room_code]


def get_room(room_code: str) -> Optional[GameState]:
    """Get an existing game room."""
    return game_rooms.get(room_code)


def delete_room(room_code: str) -> bool:
    """Delete a game room. Returns True if successful."""
    if room_code in game_rooms:
        del game_rooms[room_code]
        return True
    return False


def get_all_rooms() -> Dict[str, GameState]:
    """Get all active game rooms."""
    return game_rooms


def cleanup_empty_rooms() -> int:
    """Remove rooms with no players. Returns count of removed rooms."""
    empty_rooms = [code for code, room in game_rooms.items() if not room.players]
    for code in empty_rooms:
        del game_rooms[code]
    return len(empty_rooms)


# =============================================================================
# BOT PLAYER CLASS
# =============================================================================

class BotPlayer:
    """
    AI Bot opponent for single-player mode.
    Supports three difficulty levels: easy, medium, hard.
    """
    
    # Bot difficulty settings
    DIFFICULTIES = {
        'easy': {
            'name': 'Easy',
            'description': 'Random valid card selection',
            'think_time': (1.0, 2.0)  # Min/max seconds to "think"
        },
        'medium': {
            'name': 'Medium', 
            'description': 'Prioritizes high-point cards',
            'think_time': (1.5, 2.5)
        },
        'hard': {
            'name': 'Hard',
            'description': 'Strategic play with combos and blocking',
            'think_time': (2.0, 3.0)
        }
    }
    
    def __init__(self, difficulty: str = 'medium'):
        """
        Initialize a bot player.
        
        Args:
            difficulty: 'easy', 'medium', or 'hard'
        """
        if difficulty not in self.DIFFICULTIES:
            difficulty = 'medium'
        self.difficulty = difficulty
        self.player_id = 'BOT_' + generate_room_code()[:4]
        self.name = f"Bot ({self.DIFFICULTIES[difficulty]['name']})"
    
    def get_think_time(self) -> float:
        """Get a random thinking time based on difficulty."""
        min_time, max_time = self.DIFFICULTIES[self.difficulty]['think_time']
        return random.uniform(min_time, max_time)
    
    def choose_card(self, hand: List[str], playable: List[str], 
                    game_state: Dict[str, Any]) -> Optional[str]:
        """
        Choose a card to play based on difficulty level.
        
        Args:
            hand: Bot's current hand
            playable: List of playable cards from hand
            game_state: Current game state dictionary
            
        Returns:
            Card name to play, or None if bot should pass
        """
        if not playable:
            return None
        
        if self.difficulty == 'easy':
            return self._easy_choice(playable)
        elif self.difficulty == 'medium':
            return self._medium_choice(hand, playable, game_state)
        else:  # hard
            return self._hard_choice(hand, playable, game_state)
    
    def _easy_choice(self, playable: List[str]) -> str:
        """Easy: Just pick a random playable card."""
        return random.choice(playable)
    
    def _medium_choice(self, hand: List[str], playable: List[str], 
                       game_state: Dict[str, Any]) -> str:
        """Medium: Prioritize high-point cards, use specials randomly."""
        # Separate special cards from regular cards
        special_cards = [c for c in playable if is_special_card(c)]
        regular_cards = [c for c in playable if not is_special_card(c)]
        
        # 30% chance to use a special card if available
        if special_cards and random.random() < 0.3:
            return random.choice(special_cards)
        
        # Otherwise, pick the highest point card
        if regular_cards:
            return max(regular_cards, key=lambda c: CARDS[c]['points'])
        
        # Fallback to any playable card
        return random.choice(playable)
    
    def _hard_choice(self, hand: List[str], playable: List[str],
                     game_state: Dict[str, Any]) -> str:
        """
        Hard: Strategic play.
        - Saves high-value cards for combos
        - Uses special cards strategically
        - Considers game state
        """
        special_cards = [c for c in playable if is_special_card(c)]
        regular_cards = [c for c in playable if not is_special_card(c)]
        
        # Get game state info
        my_score = game_state.get('your_score', 0)
        opp_score = game_state.get('opponent_score', 0)
        deck_remaining = game_state.get('deck_remaining', 0)
        opp_card_count = game_state.get('opponent_card_count', 0)
        
        # Strategic use of special cards
        if special_cards:
            # If opponent is ahead and game is ending, use offensive specials
            if opp_score > my_score and deck_remaining < 15:
                for card in special_cards:
                    effect = get_card_effect(card)
                    if effect in ['discard_2', 'skip']:
                        return card
            
            # If opponent has few cards, make them draw
            if opp_card_count <= 3:
                for card in special_cards:
                    if get_card_effect(card) == 'draw_2':
                        return card
            
            # Use Wild card to enable better plays
            wild_cards = [c for c in special_cards if get_card_effect(c) == 'wild']
            if wild_cards:
                # Check if we have high-value cards that can't currently be played
                unplayable_high = [c for c in hand if c not in playable 
                                  and not is_special_card(c) 
                                  and CARDS.get(c, {}).get('points', 0) >= 2]
                if unplayable_high and random.random() < 0.6:
                    return wild_cards[0]
        
        # For regular cards, consider building sequences
        if regular_cards:
            # Categorize by points
            high_value = [c for c in regular_cards if CARDS[c]['points'] >= 3]
            medium_value = [c for c in regular_cards if CARDS[c]['points'] == 2]
            low_value = [c for c in regular_cards if CARDS[c]['points'] <= 1]
            
            # Early game: play low-value cards to save high-value for later
            if deck_remaining > 30:
                if low_value:
                    return random.choice(low_value)
                elif medium_value:
                    return random.choice(medium_value)
            
            # Mid/late game: play high-value cards
            if high_value:
                return random.choice(high_value)
            elif medium_value:
                return random.choice(medium_value)
            elif low_value:
                return random.choice(low_value)
        
        # Fallback: random choice
        return random.choice(playable)
    
    def should_use_power(self, game_state: Dict[str, Any]) -> Optional[str]:
        """
        Decide whether to use a power and which one.
        
        Returns:
            Power name to use, or None
        """
        if not game_state.get('power_available', False):
            return None
        
        my_score = game_state.get('your_score', 0)
        opp_score = game_state.get('opponent_score', 0)
        deck_remaining = game_state.get('deck_remaining', 0)
        playable = game_state.get('playable_cards', [])
        
        if self.difficulty == 'easy':
            # Easy bot rarely uses powers
            if random.random() < 0.3:
                return random.choice(['peek', 'swap', 'mulligan', 'double_points', 'block'])
            return None
        
        elif self.difficulty == 'medium':
            # Medium bot uses powers somewhat strategically
            if len(playable) == 0:
                return 'mulligan'  # Can't play? Mulligan!
            if random.random() < 0.5:
                return random.choice(['double_points', 'swap', 'block'])
            return None
        
        else:  # hard
            # Hard bot uses powers very strategically
            
            # If behind on score, use double_points on next high-value card
            high_value_playable = [c for c in playable if CARDS.get(c, {}).get('points', 0) >= 2]
            if opp_score > my_score + 5 and high_value_playable:
                return 'double_points'
            
            # If no playable cards, mulligan
            if len(playable) == 0:
                return 'mulligan'
            
            # Block opponent if they might have special cards (late game)
            if deck_remaining < 20:
                return 'block'
            
            # Swap if hand is bad (few playable cards)
            if len(playable) <= 2:
                return 'swap'
            
            return None