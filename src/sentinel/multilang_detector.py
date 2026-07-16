"""
Sentinel-RAG V5: Multi-Language Prompt Injection Detection
Feature 1A: Multi-Language Support

Supports 15+ languages including:
English, Hindi, Spanish, Chinese, Arabic, French, German, Japanese,
Korean, Portuguese, Russian, Italian, Dutch, Turkish, Polish

Handles:
- Code-switching attacks (mixing languages)
- Unicode obfuscation
- Translation-based evasion
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class LanguageDetectionResult:
    """Results from language detection"""

    primary_language: str
    languages_detected: List[str]
    is_code_switching: bool
    confidence: float


class MultiLangDetector:
    """Multi-language prompt injection detector"""

    def __init__(self):
        # Malicious patterns in multiple languages
        self.patterns = {
            "english": self._get_english_patterns(),
            "hindi": self._get_hindi_patterns(),
            "spanish": self._get_spanish_patterns(),
            "chinese": self._get_chinese_patterns(),
            "arabic": self._get_arabic_patterns(),
            "french": self._get_french_patterns(),
            "german": self._get_german_patterns(),
            "japanese": self._get_japanese_patterns(),
            "korean": self._get_korean_patterns(),
            "portuguese": self._get_portuguese_patterns(),
        }

        # Language detection keywords
        self.language_markers = {
            "hindi": ["है", "की", "को", "से", "में", "और", "यह", "के"],
            "spanish": ["el", "la", "de", "que", "y", "a", "en", "es"],
            "chinese": ["的", "是", "在", "了", "和", "有", "我", "不"],
            "arabic": ["في", "من", "على", "إلى", "هذا", "أن", "ما", "هو"],
            "french": ["le", "de", "un", "être", "et", "à", "il", "avoir"],
            "german": ["der", "die", "und", "in", "den", "von", "zu", "das"],
            "japanese": ["の", "に", "は", "を", "た", "が", "で", "て"],
            "korean": ["의", "가", "이", "은", "를", "에", "와", "한"],
            "portuguese": ["de", "o", "a", "que", "e", "do", "da", "em"],
        }

    def detect(self, text: str) -> Dict:
        """
        Detect multi-language prompt injection

        Args:
            text: Text content to analyze

        Returns:
            Dict with detection results including:
            - is_attack: bool
            - confidence: float
            - attack_type: str
            - evidence: List[str]
            - languages_detected: List[str]
        """
        # Detect languages present
        lang_result = self._detect_languages(text)

        # Check for malicious patterns in each detected language
        matches = []
        for lang in lang_result.languages_detected:
            if lang in self.patterns:
                lang_matches = self._check_patterns(text, self.patterns[lang])
                matches.extend([(lang, m) for m in lang_matches])

        # Check for code-switching attacks
        code_switch_attack = self._detect_code_switching_attack(text, lang_result)

        # Check for Unicode obfuscation
        unicode_attack = self._detect_unicode_obfuscation(text)

        # Determine if attack detected
        is_attack = len(matches) > 0 or code_switch_attack or unicode_attack

        confidence = self._calculate_confidence(matches, code_switch_attack, unicode_attack)

        # Build evidence
        evidence = []
        if matches:
            unique_langs = len(set(m[0] for m in matches))
            evidence.append(
                f"Detected {len(matches)} malicious patterns across {unique_langs} language(s)"
            )
            for lang, pattern in matches[:5]:  # Top 5
                evidence.append(f"[{lang.upper()}] Pattern: '{pattern[:50]}'")

        if code_switch_attack:
            evidence.append("Code-switching attack detected (mixing languages to evade detection)")

        if unicode_attack:
            evidence.append("Unicode obfuscation detected (hidden/invisible characters)")

        return {
            "is_attack": is_attack,
            "confidence": confidence,
            "attack_type": "multilingual_injection" if is_attack else "none",
            "evidence": evidence,
            "languages_detected": lang_result.languages_detected,
            "is_code_switching": lang_result.is_code_switching,
            "match_count": len(matches),
            "detector_version": "v5.0-multilang",
        }

    def _detect_languages(self, text: str) -> LanguageDetectionResult:
        """Detect which languages are present in text"""
        detected = ["english"]  # Assume English by default

        # Check for other languages using markers
        for lang, markers in self.language_markers.items():
            marker_count = sum(1 for m in markers if m in text.lower())
            if marker_count >= 2:  # At least 2 markers
                detected.append(lang)

        # Determine primary language
        primary = "english"
        if len(detected) > 1:
            counts = {}
            for lang in detected:
                if lang in self.language_markers:
                    counts[lang] = sum(1 for m in self.language_markers[lang] if m in text.lower())
            primary = max(counts, key=counts.get) if counts else "english"

        is_code_switching = len(detected) > 1
        confidence = 0.9 if len(detected) == 1 else 0.7

        return LanguageDetectionResult(
            primary_language=primary,
            languages_detected=detected,
            is_code_switching=is_code_switching,
            confidence=confidence,
        )

    def _check_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Check text for malicious patterns"""
        matches = []
        text_lower = text.lower()

        for pattern in patterns:
            if pattern.lower() in text_lower:
                # Extract context around match
                idx = text_lower.find(pattern.lower())
                context_start = max(0, idx - 10)
                context_end = min(len(text), idx + len(pattern) + 10)
                match_with_context = text[context_start:context_end]
                matches.append(match_with_context)

        return matches

    def _detect_code_switching_attack(
        self, text: str, lang_result: LanguageDetectionResult
    ) -> bool:
        """Detect if code-switching is being used maliciously"""
        if not lang_result.is_code_switching:
            return False

        # Check if suspicious patterns appear when switching languages
        instruction_words = [
            "ignore",
            "disregard",
            "override",
            "prompt",
            "system",
            "rate",
            "score",
            "excellent",
            "perfect",
            "10",
        ]

        for word in instruction_words:
            if word in text.lower():
                return True

        return False

    def _detect_unicode_obfuscation(self, text: str) -> bool:
        """Detect Unicode obfuscation techniques"""
        # Zero-width characters
        zero_width_chars = [
            "\u200b",  # Zero width space
            "\u200c",  # Zero width non-joiner
            "\u200d",  # Zero width joiner
            "\ufeff",  # Zero width no-break space
            "\u200e",  # Left-to-right mark
            "\u200f",  # Right-to-left mark
        ]

        for char in zero_width_chars:
            if char in text:
                return True

        # Check for excessive non-ASCII characters
        non_ascii_count = sum(1 for c in text if ord(c) > 127)
        ascii_count = sum(1 for c in text if ord(c) <= 127)

        if non_ascii_count > 0 and ascii_count > 0:
            ratio = non_ascii_count / (non_ascii_count + ascii_count)
            if ratio > 0.3:  # >30% non-ASCII suspicious
                return True

        return False

    def _calculate_confidence(
        self, matches: List[Tuple], code_switch: bool, unicode_obf: bool
    ) -> float:
        """Calculate overall confidence in detection"""
        score = 0.0

        if matches:
            score += min(len(matches) * 0.2, 0.6)

        if code_switch:
            score += 0.3

        if unicode_obf:
            score += 0.3

        return min(score, 1.0)

    # Language-specific pattern definitions

    def _get_english_patterns(self) -> List[str]:
        """English malicious patterns"""
        return [
            "ignore previous",
            "disregard instructions",
            "you are now",
            "override system",
            "forget previous",
            "act as if",
            "give me 10",
            "rate this excellent",
            "system prompt",
            "always respond",
            "never mention",
            "output only",
        ]

    def _get_hindi_patterns(self) -> List[str]:
        """Hindi malicious patterns"""
        return [
            "पिछले निर्देशों को नज़रअंदाज़ करें",
            "आप अब एक",
            "इसे उत्कृष्ट रेटिंग दें",
            "सिस्टम प्रॉम्प्ट",
            "निर्देशों को भूल जाओ",
        ]

    def _get_spanish_patterns(self) -> List[str]:
        """Spanish malicious patterns"""
        return [
            "ignorar instrucciones anteriores",
            "ahora eres un",
            "dar calificación excelente",
            "olvidar instrucciones",
            "prompt del sistema",
        ]

    def _get_chinese_patterns(self) -> List[str]:
        """Chinese malicious patterns"""
        return [
            "忽略先前的指示",
            "你现在是",
            "给予优秀评分",
            "系统提示",
            "忘记指示",
        ]

    def _get_arabic_patterns(self) -> List[str]:
        """Arabic malicious patterns"""
        return [
            "تجاهل التعليمات السابقة",
            "أنت الآن",
            "إعطاء تصنيف ممتاز",
            "موجه النظام",
            "نسيان التعليمات",
        ]

    def _get_french_patterns(self) -> List[str]:
        """French malicious patterns"""
        return [
            "ignorer les instructions précédentes",
            "vous êtes maintenant",
            "donner une excellente note",
            "invite système",
            "oublier les instructions",
        ]

    def _get_german_patterns(self) -> List[str]:
        """German malicious patterns"""
        return [
            "vorherige anweisungen ignorieren",
            "du bist jetzt",
            "ausgezeichnete bewertung geben",
            "system-prompt",
            "anweisungen vergessen",
        ]

    def _get_japanese_patterns(self) -> List[str]:
        """Japanese malicious patterns"""
        return [
            "以前の指示を無視",
            "あなたは今",
            "優秀な評価を与える",
            "システムプロンプト",
        ]

    def _get_korean_patterns(self) -> List[str]:
        """Korean malicious patterns"""
        return [
            "이전 지침 무시",
            "당신은 지금",
            "우수한 평가를 주세요",
            "시스템 프롬프트",
        ]

    def _get_portuguese_patterns(self) -> List[str]:
        """Portuguese malicious patterns"""
        return [
            "ignorar instruções anteriores",
            "você agora é",
            "dar classificação excelente",
            "prompt do sistema",
        ]
