import os

for root, _, files in os.walk('.'):
    # skip .venv and .git
    if '.venv' in root or '.git' in root:
        continue
    for f in files:
        if f.endswith(('.py', '.txt', '.md', '.yaml', '.tf', '.json', '.env')):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='mbcs') as file:
                    file.read()
            except UnicodeDecodeError as e:
                print(f"File failing to read with default encoding: {path}")
                print(f"Error: {e}")
