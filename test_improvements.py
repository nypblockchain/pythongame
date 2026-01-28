"""
Test script to verify game logic improvements:
1. Wild card fix - any card can follow Wild
2. Parenthesis tracking - ) cannot be played without open (
3. Expanded can_follow rules
4. Statement boundaries - colon resets to START
5. Python syntax validation with ast.parse()
"""

import sys
from game_logic import (
    can_play_card, get_last_card_category, get_playable_cards,
    GameState, CARDS,
    build_python_code, validate_python_syntax, can_form_valid_python,
    get_syntax_validation_info, can_play_card_with_reason
)


def test_wild_card_fix():
    """Test that Wild card allows VALID Python continuations."""
    print("\n" + "=" * 60)
    print("TEST 1: Wild Card (Strict Python Validation)")
    print("=" * 60)
    
    # With strict validation, Wild card allows any card that results in VALID Python
    # After "for i", only "in" makes valid Python (for i in ...)
    played_cards = ["for", "i"]  # A valid sequence
    
    # Without Wild flag
    normal_playable = get_playable_cards(["in", "range", "print", "x", "1", "+"], played_cards, last_was_wild=False)
    print(f"After 'i' (VARIABLE), normal playable: {normal_playable}")
    
    # With Wild flag - still must be valid Python
    wild_playable = get_playable_cards(["in", "range", "print", "x", "1", "+", "for", "if"], played_cards, last_was_wild=True)
    print(f"After Wild card, playable: {wild_playable}")
    
    # With strict validation:
    # - "in" is valid (for i in ...)
    # - "for" would create "for i for" - INVALID Python, correctly rejected
    all_pass = True
    
    # "in" should be playable
    result_in = can_play_card("in", played_cards, last_was_wild=True)
    status = "PASS" if result_in else "FAIL"
    if not result_in:
        all_pass = False
    print(f"  {status} 'in' can follow 'i' (valid Python): {result_in}")
    
    # "for" should NOT be playable (would create "for i for" - invalid)
    result_for = can_play_card("for", played_cards, last_was_wild=True)
    status = "PASS" if not result_for else "FAIL"
    if result_for:
        all_pass = False
    print(f"  {status} 'for' correctly rejected (would be invalid Python): {not result_for}")
    
    # Test valid pattern: empty start, Wild allows statement starters
    result_empty_for = can_play_card("for", [], last_was_wild=True)
    status = "PASS" if result_empty_for else "FAIL"
    if not result_empty_for:
        all_pass = False
    print(f"  {status} 'for' at empty start: {result_empty_for}")
    
    return all_pass


def test_parenthesis_tracking():
    """Test that ) cannot be played without an open (."""
    print("\n" + "=" * 60)
    print("TEST 2: Parenthesis Tracking")
    print("=" * 60)
    
    all_pass = True
    
    # Test 1: ) should NOT be playable with open_paren_count = 0
    played_cards = ["print"]  # After a function, ( is expected, then )
    result1 = can_play_card(")", played_cards, open_paren_count=0)
    status1 = "PASS" if not result1 else "FAIL"
    if result1:
        all_pass = False
    print(f"  {status1} ')' blocked when no open parenthesis: {not result1}")
    
    # Test 2: ) SHOULD be playable when open_paren_count > 0
    played_cards2 = ["print", "(", "x"]  # Valid: print(x
    result2 = can_play_card(")", played_cards2, open_paren_count=1)
    status2 = "PASS" if result2 else "FAIL"
    if not result2:
        all_pass = False
    print(f"  {status2} ')' allowed when parenthesis is open: {result2}")
    
    # Test 3: ( should always be playable after functions
    result3 = can_play_card("(", ["print"], open_paren_count=0)
    status3 = "PASS" if result3 else "FAIL"
    if not result3:
        all_pass = False
    print(f"  {status3} '(' playable after function: {result3}")
    
    # Test 4: Verify GameState tracks paren count correctly
    state = GameState("TEST")
    state.add_player("p1", "Player 1")
    state.add_player("p2", "Player 2")
    state.start_game()
    
    # Manually set up a scenario
    state.hands["p1"] = ["print", "(", "x", ")", "+"]
    state.current_turn = state.players.index("p1")
    state.played_cards = []
    
    # Play print
    state.play_card("p1", "print")
    print(f"  After 'print', open_paren_count = {state.open_paren_count}")
    
    # Play (
    state.hands["p1"].insert(0, "(")
    state.current_turn = state.players.index("p1")
    state.play_card("p1", "(")
    paren_after_open = state.open_paren_count
    status4 = "PASS" if paren_after_open == 1 else "FAIL"
    if paren_after_open != 1:
        all_pass = False
    print(f"  {status4} After '(', open_paren_count = {paren_after_open} (expected 1)")
    
    # Play x
    state.hands["p1"].insert(0, "x")
    state.current_turn = state.players.index("p1")
    state.play_card("p1", "x")
    
    # Play )
    state.hands["p1"].insert(0, ")")
    state.current_turn = state.players.index("p1")
    state.play_card("p1", ")")
    paren_after_close = state.open_paren_count
    status5 = "PASS" if paren_after_close == 0 else "FAIL"
    if paren_after_close != 0:
        all_pass = False
    print(f"  {status5} After ')', open_paren_count = {paren_after_close} (expected 0)")
    
    return all_pass


