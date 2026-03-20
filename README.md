<p align="center">
  <img src="https://raw.githubusercontent.com/caroline-li-bot/DrugClaw/main/support/DrugClaw_Logo.jpg" alt="DrugClaw Logo" width="600"/>
</p>

<h1 align="center">DrugClaw</h1>
<p align="center">
  <strong>AI-powered full-stack drug discovery assistant based on OpenClaw</strong><br>
  Accelerate your drug discovery workflow from literature analysis to experimental design
</p>

<p align="center">
  <a href="https://github.com/caroline-li-bot/DrugClaw/blob/main/LICENSE"><img src="https://img.shields.io/github/license/caroline-li-bot/DrugClaw.svg" alt="License"></a>
  <a href="https://pypi.org/project/drugclaw/"><img src="https://img.shields.io/pypi/v/drugclaw.svg" alt="PyPI"></a>
  <a href="https://img.shields.io/badge/domain-drug%20discovery-blue.svg"><img src="https://img.shields.io/badge/domain-drug%20discovery-blue.svg" alt="Domain"></a>
  <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style"></a>
</p>

<p align="center">
  <a href="./README_CN.md">中文 README</a>
</p>

---

# 🎯 What makes DrugClaw different

**DrugClaw is an OpenClaw-native full-stack drug discovery assistant. Just talk to it like you talk to me - it does the work for you.**

✅ **Completely conversational** - No scripting, no command-line fighting, just tell it what target you're interested in, it plans and executes step-by-step  
✅ **Full pipeline from literature to candidate molecules** - From literature review to virtual screening, you get a ranked list of candidate molecules ready for experimental validation  
✅ **15-category skill tree** - Covers drug-target interactions, adverse reactions, drug-drug interactions, pharmacogenomics, drug repurposing, and more  
✅ **Agentic "vibe coding"** - Each data source has a SKILL.md + example.py, the CodeAgent writes the query code for you, no need to pre-write everything  
✅ **Three-level fallback** - Pre-written scripts → LLM code generation → skill module, always gracefully degraded  

Give it a target protein that you think is associated with a disease, it will help you find candidate small molecule binders. That's it.

## 🎯 What DrugClaw Does

DrugClaw covers the full drug discovery pipeline with an agentic workflow:

### 🔍 Literature & Knowledge
- **Literature Analysis** - Automatic PubMed search, key information extraction, trend analysis
- **Target Intelligence** - Build target dossiers from UniProt, OpenTargets, Reactome, STRING, ClinVar
- **Evidence Synthesis** - Aggregate evidence from multiple databases for reasoned conclusions

### 🧪 Compound Screening & Prediction
- **Virtual Screening** - Automated molecular docking with AutoDock Vina, post-processing and ranking
- **ADMET Prediction** - Heuristic ADMET property prediction using ChemBERTa
- **Drug-Target Interaction (DTI)** - Query ChEMBL, BindingDB, DGIdb, TTD for known interactions
- **Molecule Generation** - Generate novel molecules based on scaffold constraints

### 📊 Data Analysis & Experimental Design
- **Experimental Protocol Design** - Automatic cell/animal experiment protocol generation
- **Statistical Analysis** - Automated data processing, visualization and statistical testing
- **Clinical Trial Design** - Protocol design assistance, eligibility criteria selection

### 🔬 Domain-Specific Skills

