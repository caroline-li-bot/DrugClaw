#!/usr/bin/env python3
"""
Run AutoDock Vina docking
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def _check_vina():
    """Check if vina is available"""
    try:
        result = subprocess.run(['vina', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Found Vina: {result.stdout.strip()}")
            return True
        return False
    except:
        return False

def run_vina_docking(
    receptor_pdbqt: str,
    ligand_pdbqt: str,
    center: Tuple[float, float, float],
    box_size: Tuple[float, float, float],
    cpu: int = 1,
    exhaustiveness: int = 8,
    output_dir: str = "./docking_output",
    vina_path: str = "vina"
) -> Optional[float]:
    """
    Run AutoDock Vina docking for a single ligand
    
    Args:
        receptor_pdbqt: Path to prepared receptor PDBQT
        ligand_pdbqt: Path to prepared ligand PDBQT
        center: (x, y, z) binding pocket center
        box_size: (size_x, size_y, size_z) box dimensions in Angstrom
        cpu: Number of CPUs to use
        exhaustiveness: Vina exhaustiveness parameter
        output_dir: Directory for output
        vina_path: Path to vina executable
    
    Returns:
        Best binding affinity (kcal/mol), None on failure
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    ligand_name = Path(ligand_pdbqt).stem
    output_pdbqt = str(output_path / f"{ligand_name}_out.pdbqt")
    log_path = str(output_path / f"{ligand_name}_log.txt")
    
    cmd = [
        vina_path,
        '--receptor', receptor_pdbqt,
        '--ligand', ligand_pdbqt,
        '--center_x', str(center[0]),
        '--center_y', str(center[1]),
        '--center_z', str(center[2]),
        '--size_x', str(box_size[0]),
        '--size_y', str(box_size[1]),
        '--size_z', str(box_size[2]),
        '--exhaustiveness', str(exhaustiveness),
        '--cpu', str(cpu),
        '--out', output_pdbqt,
        '--log', log_path
    ]
    
    logger.info(f"Running docking for {ligand_name}: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Docking failed for {ligand_name}: {result.stderr}")
            return None
        
        # Parse best affinity from log
        best_affinity = _parse_affinity_from_log(log_path)
        logger.info(f"Docking complete for {ligand_name}, best affinity: {best_affinity:.2f} kcal/mol")
        
        return best_affinity
    
    except Exception as e:
        logger.error(f"Exception docking {ligand_name}: {str(e)}")
        return None

def _parse_affinity_from_log(log_path: str) -> float:
    """Parse the best binding affinity from Vina log file"""
    best_affinity = None
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    # Look for the table of modes
    in_table = False
    for line in lines:
        line = line.strip()
        if line.startswith('mode'):
            in_table = True
            continue
        if in_table and line and not line.startswith('----'):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    affinity = float(parts[0])
                    if best_affinity is None or affinity < best_affinity:
                        best_affinity = affinity
                except:
                    pass
    
    return best_affinity if best_affinity is not None else 0.0

def run_batch_docking(
    receptor_pdbqt: str,
    ligands: list,
    center: Tuple[float, float, float],
    box_size: Tuple[float, float, float],
    output_dir: str = "./docking_output",
    cpu_per_ligand: int = 1,
    max_parallel: int = 4
) -> list:
    """
    Run batch docking for multiple ligands
    
    This is a simple implementation that processes ligands sequentially.
    For large libraries, you'd want to use parallel processing across multiple cores.
    
    Args:
        receptor_pdbqt: Prepared receptor
        ligands: List of (idx, smiles, ligand_pdbqt)
        center: Binding pocket center
        box_size: Box size
        output_dir: Output directory
        max_parallel: Maximum parallel processes
    
    Returns:
        List of (idx, smiles, affinity) results
    """
    results = []
    
    for idx, smiles, ligand_pdbqt in ligands:
        affinity = run_vina_docking(
            receptor_pdbqt, ligand_pdbqt,
            center, box_size,
            cpu=cpu_per_ligand,
            output_dir=output_dir
        )
        if affinity is not None:
            results.append((idx, smiles, affinity))
    
    return results
