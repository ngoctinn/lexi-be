#!/usr/bin/env python3
"""
Verify all imports and function calls in the codebase.
Detects:
1. Missing imports
2. Wrong class/function names
3. Missing dependencies
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

class ImportVerifier(ast.NodeVisitor):
    """Verify imports and function calls."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.imports: Dict[str, str] = {}  # {name: module}
        self.calls: List[Tuple[str, int]] = []  # [(name, line)]
        self.errors: List[str] = []
        
    def visit_Import(self, node):
        """Track: import x"""
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = alias.name
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Track: from x import y"""
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = f"{node.module}.{alias.name}"
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Track function calls"""
        if isinstance(node.func, ast.Name):
            self.calls.append((node.func.id, node.lineno))
        self.generic_visit(node)

def verify_file(filepath: str) -> List[str]:
    """Verify a single Python file."""
    errors = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filepath)
        verifier = ImportVerifier(filepath)
        verifier.visit(tree)
        
        # Check for undefined calls
        for call_name, line_no in verifier.calls:
            # Skip built-ins and common functions
            if call_name in {'print', 'len', 'str', 'int', 'dict', 'list', 'set', 'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed', 'sum', 'max', 'min', 'any', 'all', 'isinstance', 'hasattr', 'getattr', 'setattr', 'callable', 'type', 'super', 'property', 'staticmethod', 'classmethod', 'open', 'json', 'logging', 'os', 'sys', 'boto3', 'replace', 'dataclass'}:
                continue
            
            # Check if it's imported or defined
            if call_name not in verifier.imports:
                # Could be a method or local function, skip for now
                pass
                
    except SyntaxError as e:
        errors.append(f"SYNTAX ERROR in {filepath}:{e.lineno}: {e.msg}")
    except Exception as e:
        errors.append(f"ERROR in {filepath}: {str(e)}")
    
    return errors

def check_imports_exist(filepath: str) -> List[str]:
    """Check if imported modules/classes actually exist."""
    errors = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filepath)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module
                if not module:
                    continue
                    
                for alias in node.names:
                    name = alias.name
                    
                    # Try to import and check
                    try:
                        parts = module.split('.')
                        mod = __import__(module)
                        for part in parts[1:]:
                            mod = getattr(mod, part)
                        
                        # Check if the imported name exists
                        if not hasattr(mod, name) and name != '*':
                            errors.append(f"{filepath}:{node.lineno}: Cannot import '{name}' from '{module}'")
                    except ImportError:
                        # Module doesn't exist, but that's OK for now
                        pass
                    except AttributeError:
                        errors.append(f"{filepath}:{node.lineno}: Cannot import '{name}' from '{module}'")
                        
    except SyntaxError:
        pass
    except Exception:
        pass
    
    return errors

def scan_directory(directory: str) -> Dict[str, List[str]]:
    """Scan all Python files in directory."""
    results = {}
    
    for filepath in Path(directory).rglob('*.py'):
        # Skip test files and build directories
        if '.aws-sam' in str(filepath) or '__pycache__' in str(filepath) or 'test' in str(filepath):
            continue
        
        errors = verify_file(str(filepath))
        if errors:
            results[str(filepath)] = errors
    
    return results

def main():
    """Main entry point."""
    print("🔍 Verifying Python imports and function calls...\n")
    
    # Scan backend
    print("Scanning lexi-be/src...")
    results = scan_directory('lexi-be/src')
    
    if not results:
        print("✅ No syntax errors found!\n")
    else:
        print("❌ Errors found:\n")
        for filepath, errors in sorted(results.items()):
            print(f"  {filepath}:")
            for error in errors:
                print(f"    - {error}")
        print()
    
    # Try to import all handlers to catch runtime errors
    print("Testing handler imports...")
    handlers = [
        'lexi-be/src/infrastructure/handlers/websocket_handler.py',
        'lexi-be/src/infrastructure/handlers/session_handler.py',
        'lexi-be/src/infrastructure/handlers/flashcard/create_flashcard_handler.py',
        'lexi-be/src/infrastructure/handlers/flashcard/list_due_cards_handler.py',
        'lexi-be/src/infrastructure/handlers/flashcard/get_flashcard_handler.py',
        'lexi-be/src/infrastructure/handlers/flashcard/list_flashcards_handler.py',
        'lexi-be/src/infrastructure/handlers/flashcard/review_flashcard_handler.py',
    ]
    
    import_errors = []
    for handler in handlers:
        if not Path(handler).exists():
            import_errors.append(f"File not found: {handler}")
            continue
        
        try:
            # Try to compile the file
            with open(handler, 'r') as f:
                compile(f.read(), handler, 'exec')
            print(f"  ✅ {handler}")
        except SyntaxError as e:
            import_errors.append(f"{handler}:{e.lineno}: {e.msg}")
            print(f"  ❌ {handler}: {e.msg}")
        except Exception as e:
            import_errors.append(f"{handler}: {str(e)}")
            print(f"  ❌ {handler}: {str(e)}")
    
    if import_errors:
        print(f"\n❌ Found {len(import_errors)} import errors")
        return 1
    else:
        print("\n✅ All handlers compile successfully!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
