"""Install this local experiment console as a user login service on Linux."""
import json
from pathlib import Path
import subprocess
import sys
from research.run import ROOT

def install():
    directory=Path.home()/'.config/systemd/user';directory.mkdir(parents=True,exist_ok=True)
    path=directory/'hexapod-research-lab.service'
    marker='# Hexapod Research Lab local service'
    if path.exists() and marker not in path.read_text():
        raise RuntimeError('A different service already uses this name; existing service left intact')
    quote=lambda value:json.dumps(str(value).replace('%','%%'))
    directory_value=str(ROOT).replace('\\','\\\\').replace(' ','\\x20').replace('%','%%')
    content=f'''{marker}
[Unit]
Description=Hexapod local research console

[Service]
Type=simple
WorkingDirectory={directory_value}
ExecStart={quote(sys.executable)} -m research.server --port 8771
Environment=PYTHONUNBUFFERED=1
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
'''
    path.write_text(content)
    subprocess.run(['systemctl','--user','daemon-reload'],check=True)
    subprocess.run(['systemctl','--user','enable','--now','hexapod-research-lab.service'],check=True)
    print('Research console login service installed at http://127.0.0.1:8771')

if __name__=='__main__':install()