| Category | Description |
|----------|-------------|
| **Adverse Drug Reactions (ADR)** | Query FAERS, SIDER, nSIDES for adverse drug reactions |
| **Drug-Drug Interactions (DDI)** | Check interaction data from multiple sources |
| **Pharmacogenomics (PGx)** | Query PharmGKB for genotype-guided dosing |
| **Drug Repurposing** | Identify repurposing opportunities from RepoDB, DRKG |
| And more... | See full [skill tree](#-skill-tree) below |

## 🗺️ Skill Tree (15 Categories)

| Category | Description | Data Sources |
|----------|-------------|--------------|
| **dti** | Drug-Target Interactions | ChEMBL, BindingDB, DGIdb, Open Targets, TTD, STITCH |
| **adr** | Adverse Drug Reactions | FAERS, SIDER, nSIDES, ADReCS |
| **ddi** | Drug-Drug Interactions | MecDDI, DDInter, KEGG Drug |
| **pgx** | Pharmacogenomics | PharmGKB, CPIC |
| **repurposing** | Drug Repurposing | RepoDB, DRKG, OREGANO, Drug Repurposing Hub |
| **knowledgebase** | Drug Knowledgebases | DrugBank, UniD3, IUPHAR/BPS, DrugCentral, WHO Essential Medicines |
| **mechanism** | Mechanisms of Action | DRUGMECHDB |
| **labeling** | Drug Labeling | DailyMed, openFDA, MedlinePlus |
| **toxicity** | Drug Toxicity | UniTox, LiverTox, DILIrank |
| **ontology** | Ontology & Normalization | RxNorm, ChEBI, ATC/DDD |
| **combination** | Drug Combinations | DrugCombDB, DrugComb |
| **properties** | Molecular Properties | GDSC, ChemBERTa |
| **disease** | Drug-Disease Associations | SemaTyP |
| **reviews** | Patient Reviews | WebMD, Drugs.com |
| **nlp** | NLP Datasets | DDI Corpus, DrugProt, ADE Corpus, CADEC |

## 🛠️ Tech Stack

- **OpenClaw** - Agent framework, skill system, memory, multi-channel support
- **RDKit** - Cheminformatics
- **ChemBERTa-2** - Molecular property prediction
- **ESMFold** - Protein structure prediction
- **DiffDock** - Molecular docking
- **AutoDock Vina** - Virtual screening
- **LangChain** - RAG and agent orchestration
- **OpenAI API** - LLM for code generation and reasoning

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/caroline-li-bot/DrugClaw.git
cd DrugClaw

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Install as OpenClaw skill
openclaw skill install .
```

See [DEPLOYMENT.md](https://github.com/caroline-li-bot/DrugClaw/blob/main/DEPLOYMENT.md) for more deployment options.

## 🚀 Quick Start

### 📋 End-to-End Example: Discover new molecules for your target

If you have a protein target that you want to discover new binders:

```bash
# 1. Install system dependencies (AutoDock Vina, OpenBabel, MGLTools)
sudo ./scripts/install_system_deps.sh

# 2. Literature review - understand your target
drugclaw run --query "Summarize recent research on TREM2 role in Alzheimer's disease"

# 3. Get target information from public databases
drugclaw run --query "Get target information for TREM2 including function and disease association"

# 4. Download sample compound library
python scripts/download_public_datasets.py --dataset zinc_15_sample --output-dir ./data

# 5. ADMET pre-filtering (filter out bad compounds)
drugclaw run --query "Predict ADMET for all compounds in data/zinc_15_sample/2k-compound-sample.csv --output admet_filtered.csv"

# 6. Parallel virtual screening (uses all CPU cores by default)
drugclaw virtual-screening \
  --receptor ./trem2.pdb \
  --center-x 10.0 --center-y 20.0 --center-z 30.0 \
  --size-x 20 --size-y 20 --size-z 20 \
  --input ./admet_filtered.csv \
  --output ./trem2_screening_results.csv
```

That's it! You'll get a CSV ranked by binding affinity, top candidates are ready for experimental validation.

---

### 1. Configure your API key

```bash
cp navigator_api_keys.example.json navigator_api_keys.json
# Edit navigator_api_keys.json and add your OpenAI API key
```

### 2. Check your setup

```bash
drugclaw doctor
drugclaw list
```

### 3. Run the demo

```bash
drugclaw demo
```

### 4. Run your own query

```bash
# Simple query
drugclaw run --query "What are the known drug targets of imatinib?"

# Complex query with graph reasoning
drugclaw run --query "What are the adverse drug reactions and interaction risks of combining warfarin with NSAIDs?" --thinking-mode graph

# Save as Markdown report
drugclaw run --query "Which approved drugs can be repurposed for triple-negative breast cancer?" --save-md-report
```

### As OpenClaw Skill

**The best experience - just install and chat!**

In OpenClaw chat, just ask naturally:
```
Find all known targets of imatinib and summarize potential adverse interactions
```

## 📁 Project Structure

```
DrugClaw/
├── drugclaw/                    # Main Python package
│   ├── __init__.py
│   ├── agent/                   # Agent architecture
│   │   ├── planner.py           # Query planning agent
│   │   ├── code_agent.py        # Code generation agent
│   │   └── responder.py         # Final answer synthesizer
│   ├── cli.py                   # Command-line interface
│   ├── config.py                # Configuration handling
│   ├── kg/                      # Knowledge graph builder and reasoner
│   ├── rag/                     # Literature RAG system
│   ├── virtual_screening/       # Parallel virtual screening with AutoDock Vina
│   └── main_system.py           # Main system entrypoint
├── skills/                      # 15-category skill tree
│   ├── dti/                     # Drug-Target Interactions
│   │   └── chembl/              # Per-source skill: SKILL.md, example.py, retrieve.py
│   ├── adr/                     # Adverse Drug Reactions
│   ├── ddi/                     # Drug-Drug Interactions
│   ├── pgx/                     # Pharmacogenomics
│   ├── repurposing/             # Drug Repurposing
│   ├── knowledgebase/           # Drug Knowledgebases
│   ├── mechanism/               # Mechanisms of Action
│   ├── labeling/                # Drug Labeling
│   ├── toxicity/                # Drug Toxicity
│   ├── ontology/                # Ontology & Normalization
│   ├── combination/             # Drug Combinations
│   ├── properties/              # Molecular Properties
│   ├── disease/                 # Drug-Disease Associations
│   ├── reviews/                 # Patient Reviews
│   └── nlp/                     # NLP Datasets
├── utils/                       # Utilities
│   ├── chem_utils.py            # Cheminformatics tools
│   ├── db_utils.py              # Database utilities
│   ├── ml_utils.py              # ML models
│   └── sota_models.py           # SOTA models (ChemBERTa, ESMFold, DiffDock)
├── examples/                    # Example usage scripts
├── docs/                        # Documentation
├── support/                     # Project assets (logo, images)
├── scripts/                     # Installation and data download scripts
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Package configuration
├── skill.yaml                   # OpenClaw skill manifest
└── README.md                    # This file
```

## 🎯 Differences from other DrugClaw projects

| Aspect | [DrugClaw/DrugClaw](https://github.com/DrugClaw/DrugClaw) | [QSong-github/DrugClaw](https://github.com/QSong-github/DrugClaw) | **caroline-li-bot/DrugClaw** |
|--------|-------------------|------------------------|-------------------|
| **Base** | Rust agent runtime | LangGraph Agentic RAG | **OpenClaw-native skill** |
| **Scope** | Full research workflow automation | Drug knowledge QA | **Full-stack drug discovery - from literature to candidate molecules** |
| **User Experience** | Standalone service | CLI / API | **Completely conversational** - you talk, it does the work |
| **Philosophy** | Generic agent with drug skills | Structured skill tree, vibe coding retrieval | **OpenClaw agent + 15-category skill tree + vibe coding + full pipeline to virtual screening** |

## 📊 Example Queries

- "What are the known targets, adverse effects, and interaction risks of imatinib?"
- "Which approved drugs may be repurposed for triple-negative breast cancer?"
- "What pharmacogenomic guidance exists for clopidogrel and CYP2C19?"
- "Are there clinically meaningful interactions between warfarin and NSAIDs?"
- "Predict ADMET properties for this SMILES: `CC1=CC=C(C=C1)NC(=O)C2=CC=C(O)C=C2`"

## 📄 License

MIT License - see [LICENSE](/LICENSE) for details.

## 🙏 Acknowledgments

- Inspired by [DrugClaw/DrugClaw](https://github.com/DrugClaw/DrugClaw) and [QSong-github/DrugClaw](https://github.com/QSong-github/DrugClaw)
- Built on top of the [OpenClaw](https://github.com/openclaw/openclaw) agent framework
- Uses publicly available biomedical databases and open-source tools

---

*DrugClaw is for research purposes only. It does not provide medical advice. All predictions should be experimentally validated.*
