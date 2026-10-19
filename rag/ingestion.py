"""
Policy Document Ingestion & Chunking Module for FinRecon.
Parses markdown policy files, extracts semantic header sections,
and attaches structured metadata.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class PolicyChunk(BaseModel):
    chunk_id: str
    source_file: str
    policy_type: str
    header: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


def parse_markdown_sections(file_path: Path) -> List[PolicyChunk]:
    """
    Parses a markdown document into semantic chunks separated by markdown headers (##).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    text = file_path.read_text(encoding="utf-8")
    filename = file_path.name
    policy_type = file_path.stem.replace("_policy", "").replace("_schedule", "")

    # Split by section headers (## 1. Title, ## 2. Title, etc.)
    sections = re.split(r'\n(?=##\s+)', text)
    chunks = []
    chunk_index = 1

    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # If the chunk is just the document title without body (e.g. starts with # and has no ##), skip or attach
        if section.startswith("# ") and not "\n##" in section and len(section.split("\n")) <= 2:
            continue

        # Extract title line
        lines = section.split("\n")
        header = lines[0].strip("# ").strip()
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else section

        chunks.append(PolicyChunk(
            chunk_id=f"{policy_type}_chunk_{chunk_index:03d}",
            source_file=filename,
            policy_type=policy_type,
            header=header,
            content=section,  # Keep full section for self-contained context
            metadata={
                "source": filename,
                "policy_type": policy_type,
                "header": header,
                "token_estimate": len(section.split())
            }
        ))
        chunk_index += 1

    return chunks


def ingest_all_policies(knowledge_dir: Path) -> List[PolicyChunk]:
    """Ingests and chunks all markdown files from the knowledge directory."""
    all_chunks = []
    for md_file in sorted(knowledge_dir.glob("*.md")):
        chunks = parse_markdown_sections(md_file)
        all_chunks.extend(chunks)
    return all_chunks
