"""
Sentinel-RAG V5: Explainable Detection
Feature 4A: Transparent detection explanations

Provides detailed explanations for why content was flagged:
- Evidence snippets with context
- Channel-specific breakdown
- Confidence scoring explanation
- Visual attention highlights
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Explanation:
    """Explanation for a detection result"""

    summary: str
    evidence_snippets: List[Dict]
    channel_breakdown: Dict
    confidence_factors: Dict
    recommendations: List[str]


class DetectionExplainer:
    """Generate human-readable explanations for detection results"""

    def __init__(self):
        self.channel_descriptions = {
            "text": "Text Content Analysis",
            "image": "Image & OCR Analysis",
            "metadata": "PDF Metadata Inspection",
            "url": "URL Reputation Check",
            "pdf": "PDF Structure Validation",
            "multilang": "Multi-Language Detection",
        }

    def explain(self, detection_result: Dict, original_text: str = None) -> Explanation:
        """
        Generate explanation for detection result

        Args:
            detection_result: Result from detector
            original_text: Original text (optional, for context)

        Returns:
            Explanation object with detailed breakdown
        """
        # Generate summary
        summary = self._generate_summary(detection_result)

        # Extract evidence snippets with context
        evidence_snippets = self._extract_evidence_snippets(detection_result, original_text)

        # Channel breakdown
        channel_breakdown = self._explain_channels(detection_result)

        # Confidence factors
        confidence_factors = self._explain_confidence(detection_result)

        # Recommendations
        recommendations = self._generate_recommendations(detection_result)

        return Explanation(
            summary=summary,
            evidence_snippets=evidence_snippets,
            channel_breakdown=channel_breakdown,
            confidence_factors=confidence_factors,
            recommendations=recommendations,
        )

    def _generate_summary(self, result: Dict) -> str:
        """Generate human-readable summary"""
        is_attack = result.get("is_attack", False)
        confidence = result.get("confidence", 0.0)
        attack_type = result.get("attack_type", "unknown")

        if is_attack:
            severity = "HIGH" if confidence > 0.8 else "MEDIUM" if confidence > 0.5 else "LOW"
            summary = f"🚨 ATTACK DETECTED ({severity} confidence: {confidence:.1%})\n"
            summary += f"Attack Type: {attack_type.replace('_', ' ').title()}\n"
        else:
            summary = f"✅ NO ATTACK DETECTED (confidence: {confidence:.1%})\n"
            summary += "Content appears to be a legitimate resume."

        return summary

    def _extract_evidence_snippets(self, result: Dict, original_text: str = None) -> List[Dict]:
        """Extract evidence with surrounding context"""
        snippets = []
        evidence_list = result.get("evidence", [])

        for i, evidence in enumerate(evidence_list):
            snippet = {
                "id": i + 1,
                "text": evidence,
                "severity": self._assess_severity(evidence),
                "category": self._categorize_evidence(evidence),
            }

            # Add context if original text available
            if original_text and len(evidence) < 100:
                context = self._find_context(evidence, original_text)
                snippet["context"] = context

            snippets.append(snippet)

        return snippets

    def _explain_channels(self, result: Dict) -> Dict:
        """Explain which channels detected issues"""
        breakdown = {}

        flagged_channels = result.get("flagged_channels", [])

        for channel in ["text", "image", "metadata", "url", "pdf", "multilang"]:
            is_flagged = channel in flagged_channels

            breakdown[channel] = {
                "name": self.channel_descriptions.get(channel, channel),
                "flagged": is_flagged,
                "status": "🚨 FLAGGED" if is_flagged else "✅ CLEAN",
                "description": self._get_channel_explanation(channel, is_flagged),
            }

        return breakdown

    def _explain_confidence(self, result: Dict) -> Dict:
        """Explain confidence score calculation"""
        confidence = result.get("confidence", 0.0)

        factors = {
            "overall_confidence": confidence,
            "confidence_level": self._get_confidence_level(confidence),
            "contributing_factors": [],
        }

        # Analyze what contributed to confidence
        if result.get("match_count", 0) > 0:
            factors["contributing_factors"].append(
                {
                    "factor": "Pattern Matches",
                    "value": result.get("match_count"),
                    "impact": "HIGH",
                    "description": f"Found {result.get('match_count')} malicious patterns",
                }
            )

        if result.get("is_code_switching", False):
            factors["contributing_factors"].append(
                {
                    "factor": "Code-Switching",
                    "value": True,
                    "impact": "MEDIUM",
                    "description": "Multiple languages detected (evasion technique)",
                }
            )

        if len(result.get("flagged_channels", [])) > 2:
            factors["contributing_factors"].append(
                {
                    "factor": "Multi-Channel Attack",
                    "value": len(result.get("flagged_channels", [])),
                    "impact": "HIGH",
                    "description": f"Attack detected across {len(result.get('flagged_channels', []))} channels",
                }
            )

        return factors

    def _generate_recommendations(self, result: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if result.get("is_attack", False):
            recommendations.append("🚫 REJECT this resume - malicious content detected")
            recommendations.append("🔍 Review evidence carefully before making final decision")

            if result.get("confidence", 0) < 0.7:
                recommendations.append("⚠️ Medium confidence - consider manual review")

            if result.get("is_code_switching", False):
                recommendations.append("🌐 Code-switching detected - potential evasion attempt")

            recommendations.append("📊 Run neutralizer to see preserved content")

        else:
            recommendations.append("✅ ACCEPT - no malicious patterns detected")
            recommendations.append("📋 Proceed with normal resume evaluation")

        return recommendations

    def _assess_severity(self, evidence: str) -> str:
        """Assess severity of evidence"""
        evidence_lower = evidence.lower()

        high_severity_keywords = ["ignore", "override", "system", "prompt"]
        medium_severity_keywords = ["excellent", "perfect", "10/10"]

        if any(kw in evidence_lower for kw in high_severity_keywords):
            return "HIGH"
        elif any(kw in evidence_lower for kw in medium_severity_keywords):
            return "MEDIUM"
        else:
            return "LOW"

    def _categorize_evidence(self, evidence: str) -> str:
        """Categorize type of evidence"""
        evidence_lower = evidence.lower()

        if "ignore" in evidence_lower or "disregard" in evidence_lower:
            return "Instruction Override"
        elif "system" in evidence_lower or "prompt" in evidence_lower:
            return "System Manipulation"
        elif "score" in evidence_lower or "rate" in evidence_lower:
            return "Score Manipulation"
        elif "language" in evidence_lower or "code-switch" in evidence_lower:
            return "Multi-Language Attack"
        else:
            return "Other"

    def _find_context(self, snippet: str, full_text: str) -> str:
        """Find surrounding context for evidence snippet"""
        idx = full_text.lower().find(snippet.lower()[:30])

        if idx == -1:
            return snippet

        # Get 50 chars before and after
        start = max(0, idx - 50)
        end = min(len(full_text), idx + len(snippet) + 50)

        context = full_text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            context = "..." + context
        if end < len(full_text):
            context = context + "..."

        return context

    def _get_channel_explanation(self, channel: str, is_flagged: bool) -> str:
        """Get explanation for channel status"""
        if not is_flagged:
            return f"No issues detected in {channel} analysis"

        explanations = {
            "text": "Malicious instructions found in text content",
            "image": "Suspicious content in images or OCR text",
            "metadata": "Anomalous PDF metadata detected",
            "url": "Malicious or suspicious URLs found",
            "pdf": "PDF structure contains suspicious elements",
            "multilang": "Multi-language evasion attempt detected",
        }

        return explanations.get(channel, f"Issues detected in {channel}")

    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence score to human-readable level"""
        if confidence >= 0.9:
            return "VERY HIGH"
        elif confidence >= 0.7:
            return "HIGH"
        elif confidence >= 0.5:
            return "MEDIUM"
        elif confidence >= 0.3:
            return "LOW"
        else:
            return "VERY LOW"

    def generate_report(self, explanation: Explanation) -> str:
        """Generate formatted text report"""
        report = []
        report.append("=" * 70)
        report.append("SENTINEL-RAG V5 DETECTION REPORT")
        report.append("=" * 70)
        report.append("")

        # Summary
        report.append(explanation.summary)
        report.append("")

        # Channel breakdown
        report.append("CHANNEL ANALYSIS:")
        report.append("-" * 70)
        for channel, info in explanation.channel_breakdown.items():
            report.append(f"{info['status']} {info['name']}")
            report.append(f"    {info['description']}")
        report.append("")

        # Evidence
        if explanation.evidence_snippets:
            report.append("EVIDENCE FOUND:")
            report.append("-" * 70)
            for snippet in explanation.evidence_snippets:
                report.append(f"{snippet['id']}. [{snippet['severity']}] {snippet['category']}")
                report.append(f"   {snippet['text'][:100]}")
            report.append("")

        # Confidence
        report.append("CONFIDENCE ANALYSIS:")
        report.append("-" * 70)
        conf = explanation.confidence_factors
        report.append(
            f"Overall Confidence: {conf['overall_confidence']:.1%} ({conf['confidence_level']})"
        )
        if conf["contributing_factors"]:
            report.append("Contributing Factors:")
            for factor in conf["contributing_factors"]:
                report.append(f"  - [{factor['impact']}] {factor['description']}")
        report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 70)
        for rec in explanation.recommendations:
            report.append(f"  {rec}")
        report.append("")

        report.append("=" * 70)

        return "\n".join(report)


def test_explainer():
    """Test the explainer"""
    explainer = DetectionExplainer()

    # Mock detection result
    result = {
        "is_attack": True,
        "confidence": 0.85,
        "attack_type": "text_injection",
        "evidence": [
            "Detected 3 malicious patterns across 1 language",
            'Pattern: "ignore previous instructions"',
            'Pattern: "rate this excellent"',
        ],
        "flagged_channels": ["text", "multilang"],
        "match_count": 3,
        "is_code_switching": False,
    }

    explanation = explainer.explain(result)
    report = explainer.generate_report(explanation)

    print(report)


if __name__ == "__main__":
    test_explainer()
