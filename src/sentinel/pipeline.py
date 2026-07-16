# src/sentinel/pipeline.py
"""
Sentinel Pipeline

The complete Sentinel-RAG security layer.
Combines detection and neutralization into a single middleware.

Usage:
    sentinel = SentinelPipeline()
    safe_chunks = sentinel.process(retrieved_chunks)
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .detector import DetectionResult, SentinelDetector, ThreatLevel, create_detector
from .neutralizer import NeutralizationResult, SentinelNeutralizer, create_neutralizer


@dataclass
class ProcessedChunk:
    """A chunk that has been through the Sentinel pipeline"""

    original_text: str
    processed_text: str
    was_threat: bool
    threat_level: ThreatLevel
    confidence: float
    was_neutralized: bool
    detection_result: DetectionResult
    neutralization_result: Optional[NeutralizationResult]
    processing_time_ms: float


@dataclass
class PipelineStats:
    """Statistics from a pipeline run"""

    total_chunks: int = 0
    threats_detected: int = 0
    chunks_neutralized: int = 0
    threat_levels: dict = field(default_factory=dict)
    avg_confidence: float = 0.0
    total_processing_time_ms: float = 0.0


class SentinelPipeline:
    """
    The complete Sentinel security layer for RAG systems.

    Pipeline flow:
    1. Receive retrieved chunks
    2. Detect threats using SentinelDetector
    3. Neutralize threats using SentinelNeutralizer
    4. Return sanitized chunks ready for the main LLM
    """

    # Default model - ProtectAI's fine-tuned DeBERTa for prompt injection
    DEFAULT_MODEL = "protectai/deberta-v3-base-prompt-injection-v2"

    def __init__(
        self,
        detector: Optional[SentinelDetector] = None,
        neutralizer: Optional[SentinelNeutralizer] = None,
        model_name: Optional[str] = None,
        detection_threshold: float = 0.5,
        enabled: bool = True,
    ):
        """
        Initialize the Sentinel Pipeline.

        Args:
            detector: Custom detector instance (or None to create default)
            neutralizer: Custom neutralizer instance (or None to create default)
            model_name: Model for detection if creating default detector
            detection_threshold: Confidence threshold for threat classification
            enabled: Whether the pipeline is active (False = passthrough)
        """
        model_to_use = model_name or self.DEFAULT_MODEL

        self.detector = detector or create_detector(
            model_name=model_to_use, threshold=detection_threshold
        )
        self.neutralizer = neutralizer or create_neutralizer()
        self.enabled = enabled

        # Stats tracking
        self._stats = PipelineStats()
        self._processing_history: List[ProcessedChunk] = []

    def process_chunk(self, text: str) -> ProcessedChunk:
        """
        Process a single text chunk through the Sentinel pipeline.

        Args:
            text: The raw text chunk from retrieval

        Returns:
            ProcessedChunk with either original or neutralized text
        """
        import time

        start_time = time.time()

        # If disabled, passthrough
        if not self.enabled:
            return ProcessedChunk(
                original_text=text,
                processed_text=text,
                was_threat=False,
                threat_level=ThreatLevel.NONE,
                confidence=0.0,
                was_neutralized=False,
                detection_result=None,
                neutralization_result=None,
                processing_time_ms=0.0,
            )

        # Step 1: Detect
        detection = self.detector.detect(text)

        # Step 2: Neutralize if threat detected
        neutralization = None
        processed_text = text

        if detection.is_threat:
            neutralization = self.neutralizer.neutralize(
                text, threat_level=detection.threat_level.value
            )
            processed_text = neutralization.neutralized_text

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        result = ProcessedChunk(
            original_text=text,
            processed_text=processed_text,
            was_threat=detection.is_threat,
            threat_level=detection.threat_level,
            confidence=detection.confidence,
            was_neutralized=neutralization.was_modified if neutralization else False,
            detection_result=detection,
            neutralization_result=neutralization,
            processing_time_ms=processing_time,
        )

        # Update stats
        self._update_stats(result)

        return result

    def process(self, chunks: List[str]) -> List[str]:
        """
        Process multiple chunks and return sanitized texts.

        This is the main interface for RAG integration.

        Args:
            chunks: List of retrieved text chunks

        Returns:
            List of sanitized text chunks (same order)
        """
        results = [self.process_chunk(chunk) for chunk in chunks]
        self._processing_history.extend(results)
        return [r.processed_text for r in results]

    def process_with_details(self, chunks: List[str]) -> List[ProcessedChunk]:
        """
        Process chunks and return full details (for debugging/evaluation).
        """
        results = [self.process_chunk(chunk) for chunk in chunks]
        self._processing_history.extend(results)
        return results

    def _update_stats(self, result: ProcessedChunk):
        """Update running statistics"""
        self._stats.total_chunks += 1

        if result.was_threat:
            self._stats.threats_detected += 1
            level = result.threat_level.value
            self._stats.threat_levels[level] = self._stats.threat_levels.get(level, 0) + 1

        if result.was_neutralized:
            self._stats.chunks_neutralized += 1

        # Running average of confidence
        n = self._stats.total_chunks
        self._stats.avg_confidence = (self._stats.avg_confidence * (n - 1) + result.confidence) / n

        self._stats.total_processing_time_ms += result.processing_time_ms

    def get_stats(self) -> PipelineStats:
        """Get current pipeline statistics"""
        return self._stats

    def get_history(self) -> List[ProcessedChunk]:
        """Get processing history"""
        return self._processing_history

    def reset_stats(self):
        """Reset statistics and history"""
        self._stats = PipelineStats()
        self._processing_history = []

    def enable(self):
        """Enable the pipeline"""
        self.enabled = True

    def disable(self):
        """Disable the pipeline (passthrough mode)"""
        self.enabled = False

    def summary(self) -> str:
        """Get a human-readable summary of pipeline activity"""
        stats = self._stats
        if stats.total_chunks == 0:
            return "No chunks processed yet."

        threat_rate = (stats.threats_detected / stats.total_chunks) * 100
        neutralize_rate = (stats.chunks_neutralized / stats.total_chunks) * 100
        avg_time = stats.total_processing_time_ms / stats.total_chunks

        lines = [
            "=== Sentinel Pipeline Summary ===",
            f"Total chunks processed: {stats.total_chunks}",
            f"Threats detected: {stats.threats_detected} ({threat_rate:.1f}%)",
            f"Chunks neutralized: {stats.chunks_neutralized} ({neutralize_rate:.1f}%)",
            f"Average confidence: {stats.avg_confidence:.2f}",
            f"Average processing time: {avg_time:.2f}ms per chunk",
            "",
            "Threat level breakdown:",
        ]

        for level, count in sorted(stats.threat_levels.items()):
            lines.append(f"  - {level}: {count}")

        return "\n".join(lines)


# Convenience function
def create_pipeline(
    model_name: str = "protectai/deberta-v3-base-prompt-injection-v2",
    threshold: float = 0.5,
    enabled: bool = True,
) -> SentinelPipeline:
    """Factory function to create a configured pipeline"""
    return SentinelPipeline(model_name=model_name, detection_threshold=threshold, enabled=enabled)
