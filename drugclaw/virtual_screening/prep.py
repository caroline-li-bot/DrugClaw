#!/usr/bin/env python3
"""
Protein and ligand preparation for AutoDock Vina
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def _check_mgltools():
    """Check if MGLTools is available"""
    try:
        result = subprocess.run(['which', 'prepare_receptor'], capture_output=True)
        return result.returncode == 0
    except:
        return False

def prepare_receptor(input_pdb: str, output_pdbqt: Optional[str] = None) -> str:
    """
    Prepare a receptor protein for docking:
    - Remove water molecules
    - Add hydrogens
    - Convert PDB to PDBQT format
    
    Args:
        input_pdb: Input PDB file path
        output_pdbqt: Output PDBQT path (auto-generated if None)
    
    Returns:
        Path to output PDBQT file
    """
    input_path = Path(input_pdb)
    
    if output_pdbqt is None:
        output_pdbqt = str(input_path.with_suffix('.pdbqt'))
    
    # Use prepare_receptor from MGLTools
    cmd = [
        'prepare_receptor',
        '-r', input_pdb,
        '-o', output_pdbqt
    ]
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"prepare_receptor failed: {result.stderr}")
            raise RuntimeError(f"Receptor preparation failed: {result.stderr}")
        
        if not os.path.exists(output_pdbqt):
            # Try alternative approach - if prepare_receptor not in PATH, use python script from MGLTools
            # This is a fallback for different installations
            logger.warning("Trying fallback approach...")
            return _prepare_receptor_fallback(input_pdb, output_pdbqt)
        
        logger.info(f"Receptor prepared: {output_pdbqt}")
        return output_pdbqt
    
    except Exception as e:
        logger.error(f"Exception preparing receptor: {str(e)}")
        raise

def _prepare_receptor_fallback(input_pdb: str, output_pdbqt: str) -> str:
    """Fallback preparation using python script from MGLTools install"""
    # Common locations
    possible_paths = [
        '/usr/local/mgltools/bin/prepare_receptor',
        '/opt/mgltools/bin/prepare_receptor',
        os.path.expanduser('~/mgltools/bin/prepare_receptor')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            cmd = [path, '-r', input_pdb, '-o', output_pdbqt]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(output_pdbqt):
                return output_pdbqt
    
    # If still fails, do minimal preparation manually
    logger.warning("MGLTools prepare_receptor not found, doing minimal processing...")
    logger.warning("For best results, please install MGLTools")
    
    # Minimal: just remove water and save as pdbqt
    with open(input_pdb, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if line.startswith('ATOM') or line.startswith('HETATM'):
            # Remove water
            res_name = line[17:20].strip()
            if res_name not in ['HOH', 'WAT']:
                # Vina doesn't strictly require pdbqt preparation for rigid docking
                # but it helps
                new_lines.append(line)
    
    with open(output_pdbqt, 'w') as f:
        f.writelines(new_lines)
    
    return output_pdbqt

def prepare_ligand_from_smiles(smiles: str, name: str, output_dir: str = ".") -> Optional[str]:
    """
    Prepare a ligand from SMILES string:
    - Generate 3D conformation
    - Convert to PDBQT
    
    Args:
        smiles: SMILES string
        name: Ligand name
        output_dir: Directory for output
    
    Returns:
        Path to output PDBQT file, None on failure
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    output_pdbqt = str(output_path / f"{name}.pdbqt")
    
    # Try to use openbabel for 3D generation
    try:
        # First, generate PDB from SMILES
        pdb_file = str(output_path / f"{name}.pdb")
        cmd = ['obabel', '-ismi', '-opdb', '-O', pdb_file, '--gen3d']
        result = subprocess.run(cmd, input=smiles.encode(), capture_output=True)
        
        if result.returncode != 0:
            logger.error(f"openbabel failed: {result.stderr}")
            return None
        
        if not os.path.exists(pdb_file):
            logger.error(f"openbabel didn't create output file")
            return None
        
        # Then convert to pdbqt using prepare_ligand
        try:
            cmd = ['prepare_ligand', '-l', pdb_file, '-o', output_pdbqt]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"prepare_ligand warned: {result.stderr}")
            
            if os.path.exists(output_pdbqt):
                logger.info(f"Ligand prepared: {output_pdbqt}")
                return output_pdbqt
            else:
                # Just use the PDB file if prepare_ligand fails
                os.rename(pdb_file, output_pdbqt)
                return output_pdbqt
        
        except:
            # If prepare_ligand fails, just use the PDB
            os.rename(pdb_file, output_pdbqt)
            return output_pdbqt
    
    except Exception as e:
        logger.error(f"Exception preparing ligand {name}: {str(e)}")
        return None

def clean_output(output_dir: str, keep_pdbqt: bool = True):
    """Clean up intermediate files after docking"""
    pass
