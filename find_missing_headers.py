import os
import ast

def has_header(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if there is a docstring
    try:
        module = ast.parse(content)
        if ast.get_docstring(module):
            return True
    except:
        pass
    
    # Or check if there are top-level comments
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#') and len(line) > 5:
            return True
        else:
            break
    return False

for root_dir in ['backend', 'solver', 'Scanner', 'motorctl']:
    for dirpath, _, filenames in os.walk(root_dir):
        for name in filenames:
            if name.endswith('.py'):
                path = os.path.join(dirpath, name)
                if not has_header(path):
                    print(path)