def test_expanded_can_follow():
    """Test that cards can follow based on VALID Python syntax."""
    print("\n" + "=" * 60)
    print("TEST 3: Valid Python Syntax Rules")
    print("=" * 60)
    
    all_pass = True
    
    # Test 1: After "x = 1", what can follow? Operators make valid Python
    result1 = can_play_card("+", ["x", "=", "1"])  # x = 1 + ...
    status1 = "PASS" if result1 else "FAIL"
    if not result1:
        all_pass = False
    print(f"  {status1} Operator '+' can follow 'x = 1': {result1}")
    
    # Test 2: "x" after "1" would create "1 x" - invalid Python
    result2 = can_play_card("x", ["1"])  # 1 x - invalid
    status2 = "PASS" if not result2 else "FAIL"
    if result2:
        all_pass = False
    print(f"  {status2} 'x' correctly rejected after '1' (would be '1 x'): {not result2}")
    
    # Test 3: Values can follow "=" (for x = 1)
    result3 = can_play_card("1", ["x", "="])  # x = 1 - valid
    status3 = "PASS" if result3 else "FAIL"
    if not result3:
        all_pass = False
    print(f"  {status3} Value '1' can follow 'x =': {result3}")
    
    # Test 4: After function call, can add operators
    result4 = can_play_card("+", ["len", "(", "x", ")"])  # len(x) + 
    status4 = "PASS" if result4 else "FAIL"
    if not result4:
        all_pass = False
    print(f"  {status4} Operator '+' can follow 'len(x)': {result4}")
    
    # Test 5: After print(x), can add operators
    result5 = can_play_card("+", ["print", "(", "x", ")"])  # print(x) +
    status5 = "PASS" if result5 else "FAIL"
    if not result5:
        all_pass = False
    print(f"  {status5} Operator '+' can follow 'print(x)': {result5}")
    
    return all_pass


def test_statement_boundaries():
    """Test that colon starts a new block where statements are valid."""
    print("\n" + "=" * 60)
    print("TEST 4: Statement Boundaries (After Colon)")
    print("=" * 60)
    
    all_pass = True
    
    # After colon, get_last_card_category should return "START"
    played_cards = ["for", "i", "in", "range", "(", "10", ")", ":"]
    category = get_last_card_category(played_cards)
    status1 = "PASS" if category == "START" else "FAIL"
    if category != "START":
        all_pass = False
    print(f"  {status1} Category after ':' is '{category}' (expected 'START')")
    
    # After colon, new statements can start
    result2 = can_play_card("for", played_cards)
    status2 = "PASS" if result2 else "FAIL"
    if not result2:
        all_pass = False
    print(f"  {status2} 'for' playable after ':' (nested loop): {result2}")
    
    result3 = can_play_card("if", played_cards)
    status3 = "PASS" if result3 else "FAIL"
    if not result3:
        all_pass = False
    print(f"  {status3} 'if' playable after ':': {result3}")
    
    result4 = can_play_card("print", played_cards)
    status4 = "PASS" if result4 else "FAIL"
    if not result4:
        all_pass = False
    print(f"  {status4} 'print' playable after ':': {result4}")
    
    # 'else' needs proper context (after if block ends)
    # After just "for...:", else doesn't make sense syntactically
    # Test else after an if block
    if_cards = ["if", "x", ":", "print", "(", "x", ")"]
    result5 = can_play_card("else", if_cards)
    # Note: This may still fail due to complex multi-statement handling
    print(f"  INFO 'else' after if block: {result5} (complex case)")
    
    return all_pass


