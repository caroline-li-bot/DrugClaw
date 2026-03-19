#!/usr/bin/env python3
"""
基于RAG的文献智能问答系统
使用PubMedBERT + 向量数据库，实现对文献的智能问答
"""
from typing import List, Dict, Optional
import os
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class LiteratureRAG:
    """文献智能问答系统"""
    
    def __init__(self):
        from utils.sota_models import get_pubmed_bert, get_rag_literature
        from skills.literature_analysis import PubMedScraper
        
        self.pubmed_bert = get_pubmed_bert()
        self.rag = get_rag_literature()
        self.scraper = PubMedScraper()
        
        # 初始化LLM用于问答生成
        try:
            from transformers import pipeline
            self.llm = pipeline(
                "text-generation",
                model="meta-llama/Llama-3.1-70B-Instruct",
                device_map="auto"
            )
            logger.info("Llama 3.1加载成功")
        except Exception as e:
            logger.warning(f"LLM加载失败: {str(e)}，将仅返回检索结果")
            self.llm = None
    
    def is_available(self) -> bool:
        return self.rag.is_available() and self.pubmed_bert.is_available()
    
    def build_index(self, keyword: str, max_papers: int = 100, days: int = 365) -> int:
        """构建文献索引"""
        logger.info(f"开始构建文献索引，关键词: {keyword}, 最大文献数: {max_papers}")
        
        # 搜索文献
        pmids = self.scraper.search(keyword, max_papers, days)
        if not pmids:
            logger.warning("未找到相关文献")
            return 0
        
        # 获取文献详情
        papers = self.scraper.fetch_details(pmids)
        if not papers:
            logger.warning("获取文献详情失败")
            return 0
        
        # 添加到RAG索引
        added_count = 0
        for paper in papers:
            if self.rag.add_paper(
                pmid=paper['pmid'],
                title=paper['title'],
                abstract=paper['abstract']
            ):
                added_count += 1
        
        logger.info(f"文献索引构建完成，共添加 {added_count} 篇文献")
        return added_count
    
    def query(self, question: str, n_results: int = 5, generate_answer: bool = True) -> Dict:
        """问答查询"""
        result = {
            'question': question,
            'related_papers': [],
            'answer': None,
            'answer_generated': False
        }
        
        # 检索相关文献
        related_papers = self.rag.query(question, n_results)
        result['related_papers'] = related_papers
        
        if not related_papers:
            result['error'] = '未找到相关文献'
            return result
        
        if not generate_answer or self.llm is None:
            return result
        
        # 构建Prompt
        context = "\n\n".join([
            f"文献 {i+1} (PMID: {paper['pmid']}, 相似度: {paper['similarity']:.3f}):\n标题: {paper['title']}\n摘要: {paper['abstract']}"
            for i, paper in enumerate(related_papers)
        ])
        
        prompt = f"""基于以下文献内容，回答用户的问题。回答要准确、客观，引用相关文献。如果信息不足，就说"现有文献不足以回答这个问题"。

相关文献:
{context}

用户问题: {question}

回答:"""
        
        # 生成回答
        try:
            output = self.llm(
                prompt,
                max_new_tokens=1000,
                temperature=0.1,
                top_p=0.95,
                do_sample=False
            )
            
            answer = output[0]['generated_text'].split("回答:")[-1].strip()
            result['answer'] = answer
            result['answer_generated'] = True
            
        except Exception as e:
            logger.error(f"生成回答失败: {str(e)}")
            result['error'] = f"生成回答失败: {str(e)}"
        
        return result
    
    def generate_review(self, topic: str, max_papers: int = 200) -> Dict:
        """自动生成文献综述"""
        logger.info(f"开始生成 {topic} 的文献综述")
        
        # 构建索引
        added_count = self.build_index(topic, max_papers)
        if added_count == 0:
            return {'error': '未找到相关文献'}
        
        # 生成综述的各个部分
        sections = [
            "研究背景与意义",
            "最新研究进展",
            "核心技术与方法",
            "当前挑战与未解决问题",
            "未来研究方向"
        ]
        
        review = {}
        for section in sections:
            question = f"总结{topic}领域的{section}"
            response = self.query(question, n_results=10)
            review[section] = response.get('answer', '无相关信息')
        
        # 整理参考文献
        all_papers = self.rag.query(topic, n_results=20)
        references = [
            f"[{i+1}] {paper['title']} (PMID: {paper['pmid']})"
            for i, paper in enumerate(all_papers)
        ]
        
        # 生成完整报告
        report = f"# {topic} 研究综述\n\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"文献数量: {added_count} 篇\n\n"
        
        for section, content in review.items():
            report += f"## {section}\n\n{content}\n\n"
        
        report += "## 参考文献\n\n"
        report += "\n".join(references)
        
        return {
            'topic': topic,
            'total_papers': added_count,
            'review': review,
            'references': references,
            'full_report': report
        }

# 技能入口
def run_literature_qa(question: str, keyword: Optional[str] = None, build_index: bool = False) -> Dict:
    """文献问答入口"""
    rag = LiteratureRAG()
    
    if not rag.is_available():
        return {'error': 'RAG系统不可用，请先安装相关依赖'}
    
    if build_index and keyword:
        rag.build_index(keyword, max_papers=100)
    
    result = rag.query(question)
    return result

def generate_literature_review(topic: str, max_papers: int = 200, output_path: Optional[str] = None) -> Dict:
    """生成文献综述入口"""
    rag = LiteratureRAG()
    
    if not rag.is_available():
        return {'error': 'RAG系统不可用，请先安装相关依赖'}
    
    result = rag.generate_review(topic, max_papers)
    
    if output_path and 'full_report' in result:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['full_report'])
        result['output_path'] = output_path
    
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  问答: python literature_rag.py qa <question> [keyword]")
        print("  综述: python literature_rag.py review <topic> [output_path]")
        sys.exit(1)
    
    if sys.argv[1] == 'qa':
        question = sys.argv[2]
        keyword = sys.argv[3] if len(sys.argv) > 3 else None
        result = run_literature_qa(question, keyword, build_index=True)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif sys.argv[1] == 'review':
        topic = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        result = generate_literature_review(topic, output_path=output_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
