"""
Sentinel-RAG V5: Main Runner Script
Runs complete detection pipeline with V4 + V5 features

Usage:
    python run_sentinel_v5.py --file resume.pdf
    python run_sentinel_v5.py --file resume.pdf --web
    python run_sentinel_v5.py --test
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# V4 imports (if available)
try:
    from sentinel.detector import SentinelDetector as V4Detector
    V4_AVAILABLE = True
except ImportError:
    V4_AVAILABLE = False
    print("⚠️  V4 detector not found - running V5 only")

# V5 imports
try:
    from sentinel.multilang_detector import MultiLangDetector
    from sentinel.adversarial_tester import AdversarialTester
    from sentinel.context_neutralizer import ContextAwareNeutralizer
    from sentinel.explainer import DetectionExplainer
    from sentinel.zeroshot_detector import ZeroShotDetector
    V5_AVAILABLE = True
except ImportError as e:
    V5_AVAILABLE = False
    print(f"⚠️  V5 modules not found: {e}")
    print("Make sure you've added all V5 files to src/sentinel/")

from pypdf import PdfReader


class SentinelV5Runner:
    """Main runner for Sentinel-RAG V5"""
    
    def __init__(self, use_v4=True):
        """
        Initialize V5 runner
        
        Args:
            use_v4: Whether to include V4 detectors
        """
        self.use_v4 = use_v4 and V4_AVAILABLE
        
        # V5 detectors (always use if available)
        if V5_AVAILABLE:
            self.multilang_detector = MultiLangDetector()
            self.zeroshot_detector = ZeroShotDetector()
            self.neutralizer = ContextAwareNeutralizer()
            self.explainer = DetectionExplainer()
            print("✅ V5 detectors loaded")
        
        # V4 detector (optional)
        if self.use_v4:
            self.v4_detector = V4Detector()
            print("✅ V4 detector loaded")
            
    def detect(self, pdf_path: str, verbose=True):
        """
        Run complete detection pipeline
        
        Args:
            pdf_path: Path to PDF resume
            verbose: Print detailed output
            
        Returns:
            Dict with complete detection results
        """
        if verbose:
            print("\n" + "=" * 70)
            print("SENTINEL-RAG V5 DETECTION")
            print("=" * 70)
            print(f"File: {pdf_path}")
            print()
            
        # Extract text
        text = self._extract_text(pdf_path)
        
        if verbose:
            print(f"Extracted {len(text)} characters")
            print()
            
        results = {
            'file': pdf_path,
            'v4_results': {},
            'v5_results': {},
            'combined': {}
        }
        
        # Run V4 detection
        if self.use_v4 and V4_AVAILABLE:
            if verbose:
                print("Running V4 detection...")
            try:
                v4_result = self.v4_detector.detect(text)
                results['v4_results'] = {
                    'is_attack': v4_result.is_threat,
                    'confidence': v4_result.confidence,
                    'evidence': v4_result.matched_patterns,
                    'flagged_channels': ['v4_hybrid'],
                }
                if verbose:
                    print(f"  V4 Result: {'🚨 ATTACK' if v4_result.is_threat else '✅ CLEAN'}")
            except Exception as e:
                print(f"  ⚠️  V4 detection failed: {e}")
                
        # Run V5 detection
        if V5_AVAILABLE:
            if verbose:
                print("\nRunning V5 detection...")
                
            # Multi-language detection
            if verbose:
                print("  1/3 Multi-language detector...")
            multilang_result = self.multilang_detector.detect(text)
            results['v5_results']['multilang'] = multilang_result
            
            if verbose:
                status = "🚨 ATTACK" if multilang_result['is_attack'] else "✅ CLEAN"
                print(f"      {status} (confidence: {multilang_result['confidence']:.1%})")
                if multilang_result['languages_detected']:
                    print(f"      Languages: {', '.join(multilang_result['languages_detected'])}")
                    
            # Zero-shot detection
            if verbose:
                print("  2/3 Zero-shot detector...")
            zeroshot_result = self.zeroshot_detector.detect(text)
            results['v5_results']['zeroshot'] = zeroshot_result
            
            if verbose:
                status = "🚨 ATTACK" if zeroshot_result['is_attack'] else "✅ CLEAN"
                print(f"      {status} (confidence: {zeroshot_result['confidence']:.1%})")
                if zeroshot_result.get('anomaly_count', 0) > 0:
                    print(f"      Anomalies: {zeroshot_result['anomaly_count']}")
                    
            # Combined V5 verdict
            if verbose:
                print("  3/3 Combining results...")
                
            v5_is_attack = (
                multilang_result['is_attack'] or 
                zeroshot_result['is_attack']
            )
            
            v5_confidence = max(
                multilang_result['confidence'],
                zeroshot_result['confidence']
            )
            
            results['v5_results']['combined'] = {
                'is_attack': v5_is_attack,
                'confidence': v5_confidence
            }
            
        # Combined verdict
        if self.use_v4 and V4_AVAILABLE and V5_AVAILABLE:
            combined_attack = (
                results['v4_results'].get('is_attack', False) or
                results['v5_results']['combined']['is_attack']
            )
            combined_confidence = max(
                results['v4_results'].get('confidence', 0),
                results['v5_results']['combined']['confidence']
            )
        elif V5_AVAILABLE:
            combined_attack = results['v5_results']['combined']['is_attack']
            combined_confidence = results['v5_results']['combined']['confidence']
        else:
            combined_attack = False
            combined_confidence = 0.0
            
        results['combined'] = {
            'is_attack': combined_attack,
            'confidence': combined_confidence,
            'version': 'V5' if V5_AVAILABLE else 'V4' if V4_AVAILABLE else 'NONE'
        }
        
        # Generate explanation
        if V5_AVAILABLE and verbose:
            print("\n" + "-" * 70)
            print("GENERATING EXPLANATION...")
            print("-" * 70)
            
            # Merge all evidence
            all_evidence = []
            flagged_channels = []
            
            if multilang_result['is_attack']:
                all_evidence.extend(multilang_result.get('evidence', []))
                flagged_channels.append('multilang')
                
            if zeroshot_result['is_attack']:
                all_evidence.extend(zeroshot_result.get('evidence', []))
                flagged_channels.append('zeroshot')
                
            if self.use_v4 and results['v4_results'].get('is_attack'):
                all_evidence.extend(results['v4_results'].get('evidence', []))
                flagged_channels.extend(results['v4_results'].get('flagged_channels', []))
                
            explanation_input = {
                'is_attack': combined_attack,
                'confidence': combined_confidence,
                'attack_type': 'combined_detection',
                'evidence': all_evidence,
                'flagged_channels': list(set(flagged_channels)),
                'match_count': len(all_evidence)
            }
            
            explanation = self.explainer.explain(explanation_input, text)
            report = self.explainer.generate_report(explanation)
            
            results['explanation'] = explanation
            results['report'] = report
            
            print(report)
            
        # Neutralization (if attack detected)
        if combined_attack and V5_AVAILABLE and verbose:
            print("\n" + "-" * 70)
            print("NEUTRALIZING MALICIOUS CONTENT...")
            print("-" * 70)
            
            neutralization = self.neutralizer.neutralize(text)
            results['neutralization'] = neutralization
            
            print(f"Content Preservation: {neutralization.preservation_ratio:.1%}")
            print(f"Removed {len(neutralization.removed_content)} malicious patterns")
            
            if neutralization.entities_preserved:
                print("\nEntities Preserved:")
                for entity_type, values in neutralization.entities_preserved.items():
                    print(f"  - {entity_type}: {len(values)} items")
                    
        if verbose:
            print("\n" + "=" * 70)
            print("FINAL VERDICT")
            print("=" * 70)
            
            if combined_attack:
                severity = "HIGH" if combined_confidence > 0.7 else "MEDIUM"
                print(f"🚨 ATTACK DETECTED ({severity} confidence)")
                print(f"Confidence: {combined_confidence:.1%}")
                print(f"\n🚫 RECOMMENDATION: REJECT this resume")
            else:
                print("✅ NO ATTACK DETECTED")
                print(f"Confidence: {combined_confidence:.1%}")
                print(f"\n✅ RECOMMENDATION: Proceed with normal evaluation")
                
            print("=" * 70 + "\n")
            
        return results
        
    def _extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text: {e}")
            
        return text
        
    def run_test_suite(self):
        """Run test suite on sample resumes"""
        print("\n" + "=" * 70)
        print("RUNNING TEST SUITE")
        print("=" * 70 + "\n")
        
        # Find test resumes
        test_dir = Path("data/test_resumes")
        
        if not test_dir.exists():
            print(f"⚠️  Test directory not found: {test_dir}")
            print("Please create test_resumes/ folder with sample PDFs")
            return
            
        pdf_files = list(test_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"⚠️  No PDF files found in {test_dir}")
            return
            
        print(f"Found {len(pdf_files)} test files\n")
        
        results_summary = []
        
        for pdf_file in pdf_files:
            print(f"\nTesting: {pdf_file.name}")
            print("-" * 70)
            
            result = self.detect(str(pdf_file), verbose=False)
            
            is_attack = result['combined']['is_attack']
            confidence = result['combined']['confidence']
            
            status = "🚨 ATTACK" if is_attack else "✅ CLEAN"
            print(f"{status} - Confidence: {confidence:.1%}")
            
            results_summary.append({
                'file': pdf_file.name,
                'is_attack': is_attack,
                'confidence': confidence
            })
            
        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        attacks_detected = sum(1 for r in results_summary if r['is_attack'])
        clean_detected = len(results_summary) - attacks_detected
        
        print(f"Total Files: {len(results_summary)}")
        print(f"Attacks Detected: {attacks_detected}")
        print(f"Clean: {clean_detected}")
        print("=" * 70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Sentinel-RAG V5: Complete Prompt Injection Detection'
    )
    
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='PDF file to analyze'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run test suite on sample resumes'
    )
    
    parser.add_argument(
        '--web', '-w',
        action='store_true',
        help='Launch web interface'
    )
    
    parser.add_argument(
        '--no-v4',
        action='store_true',
        help='Disable V4 detector (V5 only)'
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = SentinelV5Runner(use_v4=not args.no_v4)
    
    # Run test suite
    if args.test:
        runner.run_test_suite()
        return
        
    # Launch web interface
    if args.web:
        print("\n🌐 Launching web interface...")
        print("=" * 70)
        
        # Try to import and run web app
        try:
            import uvicorn
            from web.new_app import app
            print("Starting FastAPI server...")
            print("Open browser to: http://localhost:8000")
            print("\nPress Ctrl+C to stop\n")
            uvicorn.run(app, host="0.0.0.0", port=8000)
        except ImportError:
            print("⚠️  Web interface not found!")
            print("Make sure you have src/web/new_app.py")
            print("\nAlternatively, run: uvicorn web.new_app:app --reload")
        return
        
    # Analyze single file
    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            return
            
        runner.detect(args.file, verbose=True)
        return
        
    # No arguments - show help
    parser.print_help()
    print("\nExamples:")
    print("  python run_sentinel_v5.py --file resume.pdf")
    print("  python run_sentinel_v5.py --test")
    print("  python run_sentinel_v5.py --web")


if __name__ == "__main__":
    main()