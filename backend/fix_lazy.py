import glob
import os

for f in glob.glob('models/*.py'):
    with open(f, 'r') as file:
        content = file.read()
    
    if 'lazy="joined"' in content:
        content = content.replace('lazy="joined"', 'lazy="selectin"')
        with open(f, 'w') as file:
            file.write(content)
        print(f"Updated {f}")
