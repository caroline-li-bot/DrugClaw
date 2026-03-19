#!/usr/bin/env python3
"""
Deterministic retrieval/run for AutoDock Vina virtual screening
Usage: python retrieve.py receptor_pdb center_x center_y center_z box_size_x box_size_y box_size_z smiles_csv output_csv
"""

import sys
import os
import pandas as pd
from drugclaw.virtual_screening.prep import prepare_receptor, prepare_ligand_from_smiles
from drugclaw.virtual_screening.docking import run_vina_docking
from drugclaw.virtual_screening.analysis import analyze_results

def main():
    if len(sys.argv) < 10:
        print("Usage: python retrieve.py receptor_pdb center_x center_y center_z box_size_x box_size_y box_size_z smiles_csv output_csv")
        print("\nExample:")
        print("  python retrieve.py 1M17.pdb 10.0 20.0 30.0 20.0 20.0 20.0 compounds.csv results.csv")
        sys.exit(1)
    
    receptor_pdb = sys.argv[1]
    center = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
    box_size = (float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]))
    smiles_csv = sys.argv[8]
    output_csv = sys.argv[9]
    
    print(f"=== Starting AutoDock Vina Virtual Screening ===")
    print(f"Receptor: {receptor_pdb}")
    print(f"Binding pocket center: {center}")
    print(f"Box size: {box_size}")
    print(f"Input compounds: {smiles_csv}")
    print(f"Output results: {output_csv}")
    print()
    
    # Step 1: Prepare receptor
    print("1/4 Preparing receptor...")
    receptor_pdbqt = prepare_receptor(receptor_pdb)
    print(f"   Receptor prepared: {receptor_pdbqt}")
    
    # Step 2: Prepare ligands
    print(f"\n2/4 Preparing ligands...")
    df = pd.read_csv(smiles_csv)
    if 'smiles' not in df.columns:
        print("ERROR: Input CSV must have 'smiles' column")
        sys.exit(1)
    
    ligands = []
    failed = 0
    for idx, row in df.iterrows():
        smiles = row['smiles']
        name = row.get('name', f"ligand_{idx}")
        ligand_pdbqt = prepare_ligand_from_smiles(smiles, name)
        if ligand_pdbqt:
            ligands.append((idx, smiles, ligand_pdbqt))
        else:
            failed += 1
    
    print(f"   Successfully prepared {len(ligands)} ligands, {failed} failed")
    
    # Step 3: Run docking
    print(f"\n3/4 Running docking...")
    import multiprocessing
    cpu = min(4, multiprocessing.cpu_count())
    print(f"   Using {cpu} CPUs")
    
    results = []
    for idx, smiles, ligand_pdbqt in ligands:
        affinity = run_vina_docking(
            receptor_pdbqt, ligand_pdbqt,
            center, box_size,
            cpu=1,
            output_dir="docking_output"
        )
        if affinity is not None:
            results.append({
                'index': idx,
                'smiles': smiles,
                'affinity_kcal_mol': affinity
            })
    
    print(f"   Completed {len(results)} successful dockings")
    
    # Step 4: Analyze and save
    print(f"\n4/4 Analyzing and saving results...")
    df_results = analyze_results(results, output_csv)
    
    print(f"\n✅ Done! Results saved to {output_csv}")
    print(f"\nTop 5 compounds by binding affinity:")
    print(df_results.head(5).to_string(index=False))

if __name__ == "__main__":
    main()
