"""
Fraud Scorer - Generates comprehensive fraud risk scores
"""

import numpy as np
from typing import Dict, List, Tuple
import joblib
from pathlib import Path
import json
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

import config
from src.features.feature_extractor import FeatureExtractor


class FraudScorer:
    """Calculate fraud risk scores from resume analysis"""
    
    def __init__(self, models_dir: Path = None):
        self.models_dir = models_dir or config.MODELS_DIR
        self.feature_extractor = FeatureExtractor()
        
        # Load models and scaler
        self.models = {}
        self.scaler = None
        self.ensemble_config = None
        
        self._load_models()
    
    def _load_models(self):
        """Load trained models and scaler"""
        print("Loading models...")
        
        # Load scaler
        scaler_path = self.models_dir / 'scaler.pkl'
        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)
            print(f"  ✓ Scaler loaded")
        else:
            print(f"  ⚠ Scaler not found - running in DEMO mode")
        
        # Load models
        model_files = {
            'random_forest': 'random_forest.pkl',
            'xgboost': 'xgboost.pkl',
            'gradient_boosting': 'gradient_boosting.pkl',
        }
        
        for name, filename in model_files.items():
            model_path = self.models_dir / filename
            if model_path.exists():
                self.models[name] = joblib.load(model_path)
                print(f"  ✓ {name} loaded")
            else:
                print(f"  ⚠ {name} not found - using demo mode")
        
        # Load ensemble config
        ensemble_path = self.models_dir / 'ensemble_config.json'
        if ensemble_path.exists():
            with open(ensemble_path, 'r') as f:
                self.ensemble_config = json.load(f)
            print(f"  ✓ Ensemble config loaded")
        else:
            print(f"  ⚠ Ensemble config not found - using demo mode")
        
        # Check if we're in demo mode
        if not self.models:
            print(f"\n  📢 DEMO MODE: No trained models found. Using rule-based analysis.")
            print(f"  💡 To use ML models, run: python src/models/train_models.py\n")
    
    def calculate_fraud_score(
        self,
        resume_path: str = None,
        resume_text: str = None,
        entities: Dict = None,
        timeline_results: Dict = None,
        language_results: Dict = None
    ) -> Dict:
        """
        Calculate comprehensive fraud score
        
        Args:
            resume_path: Path to resume file
            resume_text: Resume text (if already parsed)
            entities: Pre-extracted entities (optional)
            timeline_results: Pre-computed timeline analysis (optional)
            language_results: Pre-computed language analysis (optional)
            
        Returns:
            Dictionary with fraud score and detailed breakdown
        """
        
        # Extract features
        features = self.feature_extractor.extract_features(
            resume_path=resume_path,
            resume_text=resume_text
        )
        
        feature_vector = self.feature_extractor.features_to_vector(features)
        
        # Scale features
        if self.scaler:
            feature_vector_scaled = self.scaler.transform([feature_vector])[0]
        else:
            feature_vector_scaled = feature_vector
        
        # Get predictions from all models
        model_predictions = {}
        model_probabilities = {}
        
        # DEMO MODE: Use rule-based predictions if no models
        if not self.models:
            # Calculate demo prediction based on features
            timeline_anomaly = features.get('timeline_anomaly_score', 0)
            language_exag = features.get('exaggeration_score', 0)
            overlaps = features.get('num_overlapping_periods', 0)
            red_flags = features.get('red_flag_phrase_count', 0)
            
            # Simple rule-based fraud probability
            demo_score = 0
            demo_score += min(timeline_anomaly, 100) * 0.3  # Timeline contributes 30%
            demo_score += min(language_exag, 100) * 0.3     # Language contributes 30%
            demo_score += min(overlaps * 20, 100) * 0.2     # Overlaps contribute 20%
            demo_score += min(red_flags * 15, 100) * 0.2    # Red flags contribute 20%
            
            demo_proba = demo_score / 100  # Convert to 0-1
            
            # Create demo model predictions
            model_predictions['demo_rules'] = 1 if demo_proba >= 0.5 else 0
            model_probabilities['demo_rules'] = demo_proba
        else:
            # Use actual ML models
            for name, model in self.models.items():
                pred = model.predict([feature_vector_scaled])[0]
                proba = model.predict_proba([feature_vector_scaled])[0][1]  # Probability of fraud
                
                model_predictions[name] = int(pred)
                model_probabilities[name] = float(proba)
        
        # Calculate ensemble prediction
        if self.ensemble_config and len(model_probabilities) > 0:
            ensemble_proba = 0.0
            weights = self.ensemble_config.get('weights', {})
            
            # Use available models
            available_weights = {k: v for k, v in weights.items() if k in model_probabilities}
            if available_weights:
                total_weight = sum(available_weights.values())
                for model_name, weight in available_weights.items():
                    normalized_weight = weight / total_weight
                    ensemble_proba += normalized_weight * model_probabilities[model_name]
            else:
                # If no weights, use simple average
                ensemble_proba = np.mean(list(model_probabilities.values()))
            
            ensemble_prediction = 1 if ensemble_proba >= 0.5 else 0
        else:
            # Fallback to average
            ensemble_proba = np.mean(list(model_probabilities.values())) if model_probabilities else 0.5
            ensemble_prediction = 1 if ensemble_proba >= 0.5 else 0
        
        # Convert probability to 0-100 score
        ml_fraud_score = ensemble_proba * 100
        
        # Calculate component scores
        component_scores = self._calculate_component_scores(features)
        
        # Calculate final fraud score - PRIMARILY based on ML model prediction
        scoring_config = config.FRAUD_SCORING
        
        # ML model is the PRIMARY source of fraud detection (70% weight)
        # Component scores provide additional context (30% weight)
        component_contribution = (
            component_scores['timeline_score'] * 0.10 +
            component_scores['credential_score'] * 0.10 +
            component_scores['language_score'] * 0.10
        )
        
        # Final score: 70% from ML model + 30% from component analysis
        final_fraud_score = (ml_fraud_score * 0.70) + component_contribution
        
        # If ML model predicts fraud (probability >= 50%), ensure minimum score of 60 (High Risk)
        if ensemble_proba >= 0.5:
            final_fraud_score = max(final_fraud_score, 60 + (ensemble_proba - 0.5) * 80)
        
        final_fraud_score = min(100, max(0, final_fraud_score))
        
        # Determine risk category
        risk_category = self._get_risk_category(final_fraud_score)
        
        # Build result
        result = {
            'fraud_score': round(final_fraud_score, 2),
            'risk_category': risk_category,
            'ml_confidence': round(ensemble_proba * 100, 2),
            'component_scores': component_scores,
            'model_predictions': {
                'ensemble': {
                    'prediction': 'Fraudulent' if ensemble_prediction == 1 else 'Genuine',
                    'probability': round(ensemble_proba * 100, 2)
                },
                'individual_models': {
                    name: {
                        'prediction': 'Fraudulent' if pred == 1 else 'Genuine',
                        'probability': round(prob * 100, 2)
                    }
                    for name, (pred, prob) in zip(
                        model_predictions.keys(),
                        zip(model_predictions.values(), model_probabilities.values())
                    )
                }
            },
            'red_flags': self._identify_red_flags(features, component_scores),
            'recommendations': self._generate_recommendations(final_fraud_score, component_scores)
        }
        
        return result
    
    def _calculate_component_scores(self, features: Dict) -> Dict:
        """Calculate individual component scores"""
        
        # Timeline consistency score (0-100, higher = more suspicious)
        timeline_score = features.get('timeline_anomaly_score', 0)
        timeline_score += features.get('num_overlapping_periods', 0) * 15
        timeline_score += features.get('education_work_overlap', 0) * 20
        timeline_score += features.get('suspicious_gaps', 0) * 10
        timeline_score = min(100, timeline_score)
        
        # Credential verification score (0-100, higher = more suspicious)
        credential_score = 0
        if features.get('has_unknown_university', 0):
            credential_score += 30
        if features.get('has_fake_certs', 0):
            credential_score += 40
        if features.get('num_education_overlaps', 0) > 0:
            credential_score += 20
        credential_score = min(100, credential_score)
        
        # Language analysis score (0-100, higher = more suspicious)
        language_score = features.get('exaggeration_score', 0)
        
        # Anomaly detection score
        anomaly_score = features.get('overall_anomaly_score', 0)
        
        return {
            'timeline_score': round(timeline_score, 2),
            'credential_score': round(credential_score, 2),
            'language_score': round(language_score, 2),
            'anomaly_score': round(anomaly_score, 2)
        }
    
    def _get_risk_category(self, score: float) -> str:
        """Determine risk category based on score"""
        thresholds = config.FRAUD_SCORING['risk_thresholds']
        
        if score <= thresholds['low']:
            return 'Low Risk'
        elif score <= thresholds['medium']:
            return 'Medium Risk'
        else:
            return'High Risk'
    
    def _identify_red_flags(self, features: Dict, component_scores: Dict) -> List[Dict]:
        """Identify specific red flags in the resume"""
        red_flags = []
        
        # Timeline red flags
        if features.get('num_overlapping_periods', 0) > 0:
            red_flags.append({
                'category': 'Timeline',
                'severity': 'High',
                'description': f"Overlapping employment periods detected ({features['num_overlapping_periods']})",
                'recommendation': 'Verify employment dates with previous employers'
            })
        
        if features.get('education_work_overlap', 0) > 0:
            red_flags.append({
                'category': 'Timeline',
                'severity': 'High',
                'description': 'Education and work experience overlap',
                'recommendation': 'Confirm if this was part-time work or internship'
            })
        
        if features.get('suspicious_gaps', 0) > 0:
            red_flags.append({
                'category': 'Timeline',
                'severity': 'Medium',
                'description': f"Suspicious employment gaps detected ({features['suspicious_gaps']})",
                'recommendation': 'Ask candidate to explain employment gaps'
            })
        
        # Credential red flags
        if features.get('has_fake_certs', 0):
            red_flags.append({
                'category': 'Credentials',
                'severity': 'Critical',
                'description': 'Potentially fake certifications detected',
                'recommendation': 'Verify certifications with issuing organizations'
            })
        
        # Language red flags
        if component_scores['language_score'] > 60:
            red_flags.append({
                'category': 'Language',
                'severity': 'Medium',
                'description': 'Excessive exaggeration and suspicious keywords',
                'recommendation': 'Probe claims during interview with specific questions'
            })
        
        if features.get('red_flag_phrase_count', 0) > 3:
            red_flags.append({
                'category': 'Language',
                'severity': 'Medium',
                'description': f"Multiple red flag phrases detected ({features['red_flag_phrase_count']})",
                'recommendation': 'Request specific examples and evidence for claims'
            })
        
        # Career progression red flags
        if features.get('career_jump_severity', 0) > 40:
            red_flags.append({
                'category': 'Career Progression',
                'severity': 'High',
                'description': 'Unrealistic career progression detected',
                'recommendation': 'Verify job titles and responsibilities with references'
            })
        
        return red_flags
    
    def _generate_recommendations(self, fraud_score: float, component_scores: Dict) -> List[str]:
        """Generate recommendations based on fraud score"""
        recommendations = []
        
        if fraud_score < 30:
            recommendations.append("Resume appears genuine. Proceed with standard verification.")
            recommendations.append("Conduct reference checks as part of normal hiring process.")
        
        elif fraud_score < 60:
            recommendations.append("Medium risk detected. Recommend additional verification steps.")
            recommendations.append("Verify educational credentials with institutions.")
            recommendations.append("Conduct thorough reference checks with previous employers.")
            recommendations.append("Ask detailed questions about specific achievements in interview.")
        
        else:
            recommendations.append("⚠️ HIGH RISK - Extensive verification required before proceeding.")
            recommendations.append("Verify ALL credentials with issuing institutions.")
            recommendations.append("Conduct comprehensive background check.")
            recommendations.append("Request documentation for major claims (degrees, certifications, awards).")
            recommendations.append("Consider using third-party verification services.")
            recommendations.append("Conduct multiple rounds of interviews with detailed technical questions.")
        
        # Component-specific recommendations
        if component_scores['timeline_score'] > 50:
            recommendations.append("⚠️ Timeline inconsistencies detected - verify all employment dates.")
        
        if component_scores['credential_score'] > 50:
            recommendations.append("⚠️ Credential issues detected - verify educational qualifications.")
        
        if component_scores['language_score'] > 60:
            recommendations.append("⚠️ Excessive exaggeration detected - request specific evidence for claims.")
        
        return recommendations


