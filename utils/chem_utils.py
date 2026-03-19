#!/usr/bin/env python3
"""
化学信息学工具函数
"""
from typing import List, Dict, Optional, Union
import rdkit
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, Crippen, QED
import pubchempy as pcp
import logging

logger = logging.getLogger(__name__)

def smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """
    将SMILES字符串转换为RDKit Mol对象
    
    Args:
        smiles: SMILES字符串
        
    Returns:
        Mol对象或None(转换失败)
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"无效的SMILES: {smiles}")
        return mol
    except Exception as e:
        logger.error(f"SMILES转换失败: {smiles}, 错误: {str(e)}")
        return None

def calculate_molecular_properties(smiles: str) -> Dict:
    """
    计算分子基本性质
    
    Args:
        smiles: SMILES字符串
        
    Returns:
        包含分子性质的字典
    """
    mol = smiles_to_mol(smiles)
    if mol is None:
        return {}
    
    try:
        properties = {
            'smiles': smiles,
            'molecular_weight': Descriptors.MolWt(mol),
            'logp': Crippen.MolLogP(mol),
            'h_donors': Lipinski.NumHDonors(mol),
            'h_acceptors': Lipinski.NumHAcceptors(mol),
            'rotatable_bonds': Lipinski.NumRotatableBonds(mol),
            'tpsa': Descriptors.TPSA(mol),
            'qed': QED.qed(mol),
            'ring_count': Lipinski.RingCount(mol),
            'aromatic_rings': Lipinski.NumAromaticRings(mol),
            'heavy_atoms': Lipinski.HeavyAtomCount(mol)
        }
        
        # Lipinski规则评估
        lipinski_violations = 0
        if properties['molecular_weight'] > 500: lipinski_violations +=1
        if properties['logp'] > 5: lipinski_violations +=1
        if properties['h_donors'] > 5: lipinski_violations +=1
        if properties['h_acceptors'] > 10: lipinski_violations +=1
        
        properties['lipinski_violations'] = lipinski_violations
        properties['follows_lipinski'] = lipinski_violations <= 1
        
        return properties
    except Exception as e:
        logger.error(f"计算分子性质失败: {smiles}, 错误: {str(e)}")
        return {}

def get_compound_info_from_pubchem(cid: Union[int, str]) -> Dict:
    """
    从PubChem获取化合物信息
    
    Args:
        cid: PubChem CID
        
    Returns:
        化合物信息字典
    """
    try:
        compound = pcp.Compound.from_cid(cid)
        if not compound:
            return {}
            
        return {
            'cid': compound.cid,
            'iupac_name': compound.iupac_name,
            'molecular_formula': compound.molecular_formula,
            'molecular_weight': compound.molecular_weight,
            'smiles': compound.isomeric_smiles,
            'synonyms': compound.synonyms[:5] if compound.synonyms else [],
            'cas': [syn for syn in compound.synonyms if 'CAS' in syn][0] if compound.synonyms else None
        }
    except Exception as e:
        logger.error(f"获取PubChem信息失败: CID={cid}, 错误: {str(e)}")
        return {}

def filter_library_by_properties(
    smiles_list: List[str],
    min_weight: float = 100,
    max_weight: float = 500,
    max_logp: float = 5,
    max_h_donors: int = 5,
    max_h_acceptors: int = 10,
    max_rotatable_bonds: int = 10,
    min_qed: float = 0.3
) -> List[str]:
    """
    根据类药性质过滤化合物库
    
    Args:
        smiles_list: SMILES列表
        min_weight: 最小分子量
        max_weight: 最大分子量
        max_logp: 最大LogP
        max_h_donors: 最大氢键供体数
        max_h_acceptors: 最大氢键受体数
        max_rotatable_bonds: 最大可旋转键数
        min_qed: 最小QED值
        
    Returns:
        符合条件的SMILES列表
    """
    filtered = []
    
    for smiles in smiles_list:
        props = calculate_molecular_properties(smiles)
        if not props:
            continue
            
        if (props['molecular_weight'] >= min_weight and
            props['molecular_weight'] <= max_weight and
            props['logp'] <= max_logp and
            props['h_donors'] <= max_h_donors and
            props['h_acceptors'] <= max_h_acceptors and
            props['rotatable_bonds'] <= max_rotatable_bonds and
            props['qed'] >= min_qed):
            filtered.append(smiles)
    
    logger.info(f"过滤前: {len(smiles_list)}个化合物, 过滤后: {len(filtered)}个化合物")
    return filtered