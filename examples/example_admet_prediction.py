#!/usr/bin/env python3
"""
ADMET预测使用示例
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.admet_prediction import run_admet_prediction

def main():
    # 示例1: 单个化合物预测
    print("示例1: 预测吉非替尼的ADMET性质...")
    
    gefitinib_smiles = "COC1=C(OCCCN2CCOCC2)C=C2C(NC3=CC(Cl)=C(F)C=C3)=NC=NC2=C1"
    
    result = run_admet_prediction(
        smiles=gefitinib_smiles,
        output="gefitinib_admet.csv"
    )
    
    if 'error' in result:
        print(f"预测失败: {result['error']}")
    else:
        print(f"预测完成!")
        print(f"SMILES: {result['smiles']}")
        print(f"综合评分: {result['overall_score']}")
        print(f"决策建议: {result['decision']}")
        print(f"报告路径: {result['report_path']}")
        
        # 打印详细结果
        print("\n详细性质:")
        print(f"- 口服生物利用度: {result['detailed_results']['absorption']['oral_bioavailability']}")
        print(f"- 血脑屏障穿透性: {result['detailed_results']['distribution']['bbb_permeability']}")
        print(f"- 代谢稳定性: {result['detailed_results']['metabolism']['metabolic_stability']}")
        print(f"- 总体毒性风险: {result['detailed_results']['toxicity']['overall_toxicity_risk']}")
    
    # 示例2: 批量预测
    print("\n\n示例2: 批量预测化合物库...")
    
    # 创建示例化合物库
    import pandas as pd
    compounds = [
        {"smiles": "COC1=C(OCCCN2CCOCC2)C=C2C(NC3=CC(Cl)=C(F)C=C3)=NC=NC2=C1", "name": "Gefitinib"},
        {"smiles": "CC1=C(C=C(C=C1)N2C=CC(=O)C(=C2)N)S(=O)(=O)N3CCN(CC3)C(=O)C4CCC4", "name": "Erlotinib"},
        {"smiles": "C1=CC(=C(C=C1Cl)Cl)O", "name": "Triclosan"},
        {"smiles": "C1=CC=C(C=C1)C(=O)O", "name": "Benzoic acid"}
    ]
    
    df = pd.DataFrame(compounds)
    df.to_csv("example_compounds.csv", index=False)
    
    # 批量预测
    batch_result = run_admet_prediction(
        input_file="example_compounds.csv",
        output="batch_admet_results.csv"
    )
    
    if 'error' in batch_result:
        print(f"批量预测失败: {batch_result['error']}")
    else:
        print(f"批量预测完成!")
        print(f"总化合物数: {batch_result['total_compounds']}")
        print(f"平均综合评分: {batch_result['average_score']:.2f}")
        print(f"优先开发: {batch_result['priority_development']} 个")
        print(f"进一步优化: {batch_result['further_optimization']} 个")
        print(f"谨慎评估: {batch_result['careful_evaluation']} 个")
        print(f"建议淘汰: {batch_result['recommended_elimination']} 个")
        print(f"结果路径: {batch_result['results_path']}")
    
    # 清理临时文件
    if os.path.exists("example_compounds.csv"):
        os.unlink("example_compounds.csv")

if __name__ == "__main__":
    main()