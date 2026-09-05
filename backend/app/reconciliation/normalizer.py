"""Normalization utilities for references, text, and dates to assist matching."""

import re

def normalize_text(text: str) -> str:
    """Lowercases, strips leading/trailing whitespace, and removes redundant internal spaces."""
    if not text:
        return ""
    text = text.lower().strip()
    return re.sub(r"\s+", " ", text)


def normalize_reference(ref: str) -> str:
    """Removes non-alphanumeric characters for fuzzy matching."""
    if not ref:
        return ""
    ref = ref.lower().strip()
    return re.sub(r"[^a-z0-9]", "", ref)


def extract_potential_ids(narration: str) -> set:
    """Extracts tokens that look like settlement IDs, UTRs, or transaction IDs."""
    if not narration:
        return set()
    
    # Normalize narration slightly for tokenization
    clean_narration = narration.upper().replace("/", " ").replace(":", " ").replace("-", " ")
    tokens = clean_narration.split()
    
    # We can return all tokens, or just things that look like identifiers.
    # To be safe, we just return the normalized text set.
    # The caller will do substring matching for exact known IDs.
    return set(tokens)


def contains_id_in_narration(narration: str, target_id: str) -> bool:
    """Checks if a known target_id (like a settlement ID or UTR) is cleanly embedded in the narration."""
    if not narration or not target_id:
        return False
    
    n_narration = normalize_reference(narration)
    n_target = normalize_reference(target_id)
    
    return n_target in n_narration
