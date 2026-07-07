# AI Data Engineering

This repository is a small Python project focused on AI-assisted data engineering workflows. It includes a starter application entry point plus notebooks for exploring retrieval-augmented generation (RAG), multi-agentic data analysis, and data modeling with LLM-based workflows.

## Project Overview

The project currently includes:

- A simple Python entry point in [main.py](main.py)
- Jupyter notebooks for experimentation and analysis:
  - [RAG_Multi_Agentic_Data_Analysis.ipynb](RAG_Multi_Agentic_Data_Analysis.ipynb)
  - [RAG_NN_ADM_Data_Modeling_GPT.ipynb](RAG_NN_ADM_Data_Modeling_GPT.ipynb)
- Generated outputs in [Output](Output)
- Source assets in [Source](Source)

## Tech Stack

The project uses Python with several AI and data-related dependencies, including:

- LangChain and LangChain Community
- OpenAI agents
- Chroma / ChromaDB
- Oracle DB support
- PyPDF for document handling

These dependencies are defined in [pyproject.toml](pyproject.toml) and [requirements.txt](requirements.txt).

## Setup

### Prerequisites

- Python 3.14
- A valid OpenAI API key

### Install dependencies

From the project root, create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you are using the project metadata workflow, you can also use:

```bash
uv sync
```

### Environment variables

Copy [.env_example](.env_example) to .env and set your API key:

```bash
copy .env_example .env
```

Then update the value of OPENAI_API_KEY in [.env](.env).

## Run the application

Run the basic entry point with:

```bash
python main.py
```

## Repository Structure

```text
.
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── .env_example
├── RAG_Multi_Agentic_Data_Analysis.ipynb
├── RAG_NN_ADM_Data_Modeling_GPT.ipynb
├── Output/
└── Source/
```

## Notes

This repository is currently a starter/experimental workspace for AI-driven data engineering scenarios. The notebooks and output artifacts are the main place where the current analysis and modeling experiments live.
