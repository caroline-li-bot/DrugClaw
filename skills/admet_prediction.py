#!/usr/bin/env python3
"""
ADMET性质预测技能
预测化合物的吸收、分布、代谢、排泄和毒性性质
"""
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ADMETPredictor:
    """ADMET性质预测器"""
    
    def __init__(self):
        from ..utils.chem_utils import calculate_molecular_properties
        from ..utils.ml_utils import ChemBERTaPredictor
        
        self.calculate_physchem = calculate_molecular_properties
        self.chemberta = ChemBERTaPredictor()
        
        # 加载规则模型
        self._load_rule_models()
    
    def _load_rule_models(self) -> None:
        """加载基于规则的预测模型"""
        # 血脑屏障穿透规则
        self.bbb_rules = {
            'max_mw': 450,
            'max_logp': 4.0,
            'min_logp': 0.4,
            'max_hba': 8,
            'max_hbd': 3,
            'max_tpsa': 90,
            'max_rotatable_bonds': 9
        }
        
        # 口服生物利用度规则
        self.oral_bioavailability_rules = {
            'max_mw': 500,
            'max_logp': 5,
            'max_hba': 10,
            'max_hbd': 5,
            'max_rotatable_bonds': 10,
            'max_tpsa': 140
        }
        
        # 肝毒性结构警示
        self.hepatotoxic_alerts = [
            'aniline', 'nitro', 'thioamide', 'hydrazine',
            'epoxide', 'aziridine', 'sulfonyl_halide'
        ]
    
    def predict_absorption(self, props: Dict) -> Dict:
        """预测吸收性质"""
        results = {}
        
        # 口服生物利用度预测
        violations = 0
        rules = self.oral_bioavailability_rules
        
        if props['molecular_weight'] > rules['max_mw']: violations += 1
        if props['logp'] > rules['max_logp']: violations += 1
        if props['h_acceptors'] > rules['max_hba']: violations += 1
        if props['h_donors'] > rules['max_hbd']: violations += 1
        if props['rotatable_bonds'] > rules['max_rotatable_bonds']: violations += 1
        if props['tpsa'] > rules['max_tpsa']: violations += 1
        
        if violations <= 1:
            results['oral_bioavailability'] = '高'
            results['oral_bioavailability_score'] = 0.8 + (1 - violations/10) * 0.2
        elif violations <= 3:
            results['oral_bioavailability'] = '中'
            results['oral_bioavailability_score'] = 0.4 + (3 - violations/10) * 0.4
        else:
            results['oral_bioavailability'] = '低'
            results['oral_bioavailability_score'] = violations / 10
        
        # Caco-2渗透性预测
        if props['tpsa'] < 140 and props['logp'] > 0 and props['logp'] < 6:
            results['caco2_permeability'] = '高'
        else:
            results['caco2_permeability'] = '低'
        
        # 肠道吸收预测
        if props['tpsa'] < 120:
            results['intestinal_absorption'] = '高'
        elif props['tpsa'] < 200:
            results['intestinal_absorption'] = '中'
        else:
            results['intestinal_absorption'] = '低'
        
        return results
    
    def predict_distribution(self, props: Dict) -> Dict:
        """预测分布性质"""
        results = {}
        
        # 血脑屏障穿透预测
        violations = 0
        rules = self.bbb_rules
        
        if props['molecular_weight'] > rules['max_mw']: violations += 1
        if props['logp'] > rules['max_logp'] or props['logp'] < rules['min_logp']: violations += 1
        if props['h_acceptors'] > rules['max_hba']: violations += 1
        if props['h_donors'] > rules['max_hbd']: violations += 1
        if props['tpsa'] > rules['max_tpsa']: violations += 1
        if props['rotatable_bonds'] > rules['max_rotatable_bonds']: violations += 1
        
        if violations == 0:
            results['bbb_permeability'] = '高'
            results['bbb_score'] = 0.9
        elif violations <= 2:
            results['bbb_permeability'] = '中'
            results['bbb_score'] = 0.7 - violations * 0.2
        else:
            results['bbb_permeability'] = '低'
            results['bbb_score'] = max(0, 0.3 - violations * 0.1)
        
        # 血浆蛋白结合率预测
        if props['logp'] > 3:
            results['plasma_protein_binding'] = '高'
        elif props['logp'] > 1:
            results['plasma_protein_binding'] = '中'
        else:
            results['plasma_protein_binding'] = '低'
        
        # 表观分布容积预测
        if props['logp'] > 2 and props['tpsa'] < 70:
            results['volume_of_distribution'] = '高'
        else:
            results['volume_of_distribution'] = '低'
        
        return results
    
    def predict_metabolism(self, smiles: str, props: Dict) -> Dict:
        """预测代谢性质"""
        results = {}
        
        # CYP抑制剂预测（基于规则）
        cyp_inhibitors = []
        
        # CYP3A4抑制剂警示
        if props['logp'] > 3 and props['molecular_weight'] > 300:
            cyp_inhibitors.append('CYP3A4')
        
        # CYP2D6抑制剂警示
        if props['h_donors'] > 0 and props['logp'] > 2:
            cyp_inhibitors.append('CYP2D6')
        
        # CYP2C9抑制剂警示
        if props['logp'] > 2.5 and props['tpsa'] < 100:
            cyp_inhibitors.append('CYP2C9')
        
        results['cyp_inhibitors'] = cyp_inhibitors if cyp_inhibitors else ['无']
        results['cyp_inhibition_risk'] = '高' if len(cyp_inhibitors) >= 2 else '中' if len(cyp_inhibitors) == 1 else '低'
        
        # 代谢稳定性预测
        if props['aromatic_rings'] >= 3 and props['logp'] > 3:
            results['metabolic_stability'] = '低'
        elif props['rotatable_bonds'] <= 5 and props['logp'] < 3:
            results['metabolic_stability'] = '高'
        else:
            results['metabolic_stability'] = '中'
        
        return results
    
    def predict_excretion(self, props: Dict) -> Dict:
        """预测排泄性质"""
        results = {}
        
        # 肾清除率预测
        if props['molecular_weight'] < 300 and props['tpsa'] > 60:
            results['renal_clearance'] = '高'
        else:
            results['renal_clearance'] = '低'
        
        # 胆汁排泄预测
        if props['molecular_weight'] > 400 and props['logp'] > 2:
            results['biliary_excretion'] = '高'
        else:
            results['biliary_excretion'] = '低'
        
        # 半衰期预测
        if props['logp'] > 3 and props['plasma_protein_binding'] == '高':
            results['half_life'] = '长'
        else:
            results['half_life'] = '中短'
        
        return results
    
    def predict_toxicity(self, smiles: str, props: Dict) -> Dict:
        """预测毒性性质"""
        results = {}
        
        # 基于AI的毒性预测
        ai_predictions = self.chemberta.predict_properties(smiles)
        
        # 肝毒性预测
        hepato_toxicity_score = ai_predictions.get('toxicity', 0.5)
        
        # 检查结构警示
        has_hepatic_alert = False
        # 这里需要实现结构警示检查逻辑
        # for alert in self.hepatotoxic_alerts:
        #     if has_substructure(smiles, alert):
        #         has_hepatic_alert = True
        #         break
        
        if has_hepatic_alert or hepato_toxicity_score > 0.7:
            results['hepatotoxicity'] = '高风险'
            results['hepatotoxicity_score'] = max(hepato_toxicity_score, 0.8)
        elif hepato_toxicity_score > 0.3:
            results['hepatotoxicity'] = '中风险'
            results['hepatotoxicity_score'] = hepato_toxicity_score
        else:
            results['hepatotoxicity'] = '低风险'
            results['hepatotoxicity_score'] = hepato_toxicity_score
        
        # 心脏毒性（hERG抑制）预测
        if props['logp'] > 3 and props['h_donors'] <= 2 and props['molecular_weight'] > 350:
            results['herg_inhibition'] = '高风险'
            results['herg_score'] = 0.8
        elif props['logp'] > 2:
            results['herg_inhibition'] = '中风险'
            results['herg_score'] = 0.5
        else:
            results['herg_inhibition'] = '低风险'
            results['herg_score'] = 0.2
        
        # 致突变性预测（Ames试验）
        if 'nitro' in smiles.lower() or 'azide' in smiles.lower():
            results['ames_mutagenicity'] = '阳性'
            results['ames_score'] = 0.9
        else:
            results['ames_mutagenicity'] = '阴性'
            results['ames_score'] = 0.1
        
        # 总体毒性风险
        toxicity_scores = [
            results['hepatotoxicity_score'],
            results['herg_score'],
            results['ames_score']
        ]
        avg_toxicity = np.mean(toxicity_scores)
        
        if avg_toxicity > 0.7:
            results['overall_toxicity_risk'] = '高'
        elif avg_toxicity > 0.4:
            results['overall_toxicity_risk'] = '中'
        else:
            results['overall_toxicity_risk'] = '低'
        
        return results
    
    def predict_all(self, smiles: str) -> Dict:
        """预测所有ADMET性质"""
        try:
            # 计算理化性质
            physchem_props = self.calculate_physchem(smiles)
            if not physchem_props:
                return {'error': '无效的SMILES字符串'}
            
            results = {
                'smiles': smiles,
                'physicochemical_properties': physchem_props
            }
            
            # 预测各类性质
            results['absorption'] = self.predict_absorption(physchem_props)
            results['distribution'] = self.predict_distribution(physchem_props)
            results['metabolism'] = self.predict_metabolism(smiles, physchem_props)
            results['excretion'] = self.predict_excretion(physchem_props)
            results['toxicity'] = self.predict_toxicity(smiles, physchem_props)
            
            # 综合评分
            results['overall_score'] = self._calculate_overall_score(results)
            results['admet_decision'] = self._make_decision(results['overall_score'])
            
            return results
        except Exception as e:
            logger.error(f"ADMET预测失败: {smiles}, 错误: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_overall_score(self, admet_results: Dict) -> float:
        """计算ADMET综合评分"""
        scores = []
        
        # 吸收评分 (权重 0.25)
        absorption_scores = {
            '高': 1.0,
            '中': 0.5,
            '低': 0.0
        }
        scores.append(absorption_scores[admet_results['absorption']['oral_bioavailability']] * 0.25)
        
        # 分布评分 (权重 0.2)
        bbb_score = admet_results['distribution']['bbb_score']
        scores.append(bbb_score * 0.2)
        
        # 代谢评分 (权重 0.2)
        metabolism_scores = {
            '高': 1.0,
            '中': 0.5,
            '低': 0.0
        }
        scores.append(metabolism_scores[admet_results['metabolism']['metabolic_stability']] * 0.2)
        
        # 排泄评分 (权重 0.15)
        # 这里简化处理，根据实际需求调整
        excretion_score = 0.5
        scores.append(excretion_score * 0.15)
        
        # 毒性评分 (权重 0.2)
        toxicity_risk = admet_results['toxicity']['overall_toxicity_risk']
        toxicity_score = 0.0 if toxicity_risk == '高' else 0.5 if toxicity_risk == '中' else 1.0
        scores.append(toxicity_score * 0.2)
        
        return round(sum(scores), 3)
    
    def _make_decision(self, overall_score: float) -> str:
        """根据综合评分做出决策"""
        if overall_score >= 0.8:
            return "优先开发"
        elif overall_score >= 0.6:
            return "进一步优化"
        elif overall_score >= 0.4:
            return "谨慎评估"
        else:
            return "建议淘汰"
    
    def batch_predict(self, smiles_list: List[str], output_path: Optional[str] = None) -> pd.DataFrame:
        """批量预测ADMET性质"""
        results = []
        
        for i, smiles in enumerate(smiles_list):
            logger.info(f"预测进度: {i+1}/{len(smiles_list)}")
            result = self.predict_all(smiles)
            if 'error' not in result:
                # 扁平化结果
                flat_result = {
                    'smiles': smiles,
                    'overall_score': result['overall_score'],
                    'admet_decision': result['admet_decision']
                }
                
                # 添加理化性质
                for k, v in result['physicochemical_properties'].items():
                    flat_result[f'physchem_{k}'] = v
                
                # 添加吸收性质
                for k, v in result['absorption'].items():
                    flat_result[f'absorption_{k}'] = v
                
                # 添加分布性质
                for k, v in result['distribution'].items():
                    flat_result[f'distribution_{k}'] = v
                
                # 添加代谢性质
                for k, v in result['metabolism'].items():
                    if isinstance(v, list):
                        flat_result[f'metabolism_{k}'] = ','.join(v)
                    else:
                        flat_result[f'metabolism_{k}'] = v
                
                # 添加排泄性质
                for k, v in result['excretion'].items():
                    flat_result[f'excretion_{k}'] = v
                
                # 添加毒性性质
                for k, v in result['toxicity'].items():
                    flat_result[f'toxicity_{k}'] = v
                
                results.append(flat_result)
        
        df = pd.DataFrame(results)
        
        if output_path and not df.empty:
            df.to_csv(output_path, index=False, encoding='utf-8')
            logger.info(f"批量预测结果已保存到: {output_path}")
        
        return df
    
    def generate_report(self, admet_results: Dict, output_path: str) -> str:
        """生成ADMET预测报告"""
        if 'error' in admet_results:
            report_content = f"# ADMET预测报告\n\n错误: {admet_results['error']}"
        else:
            report_content = f"""# ADMET性质预测报告

## 基本信息
- SMILES: {admet_results['smiles']}
- 预测时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
- 综合评分: {admet_results['overall_score']}
- 决策建议: **{admet_results['admet_decision']}**

## 理化性质
| 性质 | 值 |
|------|----|
| 分子量 | {admet_results['physicochemical_properties']['molecular_weight']:.1f} |
| LogP | {admet_results['physicochemical_properties']['logp']:.2f} |
| 氢键供体 | {admet_results['physicochemical_properties']['h_donors']} |
| 氢键受体 | {admet_results['physicochemical_properties']['h_acceptors']} |
| 可旋转键 | {admet_results['physicochemical_properties']['rotatable_bonds']} |
| TPSA | {admet_results['physicochemical_properties']['tpsa']:.1f} |
| QED | {admet_results['physicochemical_properties']['qed']:.3f} |
| Lipinski规则违反 | {admet_results['physicochemical_properties']['lipinski_violations']} |
| 是否符合Lipinski规则 | {'是' if admet_results['physicochemical_properties']['follows_lipinski'] else '否'} |

## 吸收性质
| 性质 | 预测结果 |
|------|----------|
| 口服生物利用度 | {admet_results['absorption']['oral_bioavailability']} |
| 口服生物利用度评分 | {admet_results['absorption']['oral_bioavailability_score']:.2f} |
| Caco-2渗透性 | {admet_results['absorption']['caco2_permeability']} |
| 肠道吸收 | {admet_results['absorption']['intestinal_absorption']} |

## 分布性质
| 性质 | 预测结果 |
|------|----------|
| 血脑屏障穿透性 | {admet_results['distribution']['bbb_permeability']} |
| BBB评分 | {admet_results['distribution']['bbb_score']:.2f} |
| 血浆蛋白结合率 | {admet_results['distribution']['plasma_protein_binding']} |
| 表观分布容积 | {admet_results['distribution']['volume_of_distribution']} |

## 代谢性质
| 性质 | 预测结果 |
|------|----------|
| CYP抑制剂 | {','.join(admet_results['metabolism']['cyp_inhibitors'])} |
| CYP抑制风险 | {admet_results['metabolism']['cyp_inhibition_risk']} |
| 代谢稳定性 | {admet_results['metabolism']['metabolic_stability']} |

## 排泄性质
| 性质 | 预测结果 |
|------|----------|
| 肾清除率 | {admet_results['excretion']['renal_clearance']} |
| 胆汁排泄 | {admet_results['excretion']['biliary_excretion']} |
| 半衰期 | {admet_results['excretion']['half_life']} |

## 毒性性质
| 性质 | 预测结果 |
|------|----------|
| 肝毒性 | {admet_results['toxicity']['hepatotoxicity']} |
| 肝毒性评分 | {admet_results['toxicity']['hepatotoxicity_score']:.2f} |
| hERG抑制 | {admet_results['toxicity']['herg_inhibition']} |
| hERG评分 | {admet_results['toxicity']['herg_score']:.2f} |
| Ames致突变性 | {admet_results['toxicity']['ames_mutagenicity']} |
| Ames评分 | {admet_results['toxicity']['ames_score']:.2f} |
| 总体毒性风险 | {admet_results['toxicity']['overall_toxicity_risk']} |
"""
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"ADMET报告已保存到: {output_path}")
        return output_path

