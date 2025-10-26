import os
import fnmatch

EXCLUDE_DIRS = {'.idea', 'build', 'image', 'test', 'seleniumwire', '__pycache__'}
EXCLUDE_FILES = {'.env', 'main.spec', 'print_tree.py'}
EXCLUDE_PATTERNS = ['*.txt']

def is_excluded(name: str, full_path: str, is_dir: bool) -> bool:
    if is_dir and name in EXCLUDE_DIRS:
        return True
    if not is_dir and name in EXCLUDE_FILES:
        return True
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False

def print_dir_tree(dir_path, depth=0, max_depth=4):
    if depth > max_depth:
        return

    prefix = "│  " * depth

    try:
        entries = sorted(os.listdir(dir_path))
    except PermissionError:
        print(f"{prefix}├─ [권한 없음]: {dir_path}")
        return

    folders = []
    py_files = []

    for entry in entries:
        full_path = os.path.join(dir_path, entry)
        is_dir = os.path.isdir(full_path)

        if is_excluded(entry, full_path, is_dir):
            continue

        if is_dir:
            folders.append(entry)
        elif entry.endswith((".py", ".bat", ".log", ".exe")):
            py_files.append(entry)

    for folder in folders:
        print(f"{prefix}├─ {folder}/")
        print_dir_tree(os.path.join(dir_path, folder), depth + 1, max_depth)

    for py_file in py_files:
        print(f"{prefix}├─ {py_file}")

if __name__ == "__main__":
    current_dir = os.path.abspath(os.getcwd())
    print_dir_tree(current_dir, max_depth=4)
