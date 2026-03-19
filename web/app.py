#!/usr/bin/env python3
"""
OpenClaw Drug Web 界面
"""
from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
import json
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.literature_analysis import run_literature_analysis
from skills.admet_prediction import run_admet_prediction
from skills.virtual_screening import run_virtual_screening

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 上传限制
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # 生成输出路径
        output_dir = tempfile.mkdtemp()
        output_path = os.path.join(output_dir, 'literature_report.md')
        
        # 运行分析
        result = run_literature_analysis(
            keyword=keyword,
            output=output_path,
            max_papers=max_papers,
            days=days
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        # 读取报告内容
        with open(output_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        return jsonify({
            'success': True,
            'total_papers': result['total_papers'],
            'key_findings': result['key_findings'][:20],
            'trending_topics': result['trending_topics'],
            'top_authors': result['top_authors'],
            'top_journals': result['top_journals'],
            'report_content': report_content,
            'download_url': url_for('download_file', path=output_path)
        })
    
    except Exception as e:
        logger.error(f"文献分析失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admet/predict', methods=['POST'])
def api_admet_predict():
    """ADMET预测API"""
    try:
        # 处理两种情况：单个SMILES或上传文件
        if 'file' in request.files:
            # 批量模式
            file = request.files['file']
            if not file.filename.endswith('.csv'):
                return jsonify({'error': '请上传CSV格式文件'}), 400
            
            # 保存上传的文件
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(input_path)
            
            # 生成输出路径
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, 'admet_results.csv')
            
            # 运行预测
            result = run_admet_prediction(
                input_file=input_path,
                output=output_path
            )
            
            if 'error' in result:
                return jsonify(result), 400
            
            # 读取结果
            df = pd.read_csv(output_path)
            results_preview = df.head(20).to_dict('records')
            
            return jsonify({
                'success': True,
                'mode': 'batch',
                'total_compounds': result['total_compounds'],
                'average_score': result['average_score'],
                'statistics': {
                    'priority': result['priority_development'],
                    'optimization': result['further_optimization'],
                    'evaluation': result['careful_evaluation'],
                    'elimination': result['recommended_elimination']
                },
                'results_preview': results_preview,
                'download_url': url_for('download_file', path=output_path)
            })
        
        else:
            # 单模式
            data = request.json
            smiles = data.get('smiles')
            
            if not smiles:
                return jsonify({'error': '请输入SMILES字符串'}), 400
            
            # 生成输出路径
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, 'admet_results.csv')
            
            # 运行预测
            result = run_admet_prediction(
                smiles=smiles,
                output=output_path
            )
            
            if 'error' in result:
                return jsonify(result), 400
            
            # 读取报告内容
            report_path = result['report_path']
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            return jsonify({
                'success': True,
                'mode': 'single',
                'smiles': result['smiles'],
                'overall_score': result['overall_score'],
                'decision': result['decision'],
                'detailed_results': result['detailed_results'],
                'report_content': report_content,
                'download_url': url_for('download_file', path=report_path)
            })
    
    except Exception as e:
        logger.error(f"ADMET预测失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/screening/run', methods=['POST'])
def api_screening_run():
    """虚拟筛选API"""
    try:
        # 获取表单数据
        target_pdb = request.files.get('target_pdb')
        library_file = request.files.get('library_file')
        center_x = float(request.form.get('center_x', 0))
        center_y = float(request.form.get('center_y', 0))
        center_z = float(request.form.get('center_z', 0))
        size_x = float(request.form.get('size_x', 20))
        size_y = float(request.form.get('size_y', 20))
        size_z = float(request.form.get('size_z', 20))
        top_n = int(request.form.get('top_n', 20))
        
        if not target_pdb or not library_file:
            return jsonify({'error': '请上传靶点PDB文件和化合物库文件'}), 400
        
        # 保存上传的文件
        target_path = os.path.join(app.config['UPLOAD_FOLDER'], target_pdb.filename)
        target_pdb.save(target_path)
        
        library_path = os.path.join(app.config['UPLOAD_FOLDER'], library_file.filename)
        library_file.save(library_path)
        
        # 生成输出路径
        output_dir = tempfile.mkdtemp()
        output_path = os.path.join(output_dir, 'screening_results.csv')
        
        # 运行虚拟筛选
        result = run_virtual_screening(
            target_pdb=target_path,
            library_file=library_path,
            binding_site_center=(center_x, center_y, center_z),
            binding_site_size=(size_x, size_y, size_z),
            output=output_path,
            top_n=top_n
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        # 读取结果
        df = pd.read_csv(output_path)
        top_candidates = df.head(top_n).to_dict('records')
        
        # 读取报告内容
        report_path = output_path.replace('.csv', '_report.md')
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        return jsonify({
            'success': True,
            'total_compounds': result['total_compounds'],
            'best_affinity': result['best_affinity'],
            'top_candidates': top_candidates,
            'report_content': report_content,
            'download_url': url_for('download_file', path=output_path),
            'report_download_url': url_for('download_file', path=report_path)
        })
    
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
    return jsonify({'status': 'ok', 'message': 'OpenClaw Drug API is running'})

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='OpenClaw Drug Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=7890, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"""
🚀 OpenClaw Drug Web 界面启动成功！

📱 访问地址: http://{args.host}:{args.port}
🧪 功能模块:
   • 文献分析 - 自动搜索和分析学术文献
   • ADMET预测 - 预测化合物成药性
   • 虚拟筛选 - 自动化分子对接和化合物筛选
   
⚠️  注意：首次启动会自动下载AI模型，可能需要几分钟时间。
""")
    
    app.run(host=args.host, port=args.port, debug=args.debug)