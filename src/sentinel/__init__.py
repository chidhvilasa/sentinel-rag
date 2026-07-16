# Sentinel V5 modules
from .multilang_detector import MultiLangDetector
from .zeroshot_detector import ZeroShotDetector
from .context_neutralizer import ContextAwareNeutralizer
from .explainer import DetectionExplainer
from .adversarial_tester import AdversarialTester

# V4 exports
try:
    from .detector import SentinelDetector
    from .neutralizer import SentinelNeutralizer
    from .pipeline import SentinelPipeline, ProcessedChunk
except ImportError:
    pass

__all__ = [
    'MultiLangDetector',
    'ZeroShotDetector',
    'ContextAwareNeutralizer',
    'DetectionExplainer',
    'AdversarialTester',
    'SentinelDetector',
    'SentinelNeutralizer',
    'SentinelPipeline',
    'ProcessedChunk',
]