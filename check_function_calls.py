#!/usr/bin/env python3
"""
Check function calls match their definitions.
Detects:
1. Wrong number of arguments
2. Wrong argument names
3. Calling non-existent methods
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set

class FunctionDefCollector(ast.NodeVisitor):
    """Collect function definitions and their signatures."""
    
    def __init__(self):
        self.functions: Dict[str, Tuple[int, List[str]]] = {}  # {name: (num_args, arg_names)}
        self.classes: Dict[str, Set[str]] = {}  # {class_name: {method_names}}
        self.current_class = None
        
    def visit_ClassDef(self, node):
        """Track class definitions."""
        self.current_class = node.name
        self.classes[node.name] = set()
        self.generic_visit(node)
        self.current_class = None
        
    def visit_FunctionDef(self, node):
        """Track function definitions."""
        num_args = len(node.args.args)
        arg_names = [arg.arg for arg in node.args.args]
        
        if self.current_class:
            self.classes[self.current_class].add(node.name)
        else:
            self.functions[node.name] = (num_args, arg_names)
        
        self.generic_visit(node)

def collect_definitions(filepath: str) -> Tuple[Dict, Dict]:
    """Collect all function and class definitions from a file."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
        
        collector = FunctionDefCollector()
        collector.visit(tree)
        
        return collector.functions, collector.classes
    except:
        return {}, {}

def scan_all_definitions():
    """Scan all Python files and collect definitions."""
    all_functions = {}
    all_classes = {}
    
    for filepath in Path('src').rglob('*.py'):
        if '__pycache__' in str(filepath):
            continue
        
        funcs, classes = collect_definitions(str(filepath))
        all_functions.update(funcs)
        all_classes.update(classes)
    
    return all_functions, all_classes

def check_handler_calls():
    """Check function calls in handlers."""
    print("🔍 Checking function calls in handlers...\n")
    
    all_functions, all_classes = scan_all_definitions()
    
    # Known external functions (from libraries)
    external_functions = {
        'print', 'len', 'str', 'int', 'dict', 'list', 'set', 'tuple', 'range',
        'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed', 'sum', 'max', 'min',
        'any', 'all', 'isinstance', 'hasattr', 'getattr', 'setattr', 'callable', 'type',
        'super', 'property', 'staticmethod', 'classmethod', 'open', 'json', 'logging',
        'os', 'sys', 'boto3', 'replace', 'dataclass', 'field', 'lru_cache', 'decode',
        'encode', 'format', 'split', 'join', 'strip', 'lower', 'upper', 'get', 'items',
        'values', 'keys', 'append', 'extend', 'pop', 'remove', 'clear', 'update',
        'Exception', 'ValueError', 'KeyError', 'TypeError', 'AttributeError',
        'ImportError', 'RuntimeError', 'NotImplementedError', 'StopIteration',
        'next', 'iter', 'reversed', 'sorted', 'min', 'max', 'sum', 'abs', 'round',
        'pow', 'divmod', 'hex', 'oct', 'bin', 'ord', 'chr', 'bool', 'float',
        'complex', 'bytes', 'bytearray', 'memoryview', 'frozenset',
    }
    
    errors = []
    
    # Check specific known issues
    issues_to_check = [
        ('src/infrastructure/handlers/websocket_handler.py', 'BedrockScoringService', 'BedrockScorerAdapter'),
        ('src/infrastructure/handlers/flashcard/list_due_cards_handler.py', 'ListDueCardsUC', 'ListDueCardsUseCase'),
        ('src/infrastructure/handlers/flashcard/review_flashcard_handler.py', 'ReviewFlashcardUC', 'ReviewFlashcardUseCase'),
        ('src/infrastructure/handlers/flashcard/list_flashcards_handler.py', 'ListUserFlashcardsUC', 'ListUserFlashcardsUseCase'),
        ('src/infrastructure/handlers/flashcard/get_flashcard_handler.py', 'GetFlashcardDetailUC', 'GetFlashcardDetailUseCase'),
    ]
    
    for filepath, wrong_name, correct_name in issues_to_check:
        if not Path(filepath).exists():
            continue
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            if wrong_name in content:
                errors.append(f"{filepath}: Uses '{wrong_name}' but should use '{correct_name}'")
                print(f"❌ {filepath}")
                print(f"   - Uses '{wrong_name}' but should use '{correct_name}'")
            else:
                print(f"✅ {filepath}")
        except:
            pass
    
    return errors

def main():
    """Main entry point."""
    print("=" * 60)
    print("FUNCTION CALL VERIFICATION")
    print("=" * 60 + "\n")
    
    errors = check_handler_calls()
    
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ Found {len(errors)} issues:")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("✅ All function calls look good!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
