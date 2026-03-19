#!/usr/bin/env python3
"""
DrugClaw - AI-powered drug discovery assistant based on OpenClaw
"""

__version__ = "0.2.0"
__author__ = "DrugClaw Contributors"

# Lazy imports to allow using parts without OpenAI installed
def DrugClawSystem():
    from .main_system import DrugClawSystem
    return DrugClawSystem

def Config():
    from .config import Config
    return Config

def LiteratureRAG():
    from .rag.literature_rag import LiteratureRAG
    return LiteratureRAG

def RetrievedDocument():
    from .rag.literature_rag import RetrievedDocument
    return RetrievedDocument

def KnowledgeGraph():
    from .kg.graph_builder import KnowledgeGraph
    return KnowledgeGraph

def Triple():
    from .kg.graph_builder import Triple
    return Triple

def Entity():
    from .kg.graph_builder import Entity
    return Entity