# OpenClaw技能入口
def run_admet_prediction(smiles: Optional[str] = None, input_file: Optional[str] = None, 
                        output: str = "admet_results.csv") -> Dict:
    """
    ADMET预测技能入口
    
    Args:
        smiles: 单个SMILES字符串（单模式）
        input_file: 包含smiles列的CSV文件（批量模式）
        output: 输出文件路径
        
    Returns:
        预测结果
    """
    try:
        predictor = ADMETPredictor()
        
        if smiles:
            # 单模式
            result = predictor.predict_all(smiles)
            
            if 'error' in result:
                return result
            
            # 生成报告
            report_path = output.replace('.csv', '_report.md')
            predictor.generate_report(result, report_path)
            
            return {
                'smiles': smiles,
                'overall_score': result['overall_score'],
                'decision': result['admet_decision'],
                'detailed_results': result,
                'report_path': report_path
            }
        
        elif input_file:
            # 批量模式
            df = pd.read_csv(input_file)
            if 'smiles' not in df.columns:
                return {'error': '输入文件需要包含smiles列'}
            
            smiles_list = df['smiles'].tolist()
            results_df = predictor.batch_predict(smiles_list, output_path=output)
            
            if results_df.empty:
                return {'error': '没有有效的预测结果'}
            
            return {
                'total_compounds': len(results_df),
                'average_score': results_df['overall_score'].mean(),
                'priority_development': sum(results_df['admet_decision'] == '优先开发'),
                'further_optimization': sum(results_df['admet_decision'] == '进一步优化'),
                'careful_evaluation': sum(results_df['admet_decision'] == '谨慎评估'),
                'recommended_elimination': sum(results_df['admet_decision'] == '建议淘汰'),
                'results_path': output
            }
        
        else:
            return {'error': '请提供smiles参数或input_file参数'}
    
    except Exception as e:
        logger.error(f"ADMET预测失败: {str(e)}")
        return {'error': str(e)}

if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  单模式: python admet_prediction.py --smiles <SMILES> [output]")
        print("  批量模式: python admet_prediction.py --input <input.csv> [output]")
        sys.exit(1)
    
    if sys.argv[1] == '--smiles':
        smiles = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else "admet_results.csv"
        result = run_admet_prediction(smiles=smiles, output=output)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif sys.argv[1] == '--input':
        input_file = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else "admet_results.csv"
        result = run_admet_prediction(input_file=input_file, output=output)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print("无效参数")
        sys.exit(1)