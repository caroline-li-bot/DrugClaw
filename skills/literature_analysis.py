#!/usr/bin/env python3
"""
文献分析技能
自动抓取和分析PubMed、Google Scholar等学术数据库的文献
"""
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PubMedScraper:
    """PubMed文献抓取器"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email: str = "your@email.com"):
        self.email = email
    
    def search(self, keyword: str, max_results: int = 50, days: int = 365) -> List[str]:
        """
        搜索PubMed文献
        
        Args:
            keyword: 搜索关键词
            max_results: 最大返回结果数
            days: 搜索最近多少天的文献
            
        Returns:
            PMID列表
        """
        try:
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            date_filter = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[dp]"
            
            # 搜索
            search_url = f"{self.BASE_URL}/esearch.fcgi"
            params = {
                'db': 'pubmed',
                'term': f"{keyword} AND {date_filter}",
                'retmax': max_results,
                'retmode': 'json',
                'email': self.email
            }
            
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            logger.info(f"PubMed搜索到 {len(pmids)} 篇文献: {keyword}")
            
            return pmids
        except Exception as e:
            logger.error(f"PubMed搜索失败: {keyword}, 错误: {str(e)}")
            return []
    
    def fetch_details(self, pmids: List[str]) -> List[Dict]:
        """
        批量获取文献详情
        
        Args:
            pmids: PMID列表
            
        Returns:
            文献详情列表
        """
        if not pmids:
            return []
            
        try:
            fetch_url = f"{self.BASE_URL}/efetch.fcgi"
            params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml',
                'rettype': 'abstract',
                'email': self.email
            }
            
            response = requests.get(fetch_url, params=params, timeout=60)
            response.raise_for_status()
            
            # 解析XML
            soup = BeautifulSoup(response.content, 'xml')
            articles = soup.find_all('PubmedArticle')
            
            results = []
            for article in articles:
                try:
                    # 提取基本信息
                    pmid = article.find('PMID').text if article.find('PMID') else ''
                    title = article.find('ArticleTitle').text if article.find('ArticleTitle') else ''
                    
                    # 提取摘要
                    abstract_texts = article.find_all('AbstractText')
                    abstract = ' '.join([text.text for text in abstract_texts]) if abstract_texts else ''
                    
                    # 提取作者
                    authors = []
                    author_list = article.find('AuthorList')
                    if author_list:
                        for author in author_list.find_all('Author'):
                            last_name = author.find('LastName').text if author.find('LastName') else ''
                            fore_name = author.find('ForeName').text if author.find('ForeName') else ''
                            if last_name and fore_name:
                                authors.append(f"{fore_name} {last_name}")
                    
                    # 提取期刊
                    journal = article.find('Title').text if article.find('Title') else ''
                    pub_date = article.find('PubDate')
                    year = pub_date.find('Year').text if pub_date and pub_date.find('Year') else ''
                    
                    # 提取DOI
                    doi = ''
                    article_ids = article.find_all('ArticleId')
                    for article_id in article_ids:
                        if article_id.get('IdType') == 'doi':
                            doi = article_id.text
                            break
                    
                    # 提取关键词
                    keywords = []
                    keyword_list = article.find('KeywordList')
                    if keyword_list:
                        keywords = [kw.text for kw in keyword_list.find_all('Keyword')]
                    
                    results.append({
                        'pmid': pmid,
                        'title': title,
                        'abstract': abstract,
                        'authors': authors,
                        'journal': journal,
                        'year': year,
                        'doi': doi,
                        'keywords': keywords,
                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ''
                    })
                except Exception as e:
                    logger.warning(f"解析文献失败: PMID={pmid}, 错误: {str(e)}")
                    continue
            
            logger.info(f"成功获取 {len(results)} 篇文献详情")
            return results
        except Exception as e:
            logger.error(f"获取文献详情失败, 错误: {str(e)}")
            return []

def generate_paper_list(papers):
    """生成文献列表Markdown"""
    output = []
    for i, paper in enumerate(papers):
        authors = ', '.join(paper['authors'][:3])
        if len(paper['authors']) > 3:
            authors += ' et al.'
        
        abstract = paper['abstract'][:300] + '...' if paper['abstract'] else '无摘要'
        
        output.append(f"### {i+1}. {paper['title']}")
        output.append(f"- **作者**: {authors}")
        output.append(f"- **期刊**: {paper['journal']} ({paper['year']})")
        output.append(f"- **DOI**: {paper['doi'] if paper['doi'] else 'N/A'}")
        output.append(f"- **链接**: {paper['url']}")
        output.append(f"- **摘要**: {abstract}")
        output.append("")
    
    return '\n'.join(output)


class LiteratureAnalyzer:
    """文献分析器"""
    
    def __init__(self):
        self.pubmed_scraper = PubMedScraper()
    
    def analyze_topic(self, keyword: str, max_papers: int = 50, days: int = 365) -> Dict:
        """
        分析某个研究主题的文献
        
        Args:
            keyword: 研究关键词
            max_papers: 最大文献数量
            days: 搜索最近多少天的文献
            
        Returns:
            分析结果
        """
        logger.info(f"开始分析主题: {keyword}")
        
        # 搜索文献
        pmids = self.pubmed_scraper.search(keyword, max_papers, days)
        if not pmids:
            return {'error': '未找到相关文献'}
        
        # 获取文献详情
        papers = self.pubmed_scraper.fetch_details(pmids)
        if not papers:
            return {'error': '获取文献详情失败'}
        
        # 分析结果
        analysis = {
            'keyword': keyword,
            'total_papers': len(papers),
            'time_range': f"最近{days}天",
            'analysis_time': datetime.now().isoformat(),
            'papers': papers,
            'statistics': self._generate_statistics(papers),
            'key_findings': self._extract_key_findings(papers),
            'trending_topics': self._extract_trending_topics(papers),
            'top_authors': self._get_top_authors(papers),
            'top_journals': self._get_top_journals(papers)
        }
        
        return analysis
    
    def _generate_statistics(self, papers: List[Dict]) -> Dict:
        """生成统计信息"""
        years = [p.get('year', '') for p in papers if p.get('year')]
        year_counts = {}
        for year in years:
            if year:
                year_counts[year] = year_counts.get(year, 0) + 1
        
        return {
            'year_distribution': year_counts,
            'average_authors_per_paper': round(np.mean([len(p.get('authors', [])) for p in papers]), 1),
            'papers_with_abstract': sum(1 for p in papers if p.get('abstract')),
            'papers_with_doi': sum(1 for p in papers if p.get('doi'))
        }
    
    def _extract_key_findings(self, papers: List[Dict]) -> List[str]:
        """提取关键发现"""
        # 这里可以结合NLP模型提取关键结论
        # 目前简单返回包含关键词的句子
        findings = []
        for paper in papers[:10]:  # 前10篇文献
            abstract = paper.get('abstract', '')
            if abstract:
                # 简单提取包含结果、结论的句子
                sentences = abstract.split('. ')
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in ['result', 'conclusion', 'find', 'show', 'demonstrate', 'indicate']):
                        findings.append(f"[{paper.get('pmid')}] {sentence.strip()}")
                        break
        
        return findings[:20]  # 返回最多20条关键发现
    
    def _extract_trending_topics(self, papers: List[Dict]) -> Dict:
        """提取热点主题"""
        all_keywords = []
        for paper in papers:
            all_keywords.extend([kw.lower() for kw in paper.get('keywords', [])])
        
        # 统计关键词频率
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        
        return dict(keyword_counts.most_common(20))
    
    def _get_top_authors(self, papers: List[Dict]) -> Dict:
        """获取高产作者"""
        all_authors = []
        for paper in papers:
            all_authors.extend(paper.get('authors', []))
        
        from collections import Counter
        author_counts = Counter(all_authors)
        
        return dict(author_counts.most_common(10))
    
    def _get_top_journals(self, papers: List[Dict]) -> Dict:
        """获取高产期刊"""
        journals = [p.get('journal', '') for p in papers if p.get('journal')]
        
        from collections import Counter
        journal_counts = Counter(journals)
        
        return dict(journal_counts.most_common(10))
    
    def generate_report(self, analysis: Dict, output_path: str) -> str:
        """生成分析报告"""
        report = f"""# 文献分析报告: {analysis['keyword']}

