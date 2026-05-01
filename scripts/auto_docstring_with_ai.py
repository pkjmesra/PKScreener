#!/usr/bin/env python3
"""
Auto-generate meaningful docstrings for ALL undocumented Python code using AI.
Scans pkscreener/ and ALL subdirectories recursively.
"""

import ast
import sys
import re
import time
import warnings
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import subprocess

# Suppress syntax warnings from third-party code
warnings.filterwarnings("ignore", category=SyntaxWarning)

@dataclass
class MissingDocstring:
    file: Path
    type: str
    name: str
    lineno: int
    indent: int
    source_code: str
    args: List[str] = field(default_factory=list)
    is_async: bool = False

class OllamaDocstringGenerator:
    def __init__(self, model: str = "codellama:7b-instruct", rate_limit: float = 0.5):
        self.model = model
        self.rate_limit = rate_limit
        self.last_call = 0
        self.stats = {"generated": 0, "failed": 0}

    def _call_ollama(self, prompt: str) -> str:
        elapsed = time.time() - self.last_call
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            self.last_call = time.time()
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception:
            return ""

    def generate_function_docstring(self, func_name: str, args: List[str],
                                      is_async: bool, is_method: bool,
                                      source_code: str) -> str:
        prompt = f"""Generate a Python docstring for this function.

Function name: {func_name}
Type: {'async ' if is_async else ''}{'method' if is_method else 'function'}
Parameters: {', '.join(args) if args else 'none'}

Code:
{source_code[:1500]}

Return ONLY the docstring with triple quotes. Include:
- What the function does
- Args: each parameter with description
- Returns: what is returned
- Example usage"""

        response = self._call_ollama(prompt)
        if response:
            self.stats["generated"] += 1
            return self._clean_docstring(response)
        self.stats["failed"] += 1
        return self._placeholder(func_name, args)

    def generate_class_docstring(self, class_name: str, bases: List[str], source_code: str) -> str:
        prompt = f"""Generate a Python docstring for this class.

Class name: {class_name}
Inherits from: {', '.join(bases) if bases else 'object'}

Code:
{source_code[:1500]}

Return ONLY the docstring with triple quotes describing the class purpose."""

        response = self._call_ollama(prompt)
        if response:
            self.stats["generated"] += 1
            return self._clean_docstring(response)
        self.stats["failed"] += 1
        return f'"""{class_name} class."""'

    def generate_module_docstring(self, module_name: str) -> str:
        prompt = f"""Generate a short module docstring for {module_name}.
This is for PKScreener, a stock screening system.
Return ONLY the docstring with triple quotes, 2-3 lines max."""

        response = self._call_ollama(prompt)
        if response:
            self.stats["generated"] += 1
            return self._clean_docstring(response)
        self.stats["failed"] += 1
        return f'"""{module_name} module for PKScreener."""'

    def _clean_docstring(self, docstring: str) -> str:
        docstring = re.sub(r'^```python\s*\n?', '', docstring)
        docstring = re.sub(r'^```\s*\n?', '', docstring)
        docstring = re.sub(r'\n```$', '', docstring)
        if not docstring.startswith('"""'):
            docstring = '"""\n' + docstring.strip() + '\n"""'
        return docstring

    def _placeholder(self, func_name: str, args: List[str]) -> str:
        doc = f'"""\n{func_name} function.\n\n'
        if args:
            doc += 'Args:\n'
            for arg in args:
                doc += f'    {arg}: TODO\n'
            doc += '\n'
        doc += 'Returns:\n    TODO\n"""'
        return doc