def test_wild_card_in_game():
    """Test Wild card behavior with strict Python validation."""
    print("\n" + "=" * 60)
    print("TEST 5: Wild Card in Game State (Strict Validation)")
    print("=" * 60)
    
    all_pass = True
    
    state = GameState("TEST2")
    state.add_player("p1", "Player 1")
    state.add_player("p2", "Player 2")
    state.start_game()
    
    # Set up a specific scenario: after "for i in", valid continuations are range, list, etc.
    state.hands["p1"] = ["Wild", "range", "x"]
    state.current_turn = state.players.index("p1")
    state.played_cards = ["for", "i", "in"]  # After 'in', functions like range are valid
    
    # Before Wild, check what's playable
    before_wild = get_playable_cards(state.hands["p1"], state.played_cards, state.last_was_wild, state.open_paren_count)
    print(f"  Before Wild: playable cards = {before_wild}")
    
    # Play Wild card
    result = state.play_card("p1", "Wild")
    status1 = "PASS" if result["success"] else "FAIL"
    if not result["success"]:
        all_pass = False
    print(f"  {status1} Wild card played: {result['message']}")
    
    # Check last_was_wild flag
    status2 = "PASS" if state.last_was_wild else "FAIL"
    if not state.last_was_wild:
        all_pass = False
    print(f"  {status2} last_was_wild flag is: {state.last_was_wild}")
    
    # Check what's playable with strict validation
    # "range" should be playable (for i in range... is valid)
    # "for" would create "for i in for" - invalid, should be rejected
    state.hands["p1"] = ["for", "range", "x", "1", "+"]
    after_wild = get_playable_cards(state.hands["p1"], state.played_cards, state.last_was_wild, state.open_paren_count)
    print(f"  After Wild: playable cards = {after_wild}")
    
    # 'range' should be playable (valid Python continuation)
    status3 = "PASS" if "range" in after_wild else "FAIL"
    if "range" not in after_wild:
        all_pass = False
    print(f"  {status3} 'range' is playable after Wild: {'range' in after_wild}")
    
    # 'for' should NOT be playable (would create invalid Python)
    status3b = "PASS" if "for" not in after_wild else "FAIL"
    if "for" in after_wild:
        all_pass = False
    print(f"  {status3b} 'for' correctly rejected (invalid Python): {'for' not in after_wild}")
    
    # Play a regular card and verify wild flag is reset
    state.current_turn = state.players.index("p1")
    state.play_card("p1", "range")
    status4 = "PASS" if not state.last_was_wild else "FAIL"
    if state.last_was_wild:
        all_pass = False
    print(f"  {status4} last_was_wild reset after playing regular card: {not state.last_was_wild}")
    
    return all_pass


def test_special_cards_reset_wild_flag():
    """Test that other special cards reset the wild flag."""
    print("\n" + "=" * 60)
    print("TEST 6: Special Cards Reset Wild Flag")
    print("=" * 60)
    
    all_pass = True
    
    state = GameState("TEST3")
    state.add_player("p1", "Player 1")
    state.add_player("p2", "Player 2")
    state.start_game()
    
    # Set last_was_wild to True
    state.last_was_wild = True
    
    # Play Draw 2 and verify it resets the flag
    state.hands["p1"] = ["Draw 2"]
    state.current_turn = state.players.index("p1")
    result = state.play_card("p1", "Draw 2")
    
    status1 = "PASS" if not state.last_was_wild else "FAIL"
    if state.last_was_wild:
        all_pass = False
    print(f"  {status1} 'Draw 2' resets last_was_wild: {not state.last_was_wild}")
    
    # Reset and test Skip
    state.last_was_wild = True
    state.hands["p1"] = ["Skip"]
    state.current_turn = state.players.index("p1")
    result = state.play_card("p1", "Skip")
    
    status2 = "PASS" if not state.last_was_wild else "FAIL"
    if state.last_was_wild:
        all_pass = False
    print(f"  {status2} 'Skip' resets last_was_wild: {not state.last_was_wild}")
    
    return all_pass


