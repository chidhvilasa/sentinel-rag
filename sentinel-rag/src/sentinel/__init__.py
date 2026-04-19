"""
Sentinel Module - Defense against Indirect Prompt Injection

This module provides the core security layer for Sentinel-RAG:
- Detection of imperative commands in retrieved text
- Neutralization via semantic transformation to passive voice
- Full pipeline integration for RAG systems
"""

from .detector import (
    SentinelDetector,
    DetectionResult,
    ThreatLevel,
    create_detector
)

from .neutralizer import (
    SentinelNeutralizer,
    NeutralizationResult,
    NeutralizationStrategy,
    create_neutralizer
)

from .pipeline import (
    SentinelPipeline,
    ProcessedChunk,
    PipelineStats,
    create_pipeline
)

__all__ = [
    # Detector
    "SentinelDetector",
    "DetectionResult", 
    "ThreatLevel",
    "create_detector",
    # Neutralizer
    "SentinelNeutralizer",
    "NeutralizationResult",
    "NeutralizationStrategy",
    "create_neutralizer",
    # Pipeline
    "SentinelPipeline",
    "ProcessedChunk",
    "PipelineStats",
    "create_pipeline",
]
