#!/usr/bin/env python3
"""
虚拟筛选技能
自动化分子对接和化合物筛选
"""
from typing import List, Dict, Optional, Tuple
import os
import subprocess
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from rdkit import Chem
from rdkit.Chem import AllChem

logger = logging.getLogger(__name__)

class AutoDockVinaRunner:
    """AutoDock Vina分子对接运行器"""
    
    def __init__(self, vina_path: str = "vina", prepare_ligand_path: str = "prepare_ligand4.py", 
                 prepare_receptor_path: str = "prepare_receptor4.py"):
        self.vina_path = vina_path
        self.prepare_ligand_path = prepare_ligand_path
        self.prepare_receptor_path = prepare_receptor_path
        
        # 检查依赖
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """检查依赖是否安装"""
        try:
            subprocess.run([self.vina_path, "--help"], capture_output=True, check=True)
        except:
            logger.warning("AutoDock Vina未找到，部分功能可能不可用")
        
        try:
            import pymol
        except ImportError:
            logger.warning("PyMOL未安装，部分功能可能不可用")
    
    def prepare_receptor(self, pdb_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        准备受体蛋白（加氢、去水、加电荷）
        
        Args:
            pdb_path: 受体PDB文件路径
            output_path: 输出PDBQT文件路径
            
        Returns:
            处理后的PDBQT文件路径
        """
        if output_path is None:
            output_path = Path(pdb_path).with_suffix('.pdbqt').as_posix()
        
        try:
            cmd = [
                'python', self.prepare_receptor_path,
                '-r', pdb_path,
                '-o', output_path,
                '-U', 'nphs_lps_waters'  # 去除非极性氢、孤对电子、水分子
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"受体准备完成: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"受体准备失败: {str(e)}, stderr: {e.stderr}")
            return None
    
    def prepare_ligand(self, smiles: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        准备配体分子（生成3D构象、加电荷）
        
        Args:
            smiles: 配体SMILES字符串
            output_path: 输出PDBQT文件路径
            
        Returns:
            处理后的PDBQT文件路径
        """
        try:
            # 生成3D构象
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.error(f"无效的SMILES: {smiles}")
                return None
            
            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, randomSeed=42)
            AllChem.UFFOptimizeMolecule(mol)
            
            # 保存为临时SDF文件
            with tempfile.NamedTemporaryFile(suffix='.sdf', delete=False) as tmp:
                writer = Chem.SDWriter(tmp.name)
                writer.write(mol)
                writer.close()
                sdf_path = tmp.name
            
            if output_path is None:
                output_path = Path(sdf_path).with_suffix('.pdbqt').as_posix()
            
            # 使用MGLTools准备配体
            cmd = [
                'python', self.prepare_ligand_path,
                '-l', sdf_path,
                '-o', output_path,
                '-U', 'nphs_lps'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # 清理临时文件
            os.unlink(sdf_path)
            
            logger.debug(f"配体准备完成: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"配体准备失败: {smiles}, 错误: {str(e)}")
            return None
    
    def run_docking(self, receptor_pdbqt: str, ligand_pdbqt: str, 
                   center: Tuple[float, float, float], size: Tuple[float, float, float],
                   num_modes: int = 9, exhaustiveness: int = 8) -> Optional[Dict]:
        """
        运行分子对接
        
        Args:
            receptor_pdbqt: 受体PDBQT文件路径
            ligand_pdbqt: 配体PDBQT文件路径
            center: 对接盒子中心 (x, y, z)
            size: 对接盒子大小 (x, y, z)
            num_modes: 输出构象数量
            exhaustiveness: 搜索 exhaustive 值
            
        Returns:
            对接结果，包含结合能等信息
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
                output_path = tmp.name
            
            cmd = [
                self.vina_path,
                '--receptor', receptor_pdbqt,
                '--ligand', ligand_pdbqt,
                '--center_x', str(center[0]),
                '--center_y', str(center[1]),
                '--center_z', str(center[2]),
                '--size_x', str(size[0]),
                '--size_y', str(size[1]),
                '--size_z', str(size[2]),
                '--num_modes', str(num_modes),
                '--exhaustiveness', str(exhaustiveness),
                '--out', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # 解析结果
            binding_affinity = None
            modes = []
            
            with open(output_path, 'r') as f:
                for line in f:
                    if line.startswith('Affinity:'):
                        binding_affinity = float(line.split()[1])
                    elif line.strip() and line[0].isdigit():
                        parts = line.split()
                        if len(parts) >= 4:
                            modes.append({
                                'mode': int(parts[0]),
                                'affinity': float(parts[1]),
                                'rmsd_lb': float(parts[2]),
                                'rmsd_ub': float(parts[3])
                            })
            
            # 清理临时文件
            os.unlink(output_path)
            
            return {
                'binding_affinity': binding_affinity,
                'modes': modes,
                'best_affinity': min(m['affinity'] for m in modes) if modes else None
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"对接失败: {str(e)}, stderr: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"解析对接结果失败: {str(e)}")
            return None

class VirtualScreeningWorkflow:
    """虚拟筛选工作流"""
    
    def __init__(self):
        self.vina_runner = AutoDockVinaRunner()
        from ..utils.chem_utils import filter_library_by_properties, calculate_molecular_properties
        from ..utils.ml_utils import ADMETPredictor
        
        self.filter_library = filter_library_by_properties
        self.calculate_properties = calculate_molecular_properties
        self.admet_predictor = ADMETPredictor()
    
    def run_screening(self, target_pdb: str, smiles_list: List[str], 
                     binding_site: Dict, output_path: str = "screening_results.csv",
                     admet_filter: bool = True, property_filter: bool = True) -> pd.DataFrame:
        """
        运行虚拟筛选工作流
        
        Args:
            target_pdb: 靶点PDB文件路径
            smiles_list: 待筛选的SMILES列表
            binding_site: 结合位点信息，包含center和size
            output_path: 结果输出路径
            admet_filter: 是否进行ADMET过滤
            property_filter: 是否进行类药性质过滤
            
        Returns:
            筛选结果DataFrame
        """
        logger.info(f"开始虚拟筛选，共 {len(smiles_list)} 个化合物")
        
        # 1. 性质过滤
        if property_filter:
            logger.info("第一步：类药性质过滤")
            filtered_smiles = self.filter_library(smiles_list)
            logger.info(f"性质过滤后剩余 {len(filtered_smiles)} 个化合物")
        else:
            filtered_smiles = smiles_list
        
        # 2. ADMET过滤
        if admet_filter:
            logger.info("第二步：ADMET性质预测和过滤")
            admet_filtered = []
            for smiles in filtered_smiles:
                admet_result = self.admet_predictor.predict_all(smiles)
                if admet_result.get('admet_risk_assessment') in ['低风险', '中风险']:
                    admet_filtered.append(smiles)
            
            filtered_smiles = admet_filtered
            logger.info(f"ADMET过滤后剩余 {len(filtered_smiles)} 个化合物")
        
        if not filtered_smiles:
            logger.warning("没有化合物通过过滤步骤")
            return pd.DataFrame()
        
        # 3. 准备受体
        logger.info("第三步：准备受体蛋白")
        receptor_pdbqt = self.vina_runner.prepare_receptor(target_pdb)
        if not receptor_pdbqt:
            logger.error("受体制备失败")
            return pd.DataFrame()
        
        # 4. 批量对接
        logger.info("第四步：批量分子对接")
        results = []
        
        for i, smiles in enumerate(filtered_smiles):
            logger.info(f"对接进度: {i+1}/{len(filtered_smiles)}")
            
            # 准备配体
            ligand_pdbqt = self.vina_runner.prepare_ligand(smiles)
            if not ligand_pdbqt:
                continue
            
            # 运行对接
            docking_result = self.vina_runner.run_docking(
                receptor_pdbqt,
                ligand_pdbqt,
                center=binding_site['center'],
                size=binding_site['size']
            )
            
            if docking_result and docking_result.get('best_affinity'):
                # 计算其他性质
                props = self.calculate_properties(smiles)
                admet = self.admet_predictor.predict_all(smiles)
                
                result = {
                    'smiles': smiles,
                    'binding_affinity': docking_result['best_affinity'],
                    'rank': i + 1
                }
                result.update(props)
                result.update(admet)
                
                results.append(result)
            
            # 清理临时文件
            if ligand_pdbqt and os.path.exists(ligand_pdbqt):
                os.unlink(ligand_pdbqt)
        
        # 5. 结果排序和保存
        logger.info("第五步：结果整理和排序")
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('binding_affinity', ascending=True)
            df['rank'] = range(1, len(df) + 1)
            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"筛选完成，共 {len(df)} 个化合物，结果已保存到: {output_path}")
        
        return df
    
    def get_top_candidates(self, results_df: pd.DataFrame, top_n: int = 20, 
                          max_affinity: float = -7.0) -> pd.DataFrame:
        """
        获取Top N候选化合物
        
        Args:
            results_df: 筛选结果DataFrame
            top_n: 返回数量
            max_affinity: 最大结合能阈值（越小结合越强）
            
        Returns:
            Top候选化合物DataFrame
        """
        if results_df.empty:
            return pd.DataFrame()
        
        filtered = results_df[results_df['binding_affinity'] <= max_affinity]
        top_candidates = filtered.head(top_n).copy()
        
        # 添加优先级评分
        top_candidates['priority_score'] = (
            -top_candidates['binding_affinity'] * 0.4 +  # 结合能权重40%
            top_candidates['qed'] * 0.3 +  # QED权重30%
            (1 - top_candidates['lipinski_violations'] / 4) * 0.3  # Lipinski规则权重30%
        )
        
        top_candidates = top_candidates.sort_values('priority_score', ascending=False)
        
        return top_candidates
    
    def generate_screening_report(self, results_df: pd.DataFrame, output_path: str) -> str:
        """
        生成筛选报告
        
        Args:
            results_df: 筛选结果DataFrame
            output_path: 报告输出路径
            
        Returns:
            报告路径
        """
        if results_df.empty:
            report_content = "# 虚拟筛选报告\n\n没有找到符合条件的化合物。"
        else:
            top_candidates = self.get_top_candidates(results_df)
            
            report_content = f"""# 虚拟筛选报告

## 筛选概述
- 总化合物数: {len(results_df)}
- 结合能范围: {results_df['binding_affinity'].min():.2f} ~ {results_df['binding_affinity'].max():.2f} kcal/mol
- 平均结合能: {results_df['binding_affinity'].mean():.2f} kcal/mol

## Top 20 候选化合物
{top_candidates[['rank', 'smiles', 'binding_affinity', 'molecular_weight', 'logp', 'qed', 'lipinski_violations', 'admet_risk_assessment']].to_markdown(index=False)}

## 性质分布
- 平均分子量: {results_df['molecular_weight'].mean():.1f}
- 平均LogP: {results_df['logp'].mean():.2f}
- 平均QED: {results_df['qed'].mean():.2f}
- Lipinski规则违反率: {(results_df['lipinski_violations'] > 1).mean() * 100:.1f}%
- ADMET高风险比例: {(results_df['admet_risk_assessment'] == '高风险').mean() * 100:.1f}%
"""
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"筛选报告已保存到: {output_path}")
        return output_path

# OpenClaw技能入口
def run_virtual_screening(target_pdb: str, library_file: str, 
                         binding_site_center: Tuple[float, float, float],
                         binding_site_size: Tuple[float, float, float] = (20, 20, 20),
                         output: str = "screening_results.csv",
                         top_n: int = 20) -> Dict:
    """
    虚拟筛选技能入口
    
    Args:
        target_pdb: 靶点PDB文件路径
        library_file: 化合物库文件路径（CSV格式，包含smiles列）
        binding_site_center: 结合位点中心坐标 (x, y, z)
        binding_site_size: 结合位点盒子大小 (x, y, z)，默认20x20x20
        output: 结果输出路径
        top_n: 返回Top N候选化合物
        
    Returns:
        筛选结果
    """
    try:
        # 读取化合物库
        df = pd.read_csv(library_file)
        if 'smiles' not in df.columns:
            return {'error': '化合物库文件需要包含smiles列'}
        
        smiles_list = df['smiles'].tolist()
        
        # 运行筛选
        workflow = VirtualScreeningWorkflow()
        binding_site = {
            'center': binding_site_center,
            'size': binding_site_size
        }
        
        results_df = workflow.run_screening(
            target_pdb=target_pdb,
            smiles_list=smiles_list,
            binding_site=binding_site,
            output_path=output
        )
        
        if results_df.empty:
            return {'error': '没有化合物通过筛选'}
        
        # 生成报告
        report_path = output.replace('.csv', '_report.md')
        workflow.generate_screening_report(results_df, report_path)
        
        # 获取Top候选
        top_candidates = workflow.get_top_candidates(results_df, top_n=top_n)
        
        return {
            'total_compounds': len(results_df),
            'best_affinity': results_df['binding_affinity'].min(),
            'top_candidates': top_candidates.to_dict('records'),
            'results_path': output,
            'report_path': report_path
        }
    
    except Exception as e:
        logger.error(f"虚拟筛选失败: {str(e)}")
        return {'error': str(e)}

if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 5:
        print("Usage: python virtual_screening.py <target_pdb> <library_file> <center_x> <center_y> <center_z> [size_x size_y size_z] [output] [top_n]")
        sys.exit(1)
    
    target_pdb = sys.argv[1]
    library_file = sys.argv[2]
    center = (float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
    
    size = (20, 20, 20)
    if len(sys.argv) >= 9:
        size = (float(sys.argv[6]), float(sys.argv[7]), float(sys.argv[8]))
    
    output = sys.argv[9] if len(sys.argv) > 9 else "screening_results.csv"
    top_n = int(sys.argv[10]) if len(sys.argv) > 10 else 20
    
    result = run_virtual_screening(target_pdb, library_file, center, size, output, top_n)
    print(json.dumps(result, indent=2, ensure_ascii=False))