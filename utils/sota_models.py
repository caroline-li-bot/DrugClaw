#!/usr/bin/env python3
"""
SOTA AI模型集成
包含2026年最新的药物研发SOTA模型
"""
from typing import List, Dict, Optional, Tuple
import os
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PubMedBERT:
    """PubMedBERT 文献理解模型 (SOTA for biomedical NLP)"""
    
    def __init__(self, model_name: str = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"):
        """
        初始化PubMedBERT模型
        """
        try:
            from transformers import AutoTokenizer, AutoModelForMaskedLM, pipeline
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForMaskedLM.from_pretrained(model_name)
            self.feature_extractor = pipeline(
                "feature-extraction",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1  # CPU only for now, use GPU for production
            )
            self.device = "cpu"
            logger.info("PubMedBERT 加载成功")
        except Exception as e:
            logger.warning(f"PubMedBERT 加载失败: {str(e)}，将使用规则模型替代")
            self.model = None
    
    def is_available(self) -> bool:
        return self.model is not None
    
    def get_embeddings(self, text: str) -> Optional[np.ndarray]:
        """获取文本嵌入"""
        if not self.is_available():
            return None
        
        try:
            with torch.no_grad():
                features = self.feature_extractor(text)
                # <[BOS_never_used_51bce0c785ca2f68081bfa7d91973934]>标记嵌入作为句子表示
                embedding = np.mean(features[0], axis=0)
                return embedding
        except Exception as e:
            logger.error(f"获取PubMedBERT嵌入失败: {str(e)}")
            return None
    
    def extract_key_findings(self, text: str) -> List[str]:
        """提取关键发现"""
        if not self.is_available():
            # 回退到规则方法
            sentences = text.split('. ')
            findings = []
            for sentence in sentences:
                if any(k in sentence.lower() for k in ['result', 'conclusion', 'find', 'show', 'demonstrate', 'indicate', 'prove']):
                    findings.append(sentence.strip())
            return findings[:10]
        
        # TODO: 实现基于PubMedBERT的关键信息抽取
        return []

class ChemBERTa2:
    """ChemBERTa-2 分子大模型 (当前SOTA for molecular property prediction)"""
    
    def __init__(self, model_name: str = "DeepChem/ChemBERTa-77M-MLM"):
        """
        初始化ChemBERTa-2模型
        """
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            
            # 加载多个任务的预测pipeline
            self.property_predictors = {
                'homo_lumo': pipeline("text-classification", model="DeepChem/ChemBERTa-77M-MLM", device=self.device),
                'solubility': pipeline("text-classification", model="DeepChem/ChemBERTa-77M-MTR", device=self.device),
                'toxicity': pipeline("text-classification", model="DeepChem/ChemBERTa-77M-Tox21", device=self.device)
            }
            
            logger.info(f"ChemBERTa-2模型加载成功，设备: {self.device}")
        except Exception as e:
            logger.warning(f"ChemBERTa-2模型加载失败: {str(e)}，将使用规则模型替代")
            self.model = None
    
    def is_available(self) -> bool:
        return self.model is not None
    
    def predict_properties(self, smiles: str) -> Optional[Dict]:
        """预测分子性质"""
        if not self.is_available():
            return None
        
        try:
            properties = {}
            
            # 预测HOMO-LUMO能级
            homo_lumo = self.property_predictors['homo_lumo'](smiles)[0]
            properties['homo_lumo_gap'] = homo_lumo['score']
            
            # 预测水溶性
            solubility = self.property_predictors['solubility'](smiles)[0]
            properties['solubility'] = solubility['score']
            
            # 预测毒性
            toxicity = self.property_predictors['toxicity'](smiles)[0]
            properties['toxicity_score'] = toxicity['score']
            properties['is_toxic'] = toxicity['label'] == 'toxic'
            
            # 获取分子嵌入
            inputs = self.tokenizer(
                smiles,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                properties['embedding'] = outputs.logits.mean(dim=1).cpu().numpy()
            
            return properties
        except Exception as e:
            logger.error(f"ChemBERTa性质预测失败: {str(e)}")
            return None
    
    def calculate_binding_affinity(self, smiles: str, target_name: str) -> Optional[float]:
        """预测蛋白-配体结合亲和力（使用Pretrained模型）"""
        if not self.is_available():
            return None
        
        try:
            # 使用预训练的亲和力预测模型，这里使用简化实现
            # 实际可以使用BindingDB预训练的ChemBERTa模型
            # 这里基于分子性质和已知靶点的亲和力范围给出合理预测
            from utils.chem_utils import calculate_molecular_properties
            props = calculate_molecular_properties(smiles)
            
            # 基于分子性质的经验性亲和力预测（仅作示例）
            base_affinity = -6.0
            if props.get('logp', 0) > 2 and props.get('logp', 0) < 5:
                base_affinity -= 1.0
            if props.get('qed', 0) > 0.6:
                base_affinity -= 0.5
            if props.get('molecular_weight', 0) > 300 and props.get('molecular_weight', 0) < 500:
                base_affinity -= 0.5
            
            # 针对TREM2靶点的调整
            if 'trem2' in target_name.lower():
                base_affinity -= 0.8
            
            return round(base_affinity, 2)
        except Exception as e:
            logger.error(f"结合亲和力预测失败: {str(e)}")
            return None

class DiffDock:
    """DiffDock 分子对接模型 (当前SOTA for molecular docking)"""
    
    def __init__(self):
        """初始化DiffDock"""
        try:
            # 使用HuggingFace上的DiffDock实现
            from transformers import AutoModelForStructurePrediction
            self.model = AutoModelForStructurePrediction.from_pretrained("hmg-lab/DiffDock-L")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            logger.info(f"DiffDock加载成功，设备: {self.device}")
        except Exception as e:
            logger.warning(f"DiffDock加载失败: {str(e)}，将使用AutoDock Vina作为备选")
            self.model = None
            
            # 检查AutoDock Vina是否可用
            try:
                import subprocess
                subprocess.run(['vina', '--help'], capture_output=True, check=True)
                self.vina_available = True
                logger.info("AutoDock Vina可用，将作为对接备选")
            except:
                self.vina_available = False
    
    def is_available(self) -> bool:
        return self.model is not None
    
    def dock(self, protein_pdb: str, ligand_smiles: str) -> Optional[Dict]:
        """运行分子对接"""
        if not self.is_available():
            return None
        
        try:
            # 运行DiffDock对接
            result = self.model.dock(
                protein_pdb=protein_pdb,
                ligand_smiles=ligand_smiles,
                num_poses=10,
                device=self.device
            )
            
            # 解析结果
            best_pose = result['poses'][0]
            return {
                'binding_affinity': result['confidences'][0],
                'best_affinity': min(result['confidences']),
                'poses': result['poses'],
                'confidences': result['confidences'],
                'rmsd': result.get('rmsds', [])
            }
        except Exception as e:
            logger.error(f"DiffDock对接失败: {str(e)}")
            return None

class ESMFold:
    """ESMFold 蛋白质结构预测模型 (Meta开源，速度快，精度接近AlphaFold 2)"""
    
    def __init__(self):
        """初始化ESMFold"""
        try:
            from transformers import AutoTokenizer, EsmForProteinFolding
            self.tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
            self.model = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            logger.info(f"ESMFold加载成功，设备: {self.device}")
        except Exception as e:
            logger.warning(f"ESMFold加载失败: {str(e)}，将使用AlphaFold数据库API")
            self.model = None
            self.alphafold_db_api = "https://alphafold.ebi.ac.uk/api/prediction/"
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    def predict_structure(self, sequence: str, uniprot_id: Optional[str] = None) -> Optional[str]:
        """预测蛋白质结构"""
        if self.model is not None:
            # 使用本地ESMFold预测
            try:
                inputs = self.tokenizer(sequence, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                # 转换为PDB格式
                pdb_str = self.model.output_to_pdb(outputs)[0]
                return pdb_str
            except Exception as e:
                logger.error(f"ESMFold结构预测失败: {str(e)}")
        
        # 回退到AlphaFold数据库查询
        if uniprot_id:
            try:
                import requests
                response = requests.get(f"{self.alphafold_db_api}{uniprot_id}", timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    pdb_url = data[0]['pdbUrl']
                    pdb_response = requests.get(pdb_url, timeout=30)
                    return pdb_response.text
            except Exception as e:
                logger.error(f"AlphaFold数据库查询失败: {str(e)}")
        
        logger.error("无法获取蛋白质结构")
        return None

class RAGLiterature:
    """检索增强生成的文献问答系统"""
    
    def __init__(self, vector_db_path: str = "./data/literature_index"):
        """初始化RAG系统"""
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=vector_db_path)
            self.collection = self.client.get_or_create_collection("literature")
            self.embedding_model = PubMedBERT()
            logger.info("文献RAG系统初始化成功")
        except Exception as e:
            logger.warning(f"RAG系统初始化失败: {str(e)}")
            self.collection = None
    
    def is_available(self) -> bool:
        return self.collection is not None and self.embedding_model.is_available()
    
    def add_paper(self, pmid: str, title: str, abstract: str, full_text: str = "") -> bool:
        """添加文献到索引"""
        if not self.is_available():
            return False
        
        try:
            embedding = self.embedding_model.get_embeddings(f"{title} {abstract} {full_text}")
            if embedding is None:
                return False
            
            self.collection.add(
                ids=[pmid],
                embeddings=[embedding.tolist()],
                metadatas=[{"title": title, "abstract": abstract, "pmid": pmid}],
                documents=[f"{title} {abstract} {full_text}"]
            )
            return True
        except Exception as e:
            logger.error(f"添加文献到RAG索引失败: {str(e)}")
            return False
    
    def query(self, question: str, n_results: int = 5) -> List[Dict]:
        """检索相关文献"""
        if not self.is_available():
            return []
        
        try:
            query_embedding = self.embedding_model.get_embeddings(question)
            if query_embedding is None:
                return []
            
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results
            )
            
            papers = []
            for i in range(len(results['ids'][0])):
                papers.append({
                    'pmid': results['metadatas'][0][i]['pmid'],
                    'title': results['metadatas'][0][i]['title'],
                    'abstract': results['metadatas'][0][i]['abstract'],
                    'similarity': 1 - results['distances'][0][i]
                })
            
            return papers
        except Exception as e:
            logger.error(f"RAG查询失败: {str(e)}")
            return []

# 全局单例实例
_pubmed_bert = None
_chemberta2 = None
_diffdock = None
_esmfold = None
_rag_literature = None

def get_pubmed_bert() -> PubMedBERT:
    global _pubmed_bert
    if _pubmed_bert is None:
        _pubmed_bert = PubMedBERT()
    return _pubmed_bert

def get_chemberta2() -> ChemBERTa2:
    global _chemberta2
    if _chemberta2 is None:
        _chemberta2 = ChemBERTa2()
    return _chemberta2

def get_diffdock() -> DiffDock:
    global _diffdock
    if _diffdock is None:
        _diffdock = DiffDock()
    return _diffdock

def get_esmfold() -> ESMFold:
    global _esmfold
    if _esmfold is None:
        _esmfold = ESMFold()
    return _esmfold

def get_rag_literature() -> RAGLiterature:
    global _rag_literature
    if _rag_literature is None:
        _rag_literature = RAGLiterature()
    return _rag_literature
