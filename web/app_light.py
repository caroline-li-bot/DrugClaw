#!/usr/bin/env python3
"""
OpenClaw Drug Web 界面 - 轻量化版本，无需PyTorch和重型AI模型，适合Vercel部署
"""
from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
import json
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 上传限制
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入轻量化工具
try:
    from utils.chem_utils import calculate_molecular_properties, filter_library_by_properties
    from utils.db_utils import PubChemAPI
except ImportError as e:
    logger.warning(f"导入工具失败: {str(e)}")
    calculate_molecular_properties = None
    filter_library_by_properties = None
    PubChemAPI = None

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/literature/analyze', methods=['POST'])
def api_literature_analyze():
    """文献分析API"""
    try:
        data = request.json
        keyword = data.get('keyword')
        max_papers = int(data.get('max_papers', 50))
        days = int(data.get('days', 365))
        
        if not keyword:
            return jsonify({'error': '请输入搜索关键词'}), 400
        
        # 使用PubMed API搜索
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_filter = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[dp]"
        
        # 搜索
        search_url = f"{base_url}/esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': f"{keyword} AND {date_filter}",
            'retmax': max_papers,
            'retmode': 'json',
            'email': 'demo@example.com'
        }
        
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        pmids = data.get('esearchresult', {}).get('idlist', [])
        
        if not pmids:
            return jsonify({'error': '未找到相关文献'}), 404
        
        # 获取文献详情
        fetch_url = f"{base_url}/efetch.fcgi"
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'rettype': 'abstract',
            'email': 'demo@example.com'
        }
        
        response = requests.get(fetch_url, params=params, timeout=60)
        response.raise_for_status()
        
        # 解析XML
        soup = BeautifulSoup(response.content, 'xml')
        articles = soup.find_all('PubmedArticle')
        
        papers = []
        key_findings = []
        all_keywords = []
        authors_count = {}
        journals_count = {}
        
        for article in articles[:max_papers]:
            try:
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
                            author_name = f"{fore_name} {last_name}"
                            authors.append(author_name)
                            authors_count[author_name] = authors_count.get(author_name, 0) + 1
                
                # 提取期刊
                journal = article.find('Title').text if article.find('Title') else ''
                if journal:
                    journals_count[journal] = journals_count.get(journal, 0) + 1
                
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
                    keywords = [kw.text.lower() for kw in keyword_list.find_all('Keyword')]
                    all_keywords.extend(keywords)
                
                papers.append({
                    'pmid': pmid,
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'journal': journal,
                    'year': year,
                    'doi': doi,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ''
                })
                
                # 提取关键发现
                if abstract:
                    sentences = abstract.split('. ')
                    for sentence in sentences:
                        if any(k in sentence.lower() for k in ['result', 'conclusion', 'find', 'show', 'demonstrate', 'indicate']):
                            key_findings.append(f"[{pmid}] {sentence.strip()}")
                            break
                            
            except Exception as e:
                logger.warning(f"解析文献失败: {str(e)}")
                continue
        
        # 统计关键词
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_authors = dict(sorted(authors_count.items(), key=lambda x: x[1], reverse=True)[:10])
        top_journals = dict(sorted(journals_count.items(), key=lambda x: x[1], reverse=True)[:10])
        trending_topics = dict(keyword_counts.most_common(20))
        
        # 生成报告
        report_content = f"""# 文献分析报告: {keyword}

## 基本信息
- 分析时间: {datetime.now().isoformat()}
- 文献数量: {len(papers)} 篇
- 时间范围: 最近{days}天

## 统计信息
- 年份分布: {json.dumps(Counter([p.get('year', '') for p in papers if p.get('year')]), indent=2, ensure_ascii=False)}
- 平均作者数: {round(pd.Series([len(p.get('authors', [])) for p in papers]).mean(), 1)}

## 热点主题
{json.dumps(trending_topics, indent=2, ensure_ascii=False)}

## 高产作者
{json.dumps(top_authors, indent=2, ensure_ascii=False)}

## 高产期刊
{json.dumps(top_journals, indent=2, ensure_ascii=False)}

## 关键发现
{chr(10).join(f"- {finding}" for finding in key_findings[:20])}

## 文献列表
{chr(10).join(f"### {i+1}. {paper['title']}
- **作者**: {', '.join(paper['authors'][:3])}{' et al.' if len(paper['authors'])>3 else ''}
- **期刊**: {paper['journal']} ({paper['year']})
- **DOI**: {paper['doi'] if paper['doi'] else 'N/A'}
- **链接**: {paper['url']}
- **摘要**: {paper['abstract'][:300]}...

" for i, paper in enumerate(papers[:20]))}
"""
        
        # 保存报告
        output_dir = tempfile.mkdtemp()
        output_path = os.path.join(output_dir, 'literature_report.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return jsonify({
            'success': True,
            'total_papers': len(papers),
            'key_findings': key_findings[:20],
            'trending_topics': trending_topics,
            'top_authors': top_authors,
            'top_journals': top_journals,
            'report_content': report_content,
            'download_url': url_for('download_file', path=output_path)
        })
    
    except Exception as e:
        logger.error(f"文献分析失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admet/predict', methods=['POST'])
def api_admet_predict():
    """ADMET预测API（轻量化版本，仅基于规则）"""
    try:
        if calculate_molecular_properties is None:
            return jsonify({'error': '化学信息学工具未加载，请使用本地部署版本'}), 501
        
        # 处理两种情况：单个SMILES或上传文件
        if 'file' in request.files:
            # 批量模式
            file = request.files['file']
            if not file.filename.endswith('.csv'):
                return jsonify({'error': '请上传CSV格式文件'}), 400
            
            # 保存上传的文件
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(input_path)
            
            # 读取文件
            df = pd.read_csv(input_path)
            if 'smiles' not in df.columns:
                return jsonify({'error': 'CSV文件需要包含smiles列'}), 400
            
            results = []
            stats = {
                'priority': 0,
                'optimization': 0,
                'evaluation': 0,
                'elimination': 0
            }
            
            for _, row in df.iterrows():
                smiles = row['smiles']
                props = calculate_molecular_properties(smiles)
                if not props:
                    continue
                
                # 基于规则的ADMET评估
                score = 0.0
                decision = '建议淘汰'
                
                # 计算评分
                if props['follows_lipinski']:
                    score += 0.3
                if props['qed'] > 0.6:
                    score += 0.2
                elif props['qed'] > 0.3:
                    score += 0.1
                
                if props['tpsa'] < 140:
                    score += 0.15
                if props['logp'] > 0 and props['logp'] < 5:
                    score += 0.15
                if props['rotatable_bonds'] < 10:
                    score += 0.1
                if props['h_donors'] < 5:
                    score += 0.1
                
                # 决策
                if score >= 0.8:
                    decision = '优先开发'
                    stats['priority'] += 1
                elif score >= 0.6:
                    decision = '进一步优化'
                    stats['optimization'] += 1
                elif score >= 0.4:
                    decision = '谨慎评估'
                    stats['evaluation'] += 1
                else:
                    decision = '建议淘汰'
                    stats['elimination'] += 1
                
                results.append({
                    'smiles': smiles,
                    'overall_score': round(score, 3),
                    'admet_decision': decision,
                    'physchem_molecular_weight': props['molecular_weight'],
                    'physchem_logp': props['logp'],
                    'physchem_qed': props['qed'],
                    'physchem_tpsa': props['tpsa'],
                    'toxicity_overall_toxicity_risk': '低' if score > 0.6 else '中' if score > 0.3 else '高'
                })
            
            # 保存结果
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, 'admet_results.csv')
            pd.DataFrame(results).to_csv(output_path, index=False)
            
            return jsonify({
                'success': True,
                'mode': 'batch',
                'total_compounds': len(results),
                'average_score': round(pd.Series([r['overall_score'] for r in results]).mean(), 2),
                'statistics': stats,
                'results_preview': results[:20],
                'download_url': url_for('download_file', path=output_path)
            })
        
        else:
            # 单模式
            data = request.json
            smiles = data.get('smiles')
            
            if not smiles:
                return jsonify({'error': '请输入SMILES字符串'}), 400
            
            props = calculate_molecular_properties(smiles)
            if not props:
                return jsonify({'error': '无效的SMILES字符串'}), 400
            
            # 计算评分
            score = 0.0
            if props['follows_lipinski']:
                score += 0.3
            if props['qed'] > 0.6:
                score += 0.2
            elif props['qed'] > 0.3:
                score += 0.1
            
            if props['tpsa'] < 140:
                score += 0.15
            if props['logp'] > 0 and props['logp'] < 5:
                score += 0.15
            if props['rotatable_bonds'] < 10:
                score += 0.1
            if props['h_donors'] < 5:
                score += 0.1
            
            # 决策
            if score >= 0.8:
                decision = '优先开发'
            elif score >= 0.6:
                decision = '进一步优化'
            elif score >= 0.4:
                decision = '谨慎评估'
            else:
                decision = '建议淘汰'
            
            # 生成报告
            report_content = f"""# ADMET性质预测报告

## 基本信息
- SMILES: {smiles}
- 预测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 综合评分: {round(score, 3)}
- 决策建议: **{decision}**

## 理化性质
| 性质 | 值 |
|------|----|
| 分子量 | {props['molecular_weight']:.1f} |
| LogP | {props['logp']:.2f} |
| 氢键供体 | {props['h_donors']} |
| 氢键受体 | {props['h_acceptors']} |
| TPSA | {props['tpsa']:.1f} |
| QED | {props['qed']:.3f} |
| Lipinski规则违反 | {props['lipinski_violations']} |
| 是否符合Lipinski规则 | {'是' if props['follows_lipinski'] else '否'} |

## 性质预测
| 性质 | 预测结果 |
|------|----------|
| 口服生物利用度 | {'高' if props['tpsa'] < 140 and props['follows_lipinski'] else '中' if props['tpsa'] < 200 else '低'} |
| 血脑屏障穿透性 | {'高' if props['molecular_weight'] < 450 and props['logp'] > 0.4 and props['logp'] < 4 else '低'} |
| 代谢稳定性 | {'高' if props['rotatable_bonds'] <= 5 else '中' if props['rotatable_bonds'] <= 10 else '低'} |
| 总体毒性风险 | {'低' if score > 0.6 else '中' if score > 0.3 else '高'} |
"""
            
            # 保存报告
            output_dir = tempfile.mkdtemp()
            report_path = os.path.join(output_dir, 'admet_report.md')
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            return jsonify({
                'success': True,
                'mode': 'single',
                'smiles': smiles,
                'overall_score': round(score, 3),
                'decision': decision,
                'detailed_results': {
                    'physicochemical_properties': props,
                    'absorption': {
                        'oral_bioavailability': '高' if props['tpsa'] < 140 and props['follows_lipinski'] else '中' if props['tpsa'] < 200 else '低'
                    },
                    'distribution': {
                        'bbb_permeability': '高' if props['molecular_weight'] < 450 and props['logp'] > 0.4 and props['logp'] < 4 else '低'
                    },
                    'metabolism': {
                        'metabolic_stability': '高' if props['rotatable_bonds'] <= 5 else '中' if props['rotatable_bonds'] <= 10 else '低'
                    },
                    'toxicity': {
                        'overall_toxicity_risk': '低' if score > 0.6 else '中' if score > 0.3 else '高'
                    }
                },
                'report_content': report_content,
                'download_url': url_for('download_file', path=report_path)
            })
    
    except Exception as e:
        logger.error(f"ADMET预测失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/screening/run', methods=['POST'])
def api_screening_run():
    """虚拟筛选API（轻量化版本）"""
    try:
        return jsonify({
            'error': '虚拟筛选功能需要AutoDock Vina和更多计算资源，建议使用本地部署版本或部署到GPU服务器'
        }), 501
    
    except Exception as e:
        logger.error(f"虚拟筛选失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:path>')
def download_file(path):
    """下载文件"""
    try:
        return send_file(path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': '文件不存在'}), 404

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok', 
        'message': 'OpenClaw Drug Light API is running',
        'features': ['literature-analysis', 'admet-prediction (rule-based)'],
        'note': 'Full AI features available in local deployment'
    })

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='OpenClaw Drug Light Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=7890, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"""
🚀 OpenClaw Drug Light 界面启动成功！

📱 访问地址: http://{args.host}:{args.port}
🧪 功能模块 (轻量化版本):
   • 文献分析 - 自动搜索和分析学术文献
   • ADMET预测 - 基于规则的成药性预测
   
⚠️  完整功能（AI预测、虚拟筛选）请使用本地部署版本。
""")
    
    app.run(host=args.host, port=args.port, debug=args.debug)