## 基本信息
- 分析时间: {analysis['analysis_time']}
- 文献数量: {analysis['total_papers']} 篇
- 时间范围: {analysis['time_range']}

## 统计信息
- 年份分布: {json.dumps(analysis['statistics']['year_distribution'], indent=2, ensure_ascii=False)}
- 平均作者数: {analysis['statistics']['average_authors_per_paper']}
- 有摘要的文献: {analysis['statistics']['papers_with_abstract']} 篇
- 有DOI的文献: {analysis['statistics']['papers_with_doi']} 篇

## 热点主题
{json.dumps(analysis['trending_topics'], indent=2, ensure_ascii=False)}

## 高产作者
{json.dumps(analysis['top_authors'], indent=2, ensure_ascii=False)}

## 高产期刊
{json.dumps(analysis['top_journals'], indent=2, ensure_ascii=False)}

## 关键发现
{chr(10).join(f"- {finding}" for finding in analysis['key_findings'])}

## 文献列表
{generate_paper_list(analysis['papers'][:20])}
"""
        
        # 保存报告
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"分析报告已保存到: {output_path}")
        return output_path

# OpenClaw技能入口
def run_literature_analysis(keyword: str, output: str = "literature_report.md", max_papers: int = 50, days: int = 365) -> Dict:
    """
    文献分析技能入口
    
    Args:
        keyword: 搜索关键词
        output: 输出报告路径
        max_papers: 最大文献数量
        days: 搜索最近多少天的文献
        
    Returns:
        分析结果
    """
    analyzer = LiteratureAnalyzer()
    analysis = analyzer.analyze_topic(keyword, max_papers, days)
    
    if 'error' in analysis:
        return analysis
    
    report_path = analyzer.generate_report(analysis, output)
    analysis['report_path'] = report_path
    
    return analysis

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python literature_analysis.py <keyword> [output] [max_papers] [days]")
        sys.exit(1)
    
    keyword = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "literature_report.md"
    max_papers = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    days = int(sys.argv[4]) if len(sys.argv) > 4 else 365
    
    result = run_literature_analysis(keyword, output, max_papers, days)
    print(json.dumps(result, indent=2, ensure_ascii=False))