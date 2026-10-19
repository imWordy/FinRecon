import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

# Paths
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", BASE_DIR / "knowledge"))
VECTOR_STORE_DIR = Path(os.getenv("VECTOR_STORE_DIR", BASE_DIR / "rag" / "faiss_index"))

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")

# RAG Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# General Settings
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 42))