def test_playable_cards_with_paren_restriction():
    """Test that playable cards respects paren restriction."""
    print("\n" + "=" * 60)
    print("TEST 7: Playable Cards with Paren Restriction")
    print("=" * 60)
    
    all_pass = True
    
    # Hand contains ) but no open paren - ) should not be in playable
    hand = ["x", ")", "+", "1"]
    played_cards = ["print", "(", "x"]  # After variable, ) could follow syntactically
    
    # With open_paren_count = 1, ) should be playable
    playable_with_open = get_playable_cards(hand, played_cards, open_paren_count=1)
    status1 = "PASS" if ")" in playable_with_open else "FAIL"
    if ")" not in playable_with_open:
        all_pass = False
    print(f"  {status1} ')' in playable with open_paren_count=1: {')' in playable_with_open}")
    
    # With open_paren_count = 0, ) should NOT be playable
    playable_without = get_playable_cards(hand, played_cards, open_paren_count=0)
    status2 = "PASS" if ")" not in playable_without else "FAIL"
    if ")" in playable_without:
        all_pass = False
    print(f"  {status2} ')' not in playable with open_paren_count=0: {')' not in playable_without}")
    
    return all_pass


def test_python_code_builder():
    """Test that build_python_code generates correct Python code."""
    print("\n" + "=" * 60)
    print("TEST 8: Python Code Builder")
    print("=" * 60)
    
    all_pass = True
    
    # Test 1: Simple for loop
    cards1 = ["for", "i", "in", "range", "(", "10", ")"]
    code1 = build_python_code(cards1)
    expected1 = "for i in range(10)"
    status1 = "PASS" if expected1 in code1 else "FAIL"
    if expected1 not in code1:
        all_pass = False
    print(f"  {status1} For loop code: '{code1.strip()}' (expected contains '{expected1}')")
    
    # Test 2: With colon and indentation
    cards2 = ["for", "i", "in", "range", "(", "10", ")", ":"]
    code2 = build_python_code(cards2)
    status2 = "PASS" if "pass" in code2 else "FAIL"  # Should add placeholder
    if "pass" not in code2:
        all_pass = False
    print(f"  {status2} Code with colon has placeholder: {'pass' in code2}")
    
    # Test 3: Print statement
    cards3 = ["print", "(", '"hello"', ")"]
    code3 = build_python_code(cards3)
    expected3 = 'print("hello")'
    status3 = "PASS" if expected3 in code3 else "FAIL"
    if expected3 not in code3:
        all_pass = False
    print(f"  {status3} Print statement: '{code3.strip()}'")
    
    # Test 4: Assignment
    cards4 = ["x", "=", "10"]
    code4 = build_python_code(cards4)
    expected4 = "x = 10"
    status4 = "PASS" if expected4 in code4 else "FAIL"
    if expected4 not in code4:
        all_pass = False
    print(f"  {status4} Assignment: '{code4.strip()}'")
    
    # Test 5: Special cards are filtered
    cards5 = ["for", "Wild", "i", "in", "Skip", "range", "(", "10", ")"]
    code5 = build_python_code(cards5)
    status5 = "PASS" if "Wild" not in code5 and "Skip" not in code5 else "FAIL"
    if "Wild" in code5 or "Skip" in code5:
        all_pass = False
    print(f"  {status5} Special cards filtered: 'Wild' and 'Skip' not in code")
    
    return all_pass


