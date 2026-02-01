
filename = r"f:\synapse-develop\synapse\projects\models.py"
with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "class Project" in line:
            print(f"Line {i+1}: {line.strip()}")
