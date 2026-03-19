#!/usr/bin/env python3
"""
数据库对接工具函数
"""
from typing import List, Dict, Optional
import requests
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PubChemAPI:
    """PubChem API对接"""
    
    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    
    @classmethod
    def search_compound(cls, name: str, limit: int = 10) -> List[Dict]:
        """
        根据名称搜索化合物
        
        Args:
            name: 化合物名称
            limit: 返回结果数量
            
        Returns:
            化合物列表
        """
        try:
            url = f"{cls.BASE_URL}/compound/name/{name}/cids/JSON"
            params = {'list_return': 'flat', 'limit': limit}
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            cids = data.get('IdentifierList', {}).get('CID', [])
            
            compounds = []
            for cid in cids[:limit]:
                compound = cls.get_compound_by_cid(cid)
                if compound:
                    compounds.append(compound)
            
            return compounds
        except Exception as e:
            logger.error(f"PubChem搜索失败: {name}, 错误: {str(e)}")
            return []
    
    @classmethod
    def get_compound_by_cid(cls, cid: int) -> Optional[Dict]:
        """
        根据CID获取化合物信息
        
        Args:
            cid: PubChem CID
            
        Returns:
            化合物信息
        """
        try:
            url = f"{cls.BASE_URL}/compound/cid/{cid}/property/IUPACName,MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES/XLogP,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,TPSA/JSON"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            props = data.get('PropertyTable', {}).get('Properties', [])[0]
            
            return {
                'cid': cid,
                'iupac_name': props.get('IUPACName'),
                'molecular_formula': props.get('MolecularFormula'),
                'molecular_weight': props.get('MolecularWeight'),
                'canonical_smiles': props.get('CanonicalSMILES'),
                'isomeric_smiles': props.get('IsomericSMILES'),
                'logp': props.get('XLogP'),
                'h_donors': props.get('HBondDonorCount'),
                'h_acceptors': props.get('HBondAcceptorCount'),
                'rotatable_bonds': props.get('RotatableBondCount'),
                'tpsa': props.get('TPSA')
            }
        except Exception as e:
            logger.error(f"获取PubChem化合物信息失败: CID={cid}, 错误: {str(e)}")
            return None

class ChEMBLAPI:
    """ChEMBL API对接"""
    
    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
    
    @classmethod
    def get_target_by_name(cls, name: str, limit: int = 10) -> List[Dict]:
        """
        根据名称搜索靶点
        
        Args:
            name: 靶点名称
            limit: 返回结果数量
            
        Returns:
            靶点列表
        """
        try:
            url = f"{cls.BASE_URL}/target"
            params = {
                'target_synonym__icontains': name,
                'limit': limit,
                'format': 'json'
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            targets = data.get('targets', [])
            
            return [{
                'target_chembl_id': t.get('target_chembl_id'),
                'pref_name': t.get('pref_name'),
                'organism': t.get('organism'),
                'target_type': t.get('target_type'),
                'description': t.get('description')
            } for t in targets]
        except Exception as e:
            logger.error(f"ChEMBL靶点搜索失败: {name}, 错误: {str(e)}")
            return []
    
    @classmethod
    def get_activity_by_target(cls, target_chembl_id: str, limit: int = 100) -> List[Dict]:
        """
        获取靶点的活性数据
        
        Args:
            target_chembl_id: ChEMBL靶点ID
            limit: 返回结果数量
            
        Returns:
            活性数据列表
        """
        try:
            url = f"{cls.BASE_URL}/activity"
            params = {
                'target_chembl_id': target_chembl_id,
                'limit': limit,
                'format': 'json'
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            activities = data.get('activities', [])
            
            return [{
                'activity_id': a.get('activity_id'),
                'molecule_chembl_id': a.get('molecule_chembl_id'),
                'canonical_smiles': a.get('canonical_smiles'),
                'standard_type': a.get('standard_type'),
                'standard_value': a.get('standard_value'),
                'standard_units': a.get('standard_units'),
                'pchembl_value': a.get('pchembl_value')
            } for a in activities if a.get('pchembl_value')]
        except Exception as e:
            logger.error(f"获取ChEMBL活性数据失败: {target_chembl_id}, 错误: {str(e)}")
            return []

class ZINCDownloader:
    """ZINC数据库下载工具"""
    
    BASE_URL = "https://zinc.docking.org"
    
    @classmethod
    def download_library(cls, library_name: str, output_dir: str = "./data") -> Optional[str]:
        """
        下载ZINC化合物库
        
        Args:
            library_name: 库名称 (e.g., 'zinc12_fragments', 'zinc12_leads')
            output_dir: 输出目录
            
        Returns:
            下载的文件路径
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 这里需要根据实际ZINC下载链接实现
            logger.warning("ZINC下载功能需要根据实际API实现")
            return None
        except Exception as e:
            logger.error(f"下载ZINC库失败: {library_name}, 错误: {str(e)}")
            return None