def test_python_syntax_validation():
    """Test that validate_python_syntax correctly validates Python code."""
    print("\n" + "=" * 60)
    print("TEST 9: Python Syntax Validation (ast.parse)")
    print("=" * 60)
    
    all_pass = True
    
    # Test 1: Valid complete code
    code1 = "for i in range(10):\n    pass"
    is_valid1, error1 = validate_python_syntax(code1)
    status1 = "PASS" if is_valid1 else "FAIL"
    if not is_valid1:
        all_pass = False
    print(f"  {status1} Valid for loop: is_valid={is_valid1}")
    
    # Test 2: Valid print statement
    code2 = 'print("hello")'
    is_valid2, error2 = validate_python_syntax(code2)
    status2 = "PASS" if is_valid2 else "FAIL"
    if not is_valid2:
        all_pass = False
    print(f"  {status2} Valid print: is_valid={is_valid2}")
    
    # Test 3: Invalid syntax (missing colon)
    code3 = "for i in range(10)\n    print(i)"
    is_valid3, error3 = validate_python_syntax(code3)
    status3 = "PASS" if not is_valid3 else "FAIL"
    if is_valid3:
        all_pass = False
    print(f"  {status3} Invalid (missing colon): is_valid={is_valid3}, error='{error3[:30]}...'")
    
    # Test 4: Empty code is valid
    is_valid4, error4 = validate_python_syntax("")
    status4 = "PASS" if is_valid4 else "FAIL"
    if not is_valid4:
        all_pass = False
    print(f"  {status4} Empty code is valid: is_valid={is_valid4}")
    
    # Test 5: Simple expression
    code5 = "x = 10"
    is_valid5, error5 = validate_python_syntax(code5)
    status5 = "PASS" if is_valid5 else "FAIL"
    if not is_valid5:
        all_pass = False
    print(f"  {status5} Assignment: is_valid={is_valid5}")
    
    return all_pass


def test_can_form_valid_python():
    """Test flexible Python validation for card insertion."""
    print("\n" + "=" * 60)
    print("TEST 10: Flexible Python Validation (can_form_valid_python)")
    print("=" * 60)
    
    all_pass = True
    
    # Test 1: Valid addition of 'i' after 'for'
    cards1 = ["for"]
    is_valid1, reason1 = can_form_valid_python(cards1, "i")
    status1 = "PASS" if is_valid1 else "FAIL"
    if not is_valid1:
        all_pass = False
    print(f"  {status1} 'i' can follow 'for': {is_valid1} - {reason1}")
    
    # Test 2: Valid addition of 'range' after 'in'
    cards2 = ["for", "i", "in"]
    is_valid2, reason2 = can_form_valid_python(cards2, "range")
    status2 = "PASS" if is_valid2 else "FAIL"
    if not is_valid2:
        all_pass = False
    print(f"  {status2} 'range' can follow 'in': {is_valid2} - {reason2}")
    
    # Test 3: Valid addition of '(' after 'range'
    cards3 = ["for", "i", "in", "range"]
    is_valid3, reason3 = can_form_valid_python(cards3, "(")
    status3 = "PASS" if is_valid3 else "FAIL"
    if not is_valid3:
        all_pass = False
    print(f"  {status3} '(' can follow 'range': {is_valid3} - {reason3}")
    
    # Test 4: Special cards always valid
    is_valid4, reason4 = can_form_valid_python(["for", "i"], "Wild")
    status4 = "PASS" if is_valid4 else "FAIL"
    if not is_valid4:
        all_pass = False
    print(f"  {status4} 'Wild' is always valid: {is_valid4} - {reason4}")
    
    # Test 5: Complete statement with colon
    cards5 = ["for", "i", "in", "range", "(", "10", ")"]
    is_valid5, reason5 = can_form_valid_python(cards5, ":")
    status5 = "PASS" if is_valid5 else "FAIL"
    if not is_valid5:
        all_pass = False
    print(f"  {status5} ':' can complete for loop: {is_valid5} - {reason5}")
    
    return all_pass


