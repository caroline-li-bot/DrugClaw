#!/usr/bin/env python3
"""
文献分析使用示例
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.literature_analysis import run_literature_analysis

def main():
    # 示例：分析EGFR抑制剂相关文献
    print("开始分析EGFR抑制剂相关文献...")
    
    result = run_literature_analysis(
        keyword="EGFR inhibitor",
        output="egfr_literature_report.md",
        max_papers=50,
        days=180  # 最近半年的文献
    )
    
    if 'error' in result:
        print(f"分析失败: {result['error']}")
        return
    
    print(f"分析完成!")
    print(f"总文献数: {result['total_papers']}")
    print(f"报告路径: {result['report_path']}")
    
    # 打印关键发现
    print("\n关键发现:")
    for i, finding in enumerate(result['key_findings'][:10]):
        print(f"{i+1}. {finding[:200]}...")
    
    # 打印热点主题
    print("\n热点主题:")
    for topic, count in list(result['trending_topics'].items())[:10]:
        print(f"- {topic}: {count}次")

if __name__ == "__main__":
    main()