import os
for root_dir in ['scripts']:
    for dirpath, _, filenames in os.walk(root_dir):
        for name in filenames:
            if name.endswith('.py') or name.endswith('.sh'):
                path = os.path.join(dirpath, name)
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                has_comment = False
                for line in lines:
                    line = line.strip()
                    if line.startswith('#!'):
                        continue
                    if line.startswith('#') and len(line) > 5:
                        has_comment = True
                        break
                    if line.startswith('"""') or line.startswith("'''"):
                        has_comment = True
                        break
                    if line:
                        break
                if not has_comment:
                    print(path)
