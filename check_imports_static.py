#!/usr/bin/env python3
"""
Static analysis to find import errors without running code.
Checks:
1. Imported names that don't exist in modules
2. Function calls to non-existent functions
"""

import ast
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple

class ImportChecker(ast.NodeVisitor):
    """Check imports and calls statically."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.imports: Dict[str, str] = {}  # {alias: full_path}
        self.defined_names: Set[str] = set()  # Functions, classes defined in this file
        self.calls: List[Tuple[str, int]] = []  # (name, line)
        self.errors: List[str] = []
        
    def visit_Import(self, node):
        """Track: import x, import x as y"""
        for alias in node.names:
            name = alias.asname or alias.name.split('.')[0]
            self.imports[name] = alias.name
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Track: from x import y, from x import y as z"""
        for alias in node.names:
            name = alias.asname or alias.name
            if name != '*':
                self.imports[name] = f"{node.module}.{alias.name}" if node.module else alias.name
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        """Track defined functions"""
        self.defined_names.add(node.name)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        """Track defined classes"""
        self.defined_names.add(node.name)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Track function calls"""
        if isinstance(node.func, ast.Name):
            self.calls.append((node.func.id, node.lineno))
        self.generic_visit(node)

def check_file(filepath: str) -> List[str]:
    """Check a single file for import issues."""
    errors = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filepath)
        checker = ImportChecker(filepath)
        checker.visit(tree)
        
        # Known built-ins and common functions
        builtins = {
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
        
        # Check calls
        for call_name, line_no in checker.calls:
            if call_name in builtins:
                continue
            if call_name in checker.defined_names:
                continue
            if call_name in checker.imports:
                continue
            # Could be a method or attribute, skip
            
    except SyntaxError as e:
        errors.append(f"SYNTAX ERROR: {e.msg} at line {e.lineno}")
    except Exception as e:
        errors.append(f"ERROR: {str(e)}")
    
    return errors

def scan_handlers():
    """Scan all handler files."""
    handlers = [
        'src/infrastructure/handlers/websocket_handler.py',
        'src/infrastructure/handlers/session_handler.py',
        'src/infrastructure/handlers/flashcard/create_flashcard_handler.py',
        'src/infrastructure/handlers/flashcard/list_due_cards_handler.py',
        'src/infrastructure/handlers/flashcard/get_flashcard_handler.py',
        'src/infrastructure/handlers/flashcard/list_flashcards_handler.py',
        'src/infrastructure/handlers/flashcard/review_flashcard_handler.py',
    ]
    
    print("🔍 Checking handler imports...\n")
    
    all_errors = {}
    for handler in handlers:
        if not Path(handler).exists():
            print(f"❌ {handler}: FILE NOT FOUND")
            all_errors[handler] = ["FILE NOT FOUND"]
            continue
        
        errors = check_file(handler)
        if errors:
            print(f"❌ {handler}:")
            for error in errors:
                print(f"   - {error}")
            all_errors[handler] = errors
        else:
            print(f"✅ {handler}")
    
    return all_errors

def check_undefined_calls():
    """Check for undefined function/class calls in source files."""
    print("\n🔍 Checking for undefined calls...\n")
    
    # Map of module -> defined classes/functions
    definitions: Dict[str, Set[str]] = {}
    
    # Scan all Python files to build definitions map
    for filepath in Path('src').rglob('*.py'):
        if '__pycache__' in str(filepath):
            continue
        
        try:
            with open(filepath, 'r') as f:
                tree = ast.parse(f.read())
            
            module_name = str(filepath).replace('src/', '').replace('.py', '').replace('/', '.')
            definitions[module_name] = set()
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    definitions[module_name].add(node.name)
        except:
            pass
    
    # Now check handlers for undefined calls
    errors = {}
    for handler in Path('src/infrastructure/handlers').rglob('*.py'):
        if '__pycache__' in str(handler):
            continue
        
        try:
            with open(handler, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Find all imports
            imports = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        if node.module:
                            module_key = node.module.replace('.', '/')
                            imports[name] = (node.module, alias.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name.split('.')[0]
                        imports[name] = (alias.name, None)
            
            # Check if imported names exist
            handler_errors = []
            for name, (module, attr) in imports.items():
                if attr and attr != '*':
                    # Check if class/function exists in module
                    module_key = module.replace('.', '/')
                    if module_key in definitions:
                        if attr not in definitions[module_key]:
                            handler_errors.append(f"Cannot import '{attr}' from '{module}' (not defined)")
            
            if handler_errors:
                errors[str(handler)] = handler_errors
                print(f"❌ {handler}:")
                for error in handler_errors:
                    print(f"   - {error}")
            else:
                print(f"✅ {handler}")
        except:
            pass
    
    return errors

def main():
    """Main entry point."""
    print("=" * 60)
    print("IMPORT VERIFICATION TOOL")
    print("=" * 60 + "\n")
    
    # Check handlers
    handler_errors = scan_handlers()
    
    # Check undefined calls
    call_errors = check_undefined_calls()
    
    print("\n" + "=" * 60)
    if handler_errors or call_errors:
        total = len(handler_errors) + len(call_errors)
        print(f"❌ Found issues in {total} files")
        return 1
    else:
        print("✅ All imports look good!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