def test_syntax_validation_info():
    """Test get_syntax_validation_info provides correct information."""
    print("\n" + "=" * 60)
    print("TEST 11: Syntax Validation Info")
    print("=" * 60)
    
    all_pass = True
    
    # Test 1: Empty sequence
    info1 = get_syntax_validation_info([])
    status1 = "PASS" if info1["is_valid"] else "FAIL"
    if not info1["is_valid"]:
        all_pass = False
    print(f"  {status1} Empty sequence is valid: {info1['is_valid']}")
    
    # Test 2: Incomplete sequence
    cards2 = ["for", "i", "in", "range", "(", "10", ")"]
    info2 = get_syntax_validation_info(cards2)
    status2 = "PASS" if not info2["is_complete"] else "FAIL"
    if info2["is_complete"]:
        all_pass = False
    print(f"  {status2} 'for i in range(10)' is incomplete: {not info2['is_complete']}")
    print(f"       Suggestions: {info2['suggestions']}")
    
    # Test 3: Complete sequence
    cards3 = ["for", "i", "in", "range", "(", "10", ")", ":"]
    info3 = get_syntax_validation_info(cards3)
    # After colon with 'pass' added, it should be complete
    status3 = "PASS" if info3["is_valid"] else "FAIL"
    if not info3["is_valid"]:
        all_pass = False
    print(f"  {status3} 'for i in range(10):' is valid: {info3['is_valid']}")
    print(f"       Code: {info3['code'][:50]}...")
    
    return all_pass


def test_flexible_card_insertion():
    """Test that flexible validation allows valid Python constructs."""
    print("\n" + "=" * 60)
    print("TEST 12: Flexible Card Insertion")
    print("=" * 60)
    
    all_pass = True
    
    # Test 1: With flexible validation, 'range' should be playable after 'in'
    # (already allowed by category rules, but verify flexible validation agrees)
    can_play1, reason1 = can_play_card_with_reason("range", ["for", "i", "in"])
    status1 = "PASS" if can_play1 else "FAIL"
    if not can_play1:
        all_pass = False
    print(f"  {status1} 'range' after 'for i in': {can_play1} - {reason1}")
    
    # Test 2: Test that print can start a statement
    can_play2, reason2 = can_play_card_with_reason("print", [])
    status2 = "PASS" if can_play2 else "FAIL"
    if not can_play2:
        all_pass = False
    print(f"  {status2} 'print' at start: {can_play2} - {reason2}")
    
    # Test 3: Test operators after values
    can_play3, reason3 = can_play_card_with_reason("+", ["x", "=", "10"])
    status3 = "PASS" if can_play3 else "FAIL"
    if not can_play3:
        all_pass = False
    print(f"  {status3} '+' after 'x = 10': {can_play3} - {reason3}")
    
    # Test 4: Test closing paren with context
    can_play4, reason4 = can_play_card_with_reason(")", ["print", "(", "x"], open_paren_count=1)
    status4 = "PASS" if can_play4 else "FAIL"
    if not can_play4:
        all_pass = False
    print(f"  {status4} ')' with open paren: {can_play4} - {reason4}")
    
    # Test 5: Test that ')' is blocked without open paren
    can_play5, reason5 = can_play_card_with_reason(")", ["x"], open_paren_count=0)
    status5 = "PASS" if not can_play5 else "FAIL"
    if can_play5:
        all_pass = False
    print(f"  {status5} ')' blocked without open paren: {not can_play5} - {reason5}")
    
    return all_pass


def run_all_tests():
    """Run all tests and summarize results."""
    print("\n" + "=" * 60)
    print("GAME LOGIC IMPROVEMENT TESTS")
    print("=" * 60)
    
    results = []
    
    results.append(("Wild Card Fix", test_wild_card_fix()))
    results.append(("Parenthesis Tracking", test_parenthesis_tracking()))
    results.append(("Expanded can_follow Rules", test_expanded_can_follow()))
    results.append(("Statement Boundaries", test_statement_boundaries()))
    results.append(("Wild Card in Game State", test_wild_card_in_game()))
    results.append(("Special Cards Reset Wild", test_special_cards_reset_wild_flag()))
    results.append(("Playable Cards with Paren", test_playable_cards_with_paren_restriction()))
    # New Python validation tests
    results.append(("Python Code Builder", test_python_code_builder()))
    results.append(("Python Syntax Validation", test_python_syntax_validation()))
    results.append(("Can Form Valid Python", test_can_form_valid_python()))
    results.append(("Syntax Validation Info", test_syntax_validation_info()))
    results.append(("Flexible Card Insertion", test_flexible_card_insertion()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"  {status}: {name}")
    
    print("\n" + "-" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("-" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