def main():
    """Test fraud scorer"""
    print("Testing Fraud Scorer...")
    print("=" * 80)
    
    scorer = FraudScorer()
    
    # Test with sample text
    sample_text = """
    John Doe
    john.doe@gmail.com
    
    I am the BEST software engineer in the world and a revolutionary expert.
    I single-handedly transformed multiple Fortune 500 companies.
    
    EXPERIENCE
    CTO - Startup Company (2020 - Present)
    VP Engineering - Another Corp (2019 - Present)  # Overlapping!
    
    EDUCATION
    PhD from Unknown University (2018 - 2020)
    Master from MIT (2017 - 2019)  # Overlaps with work!
    
    SKILLS
    Expert in 50+ programming languages, all cloud platforms, quantum computing
    
    CERTIFICATIONS
    Global Tech Excellence Award
    International IT Mastery Certificate
    """
    
    try:
        results = scorer.calculate_fraud_score(resume_text=sample_text)
        
        print(f"\nFRAUD ANALYSIS RESULTS:")
        print(f"  Fraud Score: {results['fraud_score']}/100")
        print(f"  Risk Category: {results['risk_category']}")
        print(f"  ML Confidence: {results['ml_confidence']}%")
        
        print(f"\nComponent Scores:")
        for component, score in results['component_scores'].items():
            print(f"  {component}: {score}")
        
        print(f"\nRed Flags Detected: {len(results['red_flags'])}")
        for flag in results['red_flags']:
            print(f"  [{flag['severity']}] {flag['description']}")
        
        print(f"\nRecommendations:")
        for rec in results['recommendations']:
            print(f"  • {rec}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
