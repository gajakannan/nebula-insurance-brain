"""Read-only model-cache/process diagnostics; no environment or credentials."""
import json
from pathlib import Path

processes = []
for directory in Path('/proc').iterdir():
    if not directory.name.isdigit():
        continue
    try:
        command = (directory / 'cmdline').read_bytes().decode(errors='replace').replace('\x00', ' ')
        if 'pytest' in command:
            processes.append({'pid':directory.name,'command':command,
                              'stat':(directory/'stat').read_text(),
                              'wait':(directory/'wchan').read_text()})
    except (FileNotFoundError, PermissionError):
        pass
base = Path('/opt/venv/lib/python3.14/site-packages/rapidocr/models')
print(json.dumps({'processes':processes,'models':[{'name':p.name,'bytes':p.stat().st_size} for p in base.glob('*') if p.is_file()]},indent=2))
