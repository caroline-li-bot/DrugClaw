#!/usr/bin/env python3
"""
AI模型工具函数
"""
from typing import List, Dict, Optional
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
import logging
from rdkit import Chem

logger = logging.getLogger(__name__)

class ChemBERTaPredictor:
    """ChemBERTa化合物性质预测器"""
    
    def __init__(self, model_name: str = "seyonec/ChemBERTa-zinc-base-v1"):
        """
        初始化ChemBERTa模型
        
        Args:
            model_name: 模型名称
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        
        # 加载预训练的分类头（示例，实际需要训练）
        self.property_heads = {
            'toxicity': torch.nn.Linear(768, 1),
            'solubility': torch.nn.Linear(768, 1),
            'bioavailability': torch.nn.Linear(768, 1)
        }
        
        for head in self.property_heads.values():
            head.to(self.device)
    
    def get_embeddings(self, smiles: str) -> Optional[torch.Tensor]:
        """
        获取SMILES的ChemBERTa嵌入
        
        Args:
            smiles: SMILES字符串
            
        Returns:
            嵌入向量
        """
        try:
            inputs = self.tokenizer(
                smiles,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)
            
            return embeddings
        except Exception as e:
            logger.error(f"获取ChemBERTa嵌入失败: {smiles}, 错误: {str(e)}")
            return None
    
    def predict_properties(self, smiles: str) -> Dict:
        """
        预测化合物性质
        
        Args:
            smiles: SMILES字符串
            
        Returns:
            性质预测结果
        """
        embeddings = self.get_embeddings(smiles)
        if embeddings is None:
            return {}
        
        try:
            predictions = {}
            
            with torch.no_grad():
                for prop_name, head in self.property_heads.items():
                    pred = head(embeddings).squeeze().cpu().item()
                    predictions[prop_name] = pred
            
            # 转换为更易读的格式
            predictions['toxicity_risk'] = '高' if predictions['toxicity'] > 0.7 else '中' if predictions['toxicity'] > 0.3 else '低'
            predictions['solubility_level'] = '高' if predictions['solubility'] > 0.7 else '中' if predictions['solubility'] > 0.3 else '低'
            predictions['bioavailability_score'] = round(predictions['bioavailability'], 3)
            
            return predictions
        except Exception as e:
            logger.error(f"性质预测失败: {smiles}, 错误: {str(e)}")
            return {}

class ActivityPredictor:
    """化合物活性预测器"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化活性预测模型
        
        Args:
            model_path: 模型路径
        """
        self.model = None
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> None:
        """加载模型"""
        try:
            self.model = torch.load(model_path)
            self.model.eval()
            logger.info(f"活性预测模型加载成功: {model_path}")
        except Exception as e:
            logger.error(f"加载活性预测模型失败: {model_path}, 错误: {str(e)}")
    
    def predict_activity(self, smiles: str, target: str) -> Optional[float]:
        """
        预测化合物对靶点的活性
        
        Args:
            smiles: SMILES字符串
            target: 靶点名称或ID
            
        Returns:
            pIC50预测值
        """
        if self.model is None:
            logger.warning("活性预测模型未加载")
            return None
        
        try:
            # 这里需要根据实际模型输入实现
            # 示例：结合化合物嵌入和靶点嵌入进行预测
            logger.warning("活性预测功能需要根据实际模型实现")
            return None
        except Exception as e:
            logger.error(f"活性预测失败: {smiles} -> {target}, 错误: {str(e)}")
            return None

class ADMETPredictor:
    """ADMET性质预测器"""
    
    def __init__(self):
        """初始化ADMET预测器"""
        self.chemberta = ChemBERTaPredictor()
    
    def predict_all(self, smiles: str) -> Dict:
        """
        预测所有ADMET性质
        
        Args:
            smiles: SMILES字符串
            
        Returns:
            ADMET性质字典
        """
        results = {}
        
        # 基于规则的性质
        from .chem_utils import calculate_molecular_properties
        physchem_props = calculate_molecular_properties(smiles)
        results.update(physchem_props)
        
        # AI预测的性质
        ai_props = self.chemberta.predict_properties(smiles)
        results.update(ai_props)
        
        # 综合评估
        results['admet_risk_assessment'] = self._assess_risk(results)
        
        return results
    
    def _assess_risk(self, props: Dict) -> str:
        """
        综合评估ADMET风险
        
        Args:
            props: 性质字典
            
        Returns:
            风险评估结果
        """
        risk_score = 0
        
        # Lipinski规则违反
        risk_score += props.get('lipinski_violations', 0) * 0.2
        
        # 毒性风险
        if props.get('toxicity', 0) > 0.7:
            risk_score += 0.3
        elif props.get('toxicity', 0) > 0.3:
            risk_score += 0.1
        
        # 溶解度
        if props.get('solubility', 0) < 0.3:
            risk_score += 0.2
        
        # 生物利用度
        if props.get('bioavailability', 0) < 0.3:
            risk_score += 0.2
        
        if risk_score >= 0.7:
            return "高风险"
        elif risk_score >= 0.4:
            return "中风险"
        else:
            return "低风险"

def calculate_similarity(smiles1: str, smiles2: str) -> float:
    """
    计算两个化合物的Tanimoto相似度
    
    Args:
        smiles1: 第一个化合物SMILES
        smiles2: 第二个化合物SMILES
        
    Returns:
        Tanimoto相似度 (0-1)
    """
    from rdkit.Chem import AllChem
    
    try:
        mol1 = Chem.MolFromSmiles(smiles1)
        mol2 = Chem.MolFromSmiles(smiles2)
        
        if mol1 is None or mol2 is None:
            return 0.0
        
        fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, 2, nBits=1024)
        fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, 2, nBits=1024)
        
        from rdkit import DataStructs
        similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
        
        return similarity
    except Exception as e:
        logger.error(f"计算相似度失败: {smiles1} vs {smiles2}, 错误: {str(e)}")
        return 0.0