import json
import itertools
import signal
import sys
import argparse

# Load language strings from JSON
def load_language(lang_file='languages.json'):
    with open(lang_file, 'r', encoding='utf-8') as file:
        return json.load(file)

# Global variables
lang = {}
tried_combinations = {}
current_combination = ''
interruption_count = 0

# Ergonomic score calculation
def ergonomic_score(combination):
    easy_pairs = [tuple(pair) for pair in itertools.permutations(characters, 2)]
    score = sum(1 for i in range(len(combination) - 1) if (combination[i], combination[i + 1]) in easy_pairs)
    return score

# Pattern score calculation
def pattern_score(combination):
    common_patterns = [''.join(pattern) for pattern in itertools.permutations(characters, 2)]
    score = sum(1 for pattern in common_patterns if pattern in combination)
    return score

def is_psychologically_likely(combination):
    if any(combination.count(c) > 2 for c in combination):
        return False
    if ergonomic_score(combination) < 1 or pattern_score(combination) < 1:
        return False
    return True

def generate_combinations():
    valid_combinations = set()
    for length in range(4, 6):
        for comb in itertools.permutations(characters, length):
            comb_str = ''.join(comb)
            if is_psychologically_likely(comb_str):
                valid_combinations.add(comb_str)
    return sorted(valid_combinations, key=lambda x: (ergonomic_score(x) + pattern_score(x)), reverse=True)

def load_tried_combinations(filename='tried_combinations.json'):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_tried_combinations(filename='tried_combinations.json'):
    with open(filename, 'w') as file:
        json.dump(tried_combinations, file, indent=4)

def ask_and_save_combination(comb):
    if comb not in tried_combinations:
        response = input(lang['ask_combination'].format(comb)).strip().lower()
        tried_combinations[comb] = response == lang['yes']
        save_tried_combinations()
    else:
        print(lang['combination_tried'].format(comb))

def signal_handler(sig, frame):
    global interruption_count
    interruption_count += 1
    if interruption_count == 1:
        print(f"\n{lang['interrupt_detected']}")
        alternative_mode()
    elif interruption_count == 2:
        response = input(f"\n{lang['exit_prompt']}").strip().lower()
        if response == lang['yes']:
            print(lang['exiting'])
            sys.exit(0)
        else:
            interruption_count = 0

def main():
    global tried_combinations, current_combination, interruption_count
    interruption_count = 0
    signal.signal(signal.SIGINT, signal_handler)
    
    tried_combinations = load_tried_combinations()
    all_combinations = generate_combinations()

    tried_count = sum(1 for comb in all_combinations if comb in tried_combinations)
    print(lang['total_combinations'].format(len(all_combinations)))
    print(lang['tried_combinations'].format(tried_count))

    while True:
        choice = input(lang['menu_prompt']).strip()
        if choice == "1":
            print(f"\n{lang['tried_combinations_header']}")
            for comb in tried_combinations:
                print(comb)
        elif choice == "2":
            print(f"\n{lang['untried_combinations_header']}")
            for comb in all_combinations:
                if comb not in tried_combinations:
                    print(comb)
        elif choice == "3":
            for comb in all_combinations:
                if comb not in tried_combinations:
                    current_combination = comb
                    print(lang['testing_combination'].format(comb))
                    ask_and_save_combination(comb)
        elif choice == "4":
            break
        else:
            print(lang['invalid_choice'])

def alternative_mode():
    while True:
        comb = input(lang['enter_combination']).strip()
        if comb.lower() == lang['exit']:
            break
        if 4 <= len(comb) <= 5 and all(comb.count(c) <= 2 for c in comb):
            ask_and_save_combination(comb)
        else:
            print(lang['invalid_combination'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Combination testing script')
    parser.add_argument('--chars', type=str, default='', help='Characters to use for combinations')
    parser.add_argument('--lang', type=str, default='de', choices=['de', 'en'], help='Language to use (de or en)')
    args = parser.parse_args()

    characters = list(args.chars)
    lang = load_language()[args.lang]

    main()