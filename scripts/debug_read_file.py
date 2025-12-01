import os

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/domain/dtos/machine_io.py'))
print(f"Reading file: {file_path}")

try:
    with open(file_path, 'r') as f:
        content = f.read()
        print("--- CONTENT START ---")
        print(content)
        print("--- CONTENT END ---")
except Exception as e:
    print(f"Error reading file: {e}")
