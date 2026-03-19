#!/usr/bin/env python3
"""
Example: Run virtual screening with AutoDock Vina
"""

import os
import sys
import pandas as pd
from drugclaw.virtual_screening.prep import prepare_receptor, prepare_ligand_from_smiles
from drugclaw.virtual_screening.docking import run_vina_docking
from drugclaw.virtual_screening.analysis import analyze_results

def run_screening(receptor_pdb: str, center: tuple, box_size: tuple, 
                 smiles_csv: str, output_csv: str, cpu: int = 4):
    """
    Run complete virtual screening pipeline
    
    Args:
        receptor_pdb: Path to receptor PDB file
        center: (x, y, z) binding pocket center
        box_size: (size_x, size_y, size_z) box dimensions
        smiles_csv: CSV file with 'smiles' column
        output_csv: Output CSV for ranked results
        cpu: Number of CPUs to use
    """
    
    print("=== Virtual Screening Pipeline ===\n")
    
    # Step 1: Prepare receptor (remove water, add hydrogens, convert to pdbqt)
    print("1/4 Preparing receptor...")
    receptor_pdbqt = prepare_receptor(receptor_pdb)
    print(f"   Receptor prepared: {receptor_pdbqt}")
    
    # Step 2: Read compounds and prepare ligands
    print(f"\n2/4 Preparing {len(pd.read_csv(smiles_csv))} ligands...")
    ligands = []
    df = pd.read_csv(smiles_csv)
    for idx, row in df.iterrows():
        smiles = row['smiles']
        ligand_pdbqt = prepare_ligand_from_smiles(smiles, f"ligand_{idx}")
        if ligand_pdbqt:
            ligands.append((idx, smiles, ligand_pdbqt))
    
    print(f"   Successfully prepared {len(ligands)} ligands")
    
    # Step 3: Run docking
    print(f"\n3/4 Running docking on {cpu} CPUs...")
    results = []
    for idx, smiles, ligand_pdbqt in ligands:
        affinity = run_vina_docking(
            receptor_pdbqt, ligand_pdbqt,
            center, box_size,
            cpu=1,  # Parallelize across ligands
            output_dir="./docking_output"
        )
        results.append({
            'index': idx,
            'smiles': smiles,
            'affinity': affinity
        })
    
    # Step 4: Analyze and rank
    print("\n4/4 Analyzing results...")
    df_results = analyze_results(results, output_csv)
    
    print(f"\n✅ Done! Top 5 compounds:")
    print(df_results.head(5))
    
    return df_results

if __name__ == "__main__":
    # Example: PDB 1M17 (EGFR) with gefitinib
    # Binding pocket center approximated from literature
    center = (10.0, 20.0, 30.0)
    box_size = (20.0, 20.0, 20.0)
    run_screening(
        receptor_pdb="1M17.pdb",
        center=center,
        box_size=box_size,
        smiles_csv="compounds.csv",
        output_csv="screening_results.csv"
    )
