# AutoDock Vina - Virtual Screening Skill

## About AutoDock Vina

AutoDock Vina is an open-source automatic docking tool for molecular docking and virtual screening.

Features:
- Fast molecular docking of small molecules to protein targets
- Parallel processing for multiple CPUs
- Good accuracy compared to older AutoDock
- Supports flexible side-chains

Website: http://vina.scripps.edu/

## System Requirements

You need to have AutoDock Vina installed on your system:
```bash
# Ubuntu/Debian
sudo apt install autodock-vina

# Or download from:
http://vina.scripps.edu/downloading-and-installing-autodock-vina/
```

Also needs MGLTools for preparing protein:
```bash
# MGLTools provides prepare_receptor.py
```

## Usage

Run virtual screening against a protein target:
- Input: Target PDB file + compound library (SMILES)
- Output: Ranking of compounds by binding affinity

### Example Queries:
- "Screen this compound library against EGFR target in PDB 1M17"
- "Run virtual screening with binding pocket at x=10 y=20 z=30"
