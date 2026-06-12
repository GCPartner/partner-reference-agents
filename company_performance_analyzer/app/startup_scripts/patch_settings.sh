#!/bin/bash
echo "[STARTUP PATCH] Printing installed Pydantic versions in container:"
python3 -c "import pydantic; import pydantic_settings; print('pydantic:', pydantic.__version__); print('pydantic-settings:', pydantic_settings.__version__)"

echo "[STARTUP PATCH] Patching /code/app/settings.py using python script..."
python3 -c '
import os
import re
path = "/code/app/settings.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()
    
    # 1. Inject model_config dict
    content, count = re.subn(
        r"class\s+Settings\s*\(\s*pydantic_settings\.BaseSettings\s*\)\s*:",
        "class Settings(pydantic_settings.BaseSettings):\n  model_config = {\"extra\": \"ignore\", \"env_file\": \".env\", \"env_prefix\": \"VERTEX_\", \"env_file_encoding\": \"utf-8\"}",
        content
    )
    print(f"[PYTHON PATCH] Injected model_config header. Matches: {count}")
    
    # 2. Strip legacy class Config subclass to prevent conflicts
    lines = content.splitlines()
    new_lines = []
    skip = False
    stripped_count = 0
    for line in lines:
        if re.match(r"^\s*class\s+Config\s*:\s*$", line):
            skip = True
            stripped_count += 1
            print("[PYTHON PATCH] Found legacy Config class, stripping...")
            continue
        if skip:
            if line.startswith("    ") or line.strip() == "":
                continue
            else:
                skip = False
        new_lines.append(line)
    
    content = "\n".join(new_lines)
    with open(path, "w") as f:
        f.write(content)
    print(f"[PYTHON PATCH] Legacy class Config stripped: {stripped_count}")
    print("[PYTHON PATCH] Patch completed successfully.")
else:
    print("[PYTHON PATCH] settings.py not found at " + path)
'

# Crucial step: Delete compiled bytecode cache to force Python to reload and recompile our patched settings.py
echo "[STARTUP PATCH] Cleaning compiled pyc cache files to force reload..."
find /code/app/ -name "*.pyc" -delete
rm -rf /code/app/__pycache__
rm -rf /code/app/*/__pycache__
echo "[STARTUP PATCH] Cache cleaning complete."

echo "[STARTUP PATCH] Debugging Settings class imports and configuration:"
python3 -c '
import sys
sys.path.insert(0, "/code")
try:
    from app.settings import Settings
    print("[DEBUG] Settings model_fields:", list(Settings.model_fields.keys()))
    print("[DEBUG] Settings model_config:", Settings.model_config)
    s = Settings()
    print("[DEBUG] Settings instantiation success:", s.model_dump())
except Exception as e:
    print("[DEBUG] Settings instantiation failed:", e)
'

echo "[STARTUP PATCH] Printing final patched /code/app/settings.py contents:"
if [ -f "/code/app/settings.py" ]; then
  cat /code/app/settings.py
  echo "[STARTUP PATCH] End of patched file printing."
else
  echo "[STARTUP PATCH] Warning: patched settings.py not found!"
fi
