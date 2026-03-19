#!/usr/bin/env python3
"""
Supabase数据库工具类
"""
from typing import List, Dict, Optional, Any
import os
import json
import logging
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase客户端封装"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化Supabase客户端"""
        self.supabase_url = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
        self.supabase_key = os.getenv('SUPABASE_KEY', 'your-supabase-anon-key-here')
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase环境变量未配置，将使用本地文件存储")
            self.client = None
            return
        
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase客户端初始化成功")
        except Exception as e:
            logger.error(f"Supabase客户端初始化失败: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查Supabase是否可用"""
        return self.client is not None
    
    # 用户任务相关方法
    def create_task(self, user_id: str, task_type: str, parameters: Dict) -> Optional[str]:
        """创建新任务"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('user_tasks').insert({
                'user_id': user_id,
                'task_type': task_type,
                'parameters': parameters,
                'status': 'pending'
            }).execute()
            
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            return None
    
    def update_task_status(self, task_id: str, status: str, result: Optional[Dict] = None, error_message: Optional[str] = None) -> bool:
        """更新任务状态"""
        if not self.is_available():
            return False
        
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if result is not None:
                update_data['result'] = result
            
            if error_message is not None:
                update_data['error_message'] = error_message
            
            self.client.table('user_tasks').update(update_data).eq('id', task_id).execute()
            return True
        except Exception as e:
            logger.error(f"更新任务状态失败: {str(e)}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('user_tasks').select('*').eq('id', task_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"获取任务信息失败: {str(e)}")
            return None
    
    # 化合物库相关方法
    def create_compound_library(self, name: str, description: str = "", source: str = "") -> Optional[str]:
        """创建化合物库"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('compound_libraries').insert({
                'name': name,
                'description': description,
                'source': source
            }).execute()
            
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"创建化合物库失败: {str(e)}")
            return None
    
    def insert_compound(self, library_id: str, smiles: str, properties: Dict) -> Optional[str]:
        """插入化合物"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.rpc('insert_compound', {
                'p_library_id': library_id,
                'p_smiles': smiles,
                'p_molecular_weight': properties.get('molecular_weight'),
                'p_logp': properties.get('logp'),
                'p_h_donors': properties.get('h_donors'),
                'p_h_acceptors': properties.get('h_acceptors'),
                'p_tpsa': properties.get('tpsa'),
                'p_qed': properties.get('qed')
            }).execute()
            
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"插入化合物失败: {str(e)}")
            return None
    
    def batch_insert_compounds(self, library_id: str, compounds: List[Dict]) -> int:
        """批量插入化合物"""
        if not self.is_available():
            return 0
        
        try:
            records = []
            for comp in compounds:
                records.append({
                    'library_id': library_id,
                    'smiles': comp['smiles'],
                    'molecular_weight': comp.get('molecular_weight'),
                    'logp': comp.get('logp'),
                    'h_donors': comp.get('h_donors'),
                    'h_acceptors': comp.get('h_acceptors'),
                    'tpsa': comp.get('tpsa'),
                    'qed': comp.get('qed')
                })
            
            response = self.client.table('compounds').insert(records, upsert=True).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"批量插入化合物失败: {str(e)}")
            return 0
    
    # ADMET结果相关方法
    def save_admet_result(self, smiles: str, result: Dict, compound_id: Optional[str] = None) -> Optional[str]:
        """保存ADMET预测结果"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('admet_results').insert({
                'compound_id': compound_id,
                'smiles': smiles,
                'overall_score': result.get('overall_score'),
                'admet_decision': result.get('admet_decision'),
                'absorption': result.get('absorption'),
                'distribution': result.get('distribution'),
                'metabolism': result.get('metabolism'),
                'excretion': result.get('excretion'),
                'toxicity': result.get('toxicity')
            }).execute()
            
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"保存ADMET结果失败: {str(e)}")
            return None
    
    def get_admet_result(self, smiles: str) -> Optional[Dict]:
        """根据SMILES获取ADMET结果"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('admet_results').select('*').eq('smiles', smiles).order('created_at', desc=True).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"获取ADMET结果失败: {str(e)}")
            return None
    
    # 虚拟筛选相关方法
    def create_screening_job(self, user_id: str, target_name: str, target_pdb: str, 
                           binding_site: Dict, library_id: str) -> Optional[str]:
        """创建虚拟筛选任务"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('screening_jobs').insert({
                'user_id': user_id,
                'target_name': target_name,
                'target_pdb': target_pdb,
                'binding_site': binding_site,
                'library_id': library_id,
                'status': 'pending'
            }).execute()
            
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"创建虚拟筛选任务失败: {str(e)}")
            return None
    
    def update_screening_job_progress(self, job_id: str, completed: int, total: int, best_affinity: Optional[float] = None) -> bool:
        """更新虚拟筛选进度"""
        if not self.is_available():
            return False
        
        try:
            update_data = {
                'completed_compounds': completed,
                'total_compounds': total,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if best_affinity is not None:
                update_data['best_affinity'] = best_affinity
            
            self.client.table('screening_jobs').update(update_data).eq('id', job_id).execute()
            return True
        except Exception as e:
            logger.error(f"更新筛选进度失败: {str(e)}")
            return False
    
    def save_screening_result(self, job_id: str, smiles: str, binding_affinity: float, 
                            rank: int, priority_score: float, compound_id: Optional[str] = None) -> Optional[str]:
        """保存虚拟筛选结果"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('screening_results').insert({
                'job_id': job_id,
                'compound_id': compound_id,
                'smiles': smiles,
                'binding_affinity': binding_affinity,
                'rank': rank,
                'priority_score': priority_score
            }).execute()
            
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"保存筛选结果失败: {str(e)}")
            return None
    
    def get_screening_results(self, job_id: str, limit: int = 100) -> List[Dict]:
        """获取虚拟筛选结果"""
        if not self.is_available():
            return []
        
        try:
            response = self.client.table('screening_results').select('*').eq('job_id', job_id).order('rank').limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"获取筛选结果失败: {str(e)}")
            return []
    
    # 文献分析相关方法
    def create_literature_job(self, user_id: str, keyword: str, max_papers: int, days: int) -> Optional[str]:
        """创建文献分析任务"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('literature_jobs').insert({
                'user_id': user_id,
                'keyword': keyword,
                'max_papers': max_papers,
                'days': days,
                'status': 'pending'
            }).execute()
            
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"创建文献分析任务失败: {str(e)}")
            return None
    
    def update_literature_job_result(self, job_id: str, total_papers: int, key_findings: List[str], 
                                   trending_topics: Dict, status: str = 'completed') -> bool:
        """更新文献分析结果"""
        if not self.is_available():
            return False
        
        try:
            self.client.table('literature_jobs').update({
                'total_papers': total_papers,
                'key_findings': key_findings,
                'trending_topics': trending_topics,
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', job_id).execute()
            return True
        except Exception as e:
            logger.error(f"更新文献分析结果失败: {str(e)}")
            return False
    
    def save_literature_paper(self, job_id: str, paper_data: Dict) -> Optional[str]:
        """保存文献信息"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.table('literature_papers').insert({
                'job_id': job_id,
                'pmid': paper_data.get('pmid'),
                'title': paper_data.get('title'),
                'abstract': paper_data.get('abstract'),
                'authors': paper_data.get('authors'),
                'journal': paper_data.get('journal'),
                'year': paper_data.get('year'),
                'doi': paper_data.get('doi'),
                'url': paper_data.get('url')
            }).execute()
            
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"保存文献失败: {str(e)}")
            return None

# 全局实例
supabase_client = SupabaseClient()