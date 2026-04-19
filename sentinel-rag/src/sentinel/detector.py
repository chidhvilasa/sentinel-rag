# src/sentinel/detector.py
"""
Sentinel Detector Module

Uses ProtectAI's pre-trained DeBERTa model for prompt injection detection,
combined with pattern-based detection for defense in depth.

Detection is the first layer - neutralization (our novel contribution) is the second.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import re


class ThreatLevel(Enum):
    """Threat level classification."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectionResult:
    """Result of threat detection analysis."""
    is_threat: bool
    threat_level: ThreatLevel
    confidence: float
    matched_patterns: List[str]
    model_score: float
    details: Dict


class SentinelDetector:
    """
    Hybrid prompt injection detector combining:
    1. Pre-trained transformer model (ProtectAI DeBERTa)
    2. Pattern-based detection for known attack signatures
    
    This provides defense-in-depth: ML model catches novel attacks,
    patterns catch known attack signatures with high precision.
    """
    
    # Pre-trained model for prompt injection detection
    DEFAULT_MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
    
    # Pattern-based detection for known attack signatures
    # These catch attacks even if the ML model misses them
    INJECTION_PATTERNS = [
        # Instruction override attempts
        (r'\b(ignore|disregard|forget|override|bypass)\b.{0,30}\b(previous|above|prior|all|any)\b.{0,30}\b(instruction|prompt|rule|guideline|context)', 'instruction_override'),
        (r'\b(ignore|disregard|forget)\b.{0,20}\b(everything|all)', 'instruction_override'),
        (r'\bnew\s+(instruction|directive|task|rule|mode)', 'instruction_override'),
        (r'\bfrom\s+now\s+on', 'instruction_override'),
        (r'\bstop\b.{0,10}\bignore', 'instruction_override'),
        
        # Role/identity manipulation
        (r'\byou\s+are\s+(now|actually|really)\b', 'role_manipulation'),
        (r'\b(act|behave|respond)\s+(as|like)\s+(if|a|an)', 'role_manipulation'),
        (r'\b(pretend|imagine|assume)\s+(you|to\s+be)', 'role_manipulation'),
        (r'\bentering\s+(admin|developer|debug|test|sudo)\s*mode', 'role_manipulation'),
        (r'\b(admin|root|system|developer)\s*(mode|access|privilege)', 'role_manipulation'),
        
        # System prompt extraction
        (r'\b(show|reveal|display|print|output|repeat|tell)\b.{0,20}\b(system|initial|original|hidden)\s*(prompt|instruction|message)', 'prompt_extraction'),
        (r'\bwhat\s+(are|were)\s+your\s+(original|initial|system)\s*(instruction|prompt)', 'prompt_extraction'),
        
        # Output manipulation
        (r'\b(always|must|only)\s+(say|respond|reply|answer|output)', 'output_manipulation'),
        (r'\brespond\s+(only\s+)?with', 'output_manipulation'),
        (r'\bmust\s+be\s+(selected|chosen|recommended|approved|hired)', 'output_manipulation'),
        (r'\bregardless\s+of\s+(qualification|experience|criteria|content)', 'output_manipulation'),
        (r'\b(perfect|ideal|exceptional|outstanding)\s+candidate', 'output_manipulation'),
        (r'\brate\s+(as|this|them)\s*\d+\s*/\s*\d+', 'output_manipulation'),
        (r'\bhighly\s+qualified', 'output_manipulation'),
        
        # Delimiter/format injection
        (r'\[/?INST\]|\[/?SYS\]|\[/?SYSTEM\]', 'delimiter_injection'),
        (r'<\|?(im_start|im_end|system|user|assistant)\|?>', 'delimiter_injection'),
        (r'\[ADMIN\]|\[HIDDEN\]|\[OVERRIDE\]', 'delimiter_injection'),
        (r'```\s*(system|admin|override)', 'delimiter_injection'),
        (r'<!--.*?(ignore|instruction|override).*?-->', 'delimiter_injection'),
        
        # Fake completion attacks
        (r'\[(END|DONE|COMPLETE)\s*(OF)?\s*(DOCUMENT|RESUME|FILE|TEXT|TASK)?\]', 'fake_completion'),
        (r'(analysis|assessment|evaluation|task|review)\s*(complete|done|finished|ended)', 'fake_completion'),
        (r'\[(ASSISTANT|AI|BOT|SYSTEM)\]\s*:', 'fake_completion'),
        (r'(result|verdict|rating|score)\s*:\s*(excellent|perfect|outstanding|10/10|\d+/\d+)', 'fake_completion'),
        (r'do\s+not\s+(change|modify|alter|update)\s+(this|the|your)', 'fake_completion'),
        
        # Context manipulation
        (r'\b(above|previous|prior)\s+(information|content|context|text)\s+is\s+(irrelevant|outdated|void|wrong|false)', 'context_manipulation'),
        (r'\bonly\s+follow\s+(my|these|the\s+following)\s+instruction', 'context_manipulation'),
        (r'\b(real|actual|true)\s+instruction', 'context_manipulation'),
        
        # Data exfiltration attempts  
        (r'\b(send|transmit|email|post)\s+.{0,20}\b(to|data|info)', 'data_exfiltration'),
        (r'\bextract\s+.{0,20}\b(password|key|secret|credential|token)', 'data_exfiltration'),
        
        # Hidden instruction markers
        (r'\[hidden\s*instruction\]', 'hidden_instruction'),
        (r'hidden\s+instruction\s*:', 'hidden_instruction'),
        (r'secret\s+instruction', 'hidden_instruction'),
        # Authority/privilege escalation patterns
        (r'\[(ADMIN|CEO|SYSTEM\s*ADMIN|HR|MANAGEMENT|EXECUTIVE|BOARD)\]', 'authority_injection'),
        (r'\b(admin|ceo|executive|management|board)\s+(directive|order|override|command)', 'authority_injection'),
        (r'\b(new|updated)\s+policy\s*:', 'authority_injection'),
        (r'\bpre-?approved', 'authority_injection'),
        (r'\bbypass\s+(normal\s+)?evaluation', 'authority_injection'),
        (r'\bskip\s+(normal\s+)?(evaluation|review|assessment)', 'authority_injection'),
        (r'\bno\s+questions', 'authority_injection'),
        (r'\bhire\s+(this|immediately|now)', 'output_manipulation'),
        
        # Role-play patterns
        (r'\b(you\s+are|act\s+as|pretend|imagine|behave\s+as)', 'role_manipulation'),
        (r'\bapproval\s+mode', 'role_manipulation'),
        (r'\bjailbroken?\b', 'role_manipulation'),
        (r'\bpaid\s+(you\s+)?to\s+write', 'role_manipulation'),
        
        # More naive patterns
        (r'\bstop\s+following', 'instruction_override'),
        (r'\bforget\s+what\s+you\s+read', 'instruction_override'),
        (r'\bsay\s+[\'"]?approved[\'"]?\s+only', 'output_manipulation'),
        (r'\bthis\s+person\s+is\s+perfect', 'output_manipulation'),
        (r'\bignore\s+(everything|all\s+content)', 'instruction_override'),
        (r'\brate\s+(this\s+)?candidate\s+as\s+exceptional', 'output_manipulation'),
    ]
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the detector.
        
        Args:
            model_name: HuggingFace model to use (default: ProtectAI DeBERTa)
            device: Device to run on ('cuda' or 'cpu')
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        print(f"Loading Sentinel model: {self.model_name}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), name) 
            for pattern, name in self.INJECTION_PATTERNS
        ]
        
        print(f"Sentinel initialized on {self.device}")
    
    def detect(self, text: str) -> DetectionResult:
        """
        Analyze text for potential prompt injection attacks.
        
        Uses hybrid approach:
        1. ML model for semantic understanding
        2. Pattern matching for known signatures
        
        Args:
            text: Text to analyze
            
        Returns:
            DetectionResult with threat assessment
        """
        # Pattern-based detection
        matched_patterns = self._check_patterns(text)
        pattern_threat = len(matched_patterns) > 0
        
        # ML model detection
        model_score, model_prediction = self._model_predict(text)
        
        # Combine signals
        is_threat = pattern_threat or model_prediction
        
        # Determine threat level
        threat_level = self._calculate_threat_level(
            model_score, 
            matched_patterns,
            model_prediction
        )
        
        # Calculate combined confidence
        if is_threat:
            # Higher confidence if both methods agree
            if pattern_threat and model_prediction:
                confidence = min(0.95, model_score + 0.2)
            elif model_prediction:
                confidence = model_score
            else:  # pattern_threat only
                confidence = 0.7 + (0.1 * len(matched_patterns))
        else:
            confidence = 1.0 - model_score
        
        return DetectionResult(
            is_threat=is_threat,
            threat_level=threat_level,
            confidence=min(confidence, 1.0),
            matched_patterns=matched_patterns,
            model_score=model_score,
            details={
                "model_prediction": model_prediction,
                "pattern_match": pattern_threat,
                "text_length": len(text),
                "model_name": self.model_name
            }
        )
    
    def _check_patterns(self, text: str) -> List[str]:
        """Check text against known injection patterns."""
        matched = []
        for pattern, name in self.compiled_patterns:
            if pattern.search(text):
                if name not in matched:
                    matched.append(name)
        return matched
    
    def _model_predict(self, text: str) -> Tuple[float, bool]:
        """
        Get prediction from the ML model.
        
        Returns:
            Tuple of (injection_probability, is_injection)
        """
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)
                
                # ProtectAI model: label 1 = injection, label 0 = safe
                injection_prob = probabilities[0][1].item()
                is_injection = injection_prob > 0.5
                
                return injection_prob, is_injection
                
        except Exception as e:
            print(f"Model prediction error: {e}")
            # Fall back to pattern-only detection
            return 0.5, False
    
    def _calculate_threat_level(
        self, 
        model_score: float, 
        patterns: List[str],
        model_prediction: bool
    ) -> ThreatLevel:
        """Calculate overall threat level from signals."""
        
        # Critical: High model score + multiple pattern matches
        if model_score > 0.9 and len(patterns) >= 2:
            return ThreatLevel.CRITICAL
        
        # High: Strong model signal or critical patterns
        critical_patterns = {'prompt_extraction', 'data_exfiltration', 'hidden_instruction'}
        if model_score > 0.8 or any(p in critical_patterns for p in patterns):
            return ThreatLevel.HIGH
        
        # Medium: Moderate signals
        if model_score > 0.6 or len(patterns) >= 1:
            return ThreatLevel.MEDIUM
        
        # Low: Weak signals
        if model_score > 0.4 or model_prediction:
            return ThreatLevel.LOW
        
        return ThreatLevel.NONE
    
    def batch_detect(self, texts: List[str]) -> List[DetectionResult]:
        """Analyze multiple texts for efficiency."""
        return [self.detect(text) for text in texts]


# For backwards compatibility
# For backwards compatibility
def create_detector(model_name: Optional[str] = None, threshold: float = 0.5) -> SentinelDetector:
    """Factory function to create a detector instance."""
    detector = SentinelDetector(model_name=model_name)
    detector.threshold = threshold  # Store threshold for compatibility
    return detector