class DocumentScanner:
    def __init__(self, root_dir: str = "pkscreener"):
        self.root_dir = Path(root_dir)
        self.missing_items: List[MissingDocstring] = []

    def scan_all(self) -> List[MissingDocstring]:
        self.missing_items = []
        for py_file in self.root_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            self._scan_file(py_file)
        return self.missing_items

    def _scan_file(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception:
            return

        try:
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            return

        # Module docstring
        if not ast.get_docstring(tree):
            self.missing_items.append(MissingDocstring(
                file=filepath, type='module', name=filepath.stem,
                lineno=1, indent=0, source_code='\n'.join(lines[:20])
            ))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    try:
                        source_lines = lines[node.lineno - 1:node.end_lineno]
                    except Exception:
                        source_lines = ['class ' + node.name]
                    self.missing_items.append(MissingDocstring(
                        file=filepath, type='class', name=node.name,
                        lineno=node.lineno, indent=0,
                        source_code='\n'.join(source_lines[:30]),
                        args=[b.id for b in node.bases if isinstance(b, ast.Name)]
                    ))

            elif isinstance(node, ast.FunctionDef):
                if node.name == '__init__' or node.name.startswith('_'):
                    continue
                if not ast.get_docstring(node):
                    try:
                        source_lines = lines[node.lineno - 1:node.end_lineno]
                    except Exception:
                        source_lines = ['def ' + node.name + '()']
                    is_method = 'self' in [arg.arg for arg in node.args.args]
                    indent = 0
                    try:
                        indent = len(lines[node.lineno - 1]) - len(lines[node.lineno - 1].lstrip())
                    except Exception:
                        indent = 4
                    self.missing_items.append(MissingDocstring(
                        file=filepath, type='method' if is_method else 'function',
                        name=node.name, lineno=node.lineno,
                        indent=indent,
                        source_code='\n'.join(source_lines),
                        args=[arg.arg for arg in node.args.args if arg.arg not in ('self', 'cls')],
                        is_async=isinstance(node, ast.AsyncFunctionDef)
                    ))

class DocstringInserter:
    def __init__(self):
        self.modified_count = 0
        self.failed_count = 0

    def insert_docstring(self, item: MissingDocstring, docstring: str) -> bool:
        try:
            filepath = item.file
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            indent_str = ' ' * (item.indent + 4)
            doc_lines = docstring.split('\n')
            formatted = [f'{indent_str}{line}' for line in doc_lines]

            insert_line = item.lineno
            for doc_line in reversed(formatted):
                lines.insert(insert_line, doc_line + '\n')

            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            self.modified_count += 1
            return True
        except Exception as e:
            self.failed_count += 1
            print(f"    Error inserting: {e}")
            return False

def main():
    print("=" * 60)
    print("AI Docstring Generator for PKScreener")
    print("=" * 60)

    # Check Ollama
    result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: Ollama not found.")
        print("Please install it first:")
        print("  curl -fsSL https://ollama.com/install.sh | sh")
        print("  ollama pull codellama:7b-instruct")
        return

    # Pull model if needed
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if "codellama" not in result.stdout and "deepseek" not in result.stdout:
        print("Pulling codellama:7b-instruct (may take 5-10 minutes)...")
        subprocess.run(["ollama", "pull", "codellama:7b-instruct"])

    # Scan
    print("\nScanning pkscreener/ and all subdirectories...")
    scanner = DocumentScanner()
    missing = scanner.scan_all()

    print(f"Found {len(missing)} items missing docstrings:")
    counts = {}
    for item in missing:
        counts[item.type] = counts.get(item.type, 0) + 1
    for t, c in counts.items():
        print(f"  - {t}: {c}")

    if not missing:
        print("No missing docstrings found!")
        return

    # Auto-proceed without asking
    print(f"\nAuto-generating docstrings for {len(missing)} items...")

    # Generate and insert
    generator = OllamaDocstringGenerator()
    inserter = DocstringInserter()

    for i, item in enumerate(missing, 1):
        print(f"[{i}/{len(missing)}] {item.type}: {item.name}")

        if item.type == 'module':
            docstring = generator.generate_module_docstring(item.name)
        elif item.type == 'class':
            docstring = generator.generate_class_docstring(item.name, item.args, item.source_code)
        else:
            docstring = generator.generate_function_docstring(
                item.name, item.args, item.is_async,
                item.type == 'method', item.source_code
            )

        if docstring:
            inserter.insert_docstring(item, docstring)
            print(f"    Added docstring")

    print(f"\n" + "=" * 60)
    print("COMPLETE!")
    print(f"Modified files: {inserter.modified_count}")
    print(f"Failed: {inserter.failed_count}")
    print(f"AI Generated: {generator.stats['generated']}")
    print(f"AI Failed: {generator.stats['failed']}")
    print("=" * 60)

if __name__ == "__main__":
    main()