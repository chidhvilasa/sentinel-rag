# Sentinel V5 modules
from .adversarial_tester import AdversarialTester
from .context_neutralizer import ContextAwareNeutralizer
from .explainer import DetectionExplainer
from .multilang_detector import MultiLangDetector
from .zeroshot_detector import ZeroShotDetector

# V4 exports
try:
    from .detector import SentinelDetector
    from .neutralizer import SentinelNeutralizer
    from .pipeline import ProcessedChunk, SentinelPipeline
except ImportError:
    pass

__all__ = [
    "MultiLangDetector",
    "ZeroShotDetector",
    "ContextAwareNeutralizer",
    "DetectionExplainer",
    "AdversarialTester",
    "SentinelDetector",
    "SentinelNeutralizer",
    "SentinelPipeline",
    "ProcessedChunk",
]
