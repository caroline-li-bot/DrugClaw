#!/usr/bin/env python3
"""
Result analysis and ranking for virtual screening
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional

def analyze_results(results: List[Dict], output_csv: Optional[str] = None) -> pd.DataFrame:
    """
    Analyze and rank docking results
    
    Args:
        results: List of dicts with keys: index, smiles, affinity_kcal_mol
        output_csv: Output CSV file path
    
    Returns:
        Ranked DataFrame sorted by affinity (lower = better binding)
    """
    df = pd.DataFrame(results)
    
    # Sort by affinity (lower = better binding)
    df = df.sort_values('affinity_kcal_mol', ascending=True)
    
    # Add rank
    df = df.reset_index(drop=True)
    df['rank'] = df.index + 1
    
    # Add Z-score
    if len(df) > 5:
        mean_aff = df['affinity_kcal_mol'].mean()
        std_aff = df['affinity_kcal_mol'].std()
        df['affinity_zscore'] = (df['affinity_kcal_mol'] - mean_aff) / std_aff
    
    if output_csv:
        df.to_csv(output_csv, index=False)
    
    return df

def select_top_n(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Select top N compounds by affinity"""
    return df.head(n)

def filter_by_affinity(df: pd.DataFrame, max_affinity: float = -7.0) -> pd.DataFrame:
    """Filter compounds with affinity better than threshold (lower = better)"""
    return df[df['affinity_kcal_mol'] <= max_affinity]

def summary_statistics(df: pd.DataFrame) -> Dict:
    """Calculate summary statistics"""
    return {
        'total_compounds': len(df),
        'mean_affinity': df['affinity_kcal_mol'].mean(),
        'min_affinity': df['affinity_kcal_mol'].min(),
        'max_affinity': df['affinity_kcal_mol'].max(),
        'std_affinity': df['affinity_kcal_mol'].std(),
        'count_below_-7': len(filter_by_affinity(df, -7.0)),
        'count_below_-9': len(filter_by_affinity(df, -9.0))
    }

def generate_report(df: pd.DataFrame, output_md: str) -> None:
    """Generate a Markdown report of screening results"""
    stats = summary_statistics(df)
    
    lines = [
        "# Virtual Screening Results Report\n",
        f"**Total compounds docked:** {stats['total_compounds']}\n",
        f"**Mean affinity:** {stats['mean_affinity']:.2f} kcal/mol\n",
        f"**Best affinity:** {stats['min_affinity']:.2f} kcal/mol\n",
        f"**Compounds with affinity < -7 kcal/mol:** {stats['count_below_-7']}\n",
        f"**Compounds with affinity < -9 kcal/mol:** {stats['count_below_-9']}\n",
        "\n## Top 10 Compounds\n",
    ]
    
    top10 = df.head(10)
    lines.append("| Rank | Affinity (kcal/mol) | SMILES |")
    lines.append("|------|---------------------|--------|")
    
    for _, row in top10.iterrows():
        rank = row['rank']
        aff = f"{row['affinity_kcal_mol']:.2f}"
        smiles = row['smiles'][:50] + ('...' if len(row['smiles']) > 50 else '')
        lines.append(f"| {rank} | {aff} | {smiles} |")
    
    with open(output_md, 'w') as f:
        f.write('\n'.join(lines))
