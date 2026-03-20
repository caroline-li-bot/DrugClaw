#!/usr/bin/env python3
"""
Planner Agent - Analyzes user query, identifies entities, selects relevant skills
"""

from typing import List, Dict, Optional, Any, Tuple
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QueryAnalysis:
    """Result of query analysis"""
    original_query: str
    entities: List[str]
    entity_types: Dict[str, str]  # entity -> type (drug/target/disease)
    selected_categories: List[str]
    selected_skills: List[str]
    thinking_mode: str  # simple/graph/web_only
    requires_web_search: bool

class PlannerAgent:
    """Query planning agent that selects appropriate skills"""
    
    # Category keywords mapping
    CATEGORY_KEYWORDS = {
        'dti': [
            'target', 'binding', 'interaction', 'bind', 'affinity', 'inhibitor', 
            'agonist', 'antagonist', 'dti', 'drug-target'
        ],
        'adr': [
            'side effect', 'adverse', 'toxicity', 'toxic', 'safety', 'allergy', 
            'reaction', 'adr', 'warning'
        ],
        'ddi': [
            'interaction', 'interact', 'combined', 'combination', 'ddi', 
            'drug-drug'
        ],
        'pgx': [
            'pharmacogenomic', 'pgx', 'genotype', 'cyp2c19', 'cyp2d6', 
            'metabolism', 'allele', 'variant'
        ],
        'repurposing': [
            'repurpose', 'repurposing', 'reposition', 'repositioning', 
            'new indication', 'old drug'
        ],
        'knowledgebase': [
            'drugbank', 'information', 'summary', 'details', 'about', 
            'knowledgebase', 'drug information'
        ],
        'mechanism': [
            'mechanism', 'pathway', 'signaling', 'how does it work', 
            'mode of action', 'moa'
        ],
        'labeling': [
            'label', 'prescribing', 'dosage', 'contraindication', 
            'indication', 'package insert', 'labeling'
        ],
        'toxicity': [
            'toxicity', 'carcinogenic', 'mutagenic', 'liver', 'kidney', 
            'neurotoxicity', 'toxic'
        ],
        'ontology': [
            'ontology', 'concept', 'identifier', 'atc code', 'rxnorm', 
            'chebi', 'normalization'
        ],
        'combination': [
            'combination', 'synergy', 'combination therapy', 'combo', 
            'drug-comb'
        ],
        'properties': [
            'property', 'properties', 'molecular weight', 'logp', 'qed', 
            'admet', 'solubility', 'lipinski'
        ],
        'disease': [
            'disease', 'indication', 'treatment', 'association', 
            'drug-disease'
        ],
        'reviews': [
            'review', 'patient', 'experience', 'side effects reported', 
            'user review'
        ],
        'nlp': [
            'corpus', 'dataset', 'extraction', 'ner', 'relation', 
            'text mining'
        ]
    }
    
    # Entity patterns
    DRUG_PATTERNS = [
        r'\b([A-Z][a-z]+(?:ib|mab|zumab|ximab|inib|afil|olol|afil|sartan|pril|floxacin))\b',
        r'\b(aspirin|metformin|imatinib|gefitinib|erlotinib|sorafenib|sunitinib)\b'
    ]
    
    TARGET_PATTERNS = [
        r'\b(EGFR|HER2|VEGF|BRAF|KRAS|ALK|PDGFR|ABL|BCR-ABL|PI3K|AKT|mTOR|TREM2)\b',
        r'\b\w+ kinase\b', r'\breceptor\b'
    ]
    
    DISEASE_PATTERNS = [
        r'\b(cancer|carcinoma|lymphoma|leukemia|diabetes|alzheimer|parkinson|asthma|arthritis)\b',
        r'\b(breast cancer|lung cancer|prostate cancer|melanoma)\b'
    ]
    
    def __init__(self):
        self.compiled_patterns = {
            'drug': [re.compile(p, re.I) for p in self.DRUG_PATTERNS],
            'target': [re.compile(p, re.I) for p in self.TARGET_PATTERNS],
            'disease': [re.compile(p, re.I) for p in self.DISEASE_PATTERNS]
        }
    
    def analyze(self, query: str) -> QueryAnalysis:
        """Analyze user query and select appropriate skills"""
        
        # Identify entities
        entities = []
        entity_types = {}
        
        for entity_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(query)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    if match not in entities:
                        entities.append(match)
                        entity_types[match] = entity_type
        
        # If no entities found via regex, extract capitalized words as potential entities
        if not entities:
            words = re.findall(r'\b[A-Z][a-z]{2,}\b', query)
            for word in words:
                if word not in ['What', 'Where', 'When', 'Which', 'How', 'Does', 'Is', 'Are', 'The']:
                    entities.append(word)
        
        # Select categories based on keywords
        selected_categories = []
        query_lower = query.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if category not in selected_categories:
                        selected_categories.append(category)
                    break
        
        # Auto-select categories based on entity types
        # If we have target entities, add dti category
        if any(et == 'target' for et in entity_types.values()) and 'dti' not in selected_categories:
            selected_categories.append('dti')
        # If we have drug entities, add knowledgebase category
        if any(et == 'drug' for et in entity_types.values()) and 'knowledgebase' not in selected_categories:
            selected_categories.append('knowledgebase')
        # If we have disease entities, add disease category (already added if keyword matched)
        if any(et == 'disease' for et in entity_types.values()) and 'disease' not in selected_categories:
            selected_categories.append('disease')
        
        # Default to knowledgebase if no category matched
        if not selected_categories:
            selected_categories = ['knowledgebase']
        
        # Determine thinking mode
        requires_web_search = any(word in query_lower for word in 
            ['recent', 'latest', 'new', '2024', '2025', 'current', 'update'])
        
        if len(selected_categories) <= 1 and len(entities) <= 2:
            thinking_mode = 'simple'
        else:
            thinking_mode = 'graph'  # Multi-hop reasoning needed
        
        if requires_web_search and thinking_mode != 'graph':
            thinking_mode = 'graph'
        
        # Get all skills in selected categories (simplified - registry will handle this)
        selected_skills = []  # Will be filled by registry
        
        logger.info(f"Query analysis: {len(entities)} entities, {len(selected_categories)} categories, mode={thinking_mode}")
        
        return QueryAnalysis(
            original_query=query,
            entities=entities,
            entity_types=entity_types,
            selected_categories=selected_categories,
            selected_skills=selected_skills,
            thinking_mode=thinking_mode,
            requires_web_search=requires_web_search
        )
    
    def get_skill_categories(self) -> List[str]:
        """Get all available skill categories"""
        return list(self.CATEGORY_KEYWORDS.keys())
