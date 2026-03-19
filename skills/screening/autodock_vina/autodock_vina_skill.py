#!/usr/bin/env python3
"""
AutoDock Vina Virtual Screening Skill
"""

from typing import List, Dict, Optional
import pandas as pd
import os

from drugclaw.virtual_screening.prep import prepare_receptor, prepare_ligand_from_smiles
from drugclaw.virtual_screening.docking import run_vina_docking, run_batch_docking
from drugclaw.virtual_screening.analysis import analyze_results, generate_report

def retrieve(entities: List[str]) -> str:
    """Retrieve/run virtual screening - this is the skill entrypoint
    
    Expected entities: receptor_pdb, center_x, center_y, center_z, smiles_csv
    """
    if len(entities) < 7:
        return """Error: Insufficient parameters.
Expected: receptor_pdb center_x center_y center_z box_size_x box_size_y box_size_z smiles_csv
Example: python retrieve.py 1M17.pdb 10.0 20.0 30.0 20.0 20.0 20.0 compounds.csv
"""
    
    receptor_pdb = entities[0]
    try:
        center = (float(entities[1]), float(entities[2]), float(entities[3]))
        box_size = (float(entities[4]), float(entities[5]), float(entities[6]))
    except ValueError:
        return "Error: center and box size must be numbers"
    
    smiles_csv = entities[7] if len(entities) > 7 else "compounds.csv"
    output_csv = "screening_results.csv"
    output_report = "screening_report.md"
    
    output_lines = [f"# Starting Virtual Screening with AutoDock Vina\n"]
    output_lines.append(f"- Receptor: {receptor_pdb}")
    output_lines.append(f"- Binding pocket center: {center}")
    output_lines.append(f"- Box size: {box_size}")
    output_lines.append(f"- Input compounds: {smiles_csv}")
    output_lines.append("")
    
    # Step 1: Prepare receptor
    output_lines.append("## 1. Preparing receptor")
    try:
        receptor_pdbqt = prepare_receptor(receptor_pdb)
        output_lines.append(f"✅ Receptor prepared: {receptor_pdbqt}")
    except Exception as e:
        output_lines.append(f"❌ Error preparing receptor: {str(e)}")
        return "\n".join(output_lines)
    
    # Step 2: Prepare ligands
    output_lines.append("\n## 2. Preparing ligands")
    df = pd.read_csv(smiles_csv)
    if 'smiles' not in df.columns:
        output_lines.append("❌ Error: Input CSV must have 'smiles' column")
        return "\n".join(output_lines)
    
    ligands = []
    failed = 0
    for idx, row in df.iterrows():
        smiles = row['smiles']
        name = row.get('name', f"ligand_{idx}")
        ligand_pdbqt = prepare_ligand_from_smiles(smiles, name, output_dir="ligands")
        if ligand_pdbqt:
            ligands.append((idx, smiles, ligand_pdbqt))
        else:
            failed += 1
    
    output_lines.append(f"✅ Prepared {len(ligands)} ligands, {failed} failed")
    
    # Step 3: Run docking
    output_lines.append(f"\n## 3. Running docking ({len(ligands)} ligands)")
    results = run_batch_docking(
        receptor_pdbqt, ligands, center, box_size,
        output_dir="docking_output",
        max_parallel=4
    )
    
    output_lines.append(f"✅ Completed {len(results)} successful dockings")
    
    # Step 4: Analyze
    output_lines.append("\n## 4. Analysis and ranking")
    result_list = [
        {
            'index': idx,
            'smiles': smiles,
            'affinity_kcal_mol': affinity
        }
        for idx, smiles, affinity in results
    ]
    
    df_results = analyze_results(result_list, output_csv)
    generate_report(df_results, output_report)
    
    # Summary
    from drugclaw.virtual_screening.analysis import summary_statistics
    stats = summary_statistics(df_results)
    
    output_lines.append("\n## 📊 Summary")
    output_lines.append(f"- Total compounds docked: **{stats['total_compounds']}**")
    output_lines.append(f"- Best affinity: **{stats['min_affinity']:.2f}** kcal/mol")
    output_lines.append(f"- Compounds with affinity < -7 kcal/mol: **{stats['count_below_-7']}**")
    output_lines.append(f"- Compounds with affinity < -9 kcal/mol: **{stats['count_below_-9']}**")
    
    output_lines.append(f"\n✅ Results saved to:")
    output_lines.append(f"- CSV: {output_csv}")
    output_lines.append(f"- Report: {output_report}")
    
    output_lines.append("\n### Top 5 compounds:")
    top5 = df_results.head()
    for _, row in top5.iterrows():
        output_lines.append(f"- Rank {row['rank']}: {row['affinity_kcal_mol']:.2f} kcal/mol - {row['smiles'][:60]}")
    
    return "\n".join(output_lines)
