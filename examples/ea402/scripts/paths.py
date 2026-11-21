"""Destinations for the current EA-4/02 samples."""
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
CURRENT_PROJECTS=BASE/'projects'
CURRENT_REPORTS=BASE/'reports'
for directory in (CURRENT_PROJECTS,CURRENT_REPORTS):directory.mkdir(parents=True,exist_ok=True)
