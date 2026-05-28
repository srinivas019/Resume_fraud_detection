"""
Train fraud detection models using all available datasets:
  1. jsonresume-fake JSON resumes (fraudulent)
  2. Raw text resumes (fraudulent)
  3. Synthetic dataset with metadata labels (genuine + fraudulent)
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, classification_report
)
import joblib
from tqdm import tqdm
import docx
import fitz  # PyMuPDF

import config
from src.features.feature_extractor import FeatureExtractor


class JSONResumeTrainer:
    """Train models using all available resume datasets"""

    def __init__(self):
        self.fake_resumes_dir = config.DATA_DIR / 'jsonresume-fake' / 'resumes'
        self.raw_data_dir = config.DATA_DIR / 'raw'
        self.synthetic_dir = config.DATA_DIR / 'synthetic'
        self.models_dir = config.MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.feature_extractor = FeatureExtractor()
        self.scaler = StandardScaler()
        self.models = {}
        self.results = {}

    # ------------------------------------------------------------------ #
    #  Text extraction helpers
    # ------------------------------------------------------------------ #
    def json_resume_to_text(self, json_data: dict) -> str:
        """Convert JSON resume to plain text for feature extraction"""
        text_parts = []

        # Basic info
        basics = json_data.get('basics', {})
        if basics.get('name'):
            text_parts.append(f"Name: {basics['name']}")
        if basics.get('label'):
            text_parts.append(f"Title: {basics['label']}")
        if basics.get('summary'):
            text_parts.append(f"Summary: {basics['summary']}")
        if basics.get('email'):
            text_parts.append(f"Email: {basics['email']}")

        location = basics.get('location', {})
        if location:
            text_parts.append(
                f"Location: {location.get('city', '')}, "
                f"{location.get('countryCode', '')}"
            )

        # Work experience
        work = json_data.get('work', [])
        if work:
            text_parts.append("\nWORK EXPERIENCE:")
            for job in work:
                company = job.get('company', 'Unknown Company')
                position = job.get('position', 'Unknown Position')
                start = job.get('startDate', '')
                end = job.get('endDate', 'Present')
                summary = job.get('summary', '')
                highlights = job.get('highlights', [])

                text_parts.append(f"\n{position} at {company}")
                text_parts.append(f"{start} - {end}")
                if summary:
                    text_parts.append(summary)
                for h in highlights:
                    text_parts.append(f"- {h}")

        # Education
        education = json_data.get('education', [])
        if education:
            text_parts.append("\nEDUCATION:")
            for edu in education:
                institution = edu.get('institution', '')
                area = edu.get('area', '')
                degree = edu.get('studyType', '')
                start = edu.get('startDate', '')
                end = edu.get('endDate', '')
                text_parts.append(
                    f"{degree} in {area} from {institution} ({start} - {end})"
                )

        # Skills
        skills = json_data.get('skills', [])
        if skills:
            text_parts.append("\nSKILLS:")
            for skill in skills:
                name = skill.get('name', '')
                keywords = skill.get('keywords', [])
                text_parts.append(f"{name}: {', '.join(keywords)}")

        # References
        references = json_data.get('references', [])
        if references:
            text_parts.append("\nREFERENCES:")
            for ref in references:
                text_parts.append(
                    f"{ref.get('name', '')}: {ref.get('reference', '')}"
                )

        return "\n".join(text_parts)

    @staticmethod
    def _extract_text_from_docx(filepath: Path) -> str:
        """Extract text from a .docx file"""
        try:
            doc = docx.Document(str(filepath))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return ""

    @staticmethod
    def _extract_text_from_pdf(filepath: Path) -> str:
        """Extract text from a .pdf file"""
        try:
            doc = fitz.open(str(filepath))
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)
        except Exception:
            return ""

    # ------------------------------------------------------------------ #
    #  Dataset loaders
    # ------------------------------------------------------------------ #
    def _load_jsonresume_fake(self):
        """Load fake resumes from jsonresume-fake JSON files (label=1)"""
        json_files = list(self.fake_resumes_dir.glob('*.json'))
        print(f"  Found {len(json_files)} JSON files in jsonresume-fake/resumes")

        texts, labels, names = [], [], []
        for jp in tqdm(json_files, desc="  Loading jsonresume-fake JSON"):
            try:
                with open(jp, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                text = self.json_resume_to_text(data)
                if len(text) >= 50:
                    texts.append(text)
                    labels.append(1)   # Fraudulent
                    names.append(jp.name)
            except Exception as e:
                print(f"    ⚠ Error reading {jp.name}: {e}")
        return texts, labels, names

    def _load_raw_text(self):
        """Load raw text resumes as fraudulent (label=1)"""
        txt_files = list(self.raw_data_dir.glob('*.txt'))
        print(f"  Found {len(txt_files)} text files in data/raw")

        texts, labels, names = [], [], []
        for tp in tqdm(txt_files, desc="  Loading raw text files"):
            try:
                with open(tp, 'r', encoding='utf-8') as f:
                    text = f.read()
                if len(text) >= 50:
                    texts.append(text)
                    labels.append(1)   # Fraudulent
                    names.append(tp.name)
            except Exception as e:
                print(f"    ⚠ Error reading {tp.name}: {e}")
        return texts, labels, names

    def _load_synthetic_dataset(self, max_samples: int = 2000):
        """
        Load synthetic resumes using metadata.json for labels.
        Reads both .docx and .pdf files from data/synthetic/.
        
        Args:
            max_samples: Maximum number of samples to load (to keep
                         training time reasonable). Set to 0 for unlimited.
        """
        meta_path = self.synthetic_dir / 'metadata.json'
        if not meta_path.exists():
            print("  ⚠ metadata.json not found in data/synthetic – skipping")
            return [], [], []

        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        print(f"  Found {len(metadata)} entries in synthetic metadata.json")

        # Select a balanced subset
        genuine_entries = [m for m in metadata if m['label'] == 0]
        fraud_entries   = [m for m in metadata if m['label'] == 1]

        if max_samples > 0:
            half = max_samples // 2
            genuine_entries = genuine_entries[:half]
            fraud_entries   = fraud_entries[:half]

        entries = genuine_entries + fraud_entries
        print(f"  Using {len(genuine_entries)} genuine + "
              f"{len(fraud_entries)} fraudulent from synthetic data")

        texts, labels, names = [], [], []
        for entry in tqdm(entries, desc="  Loading synthetic resumes"):
            filepath = self.synthetic_dir / entry['filename']
            if not filepath.exists():
                continue

            ext = filepath.suffix.lower()
            if ext == '.docx':
                text = self._extract_text_from_docx(filepath)
            elif ext == '.pdf':
                text = self._extract_text_from_pdf(filepath)
            else:
                continue

            if len(text) >= 50:
                texts.append(text)
                labels.append(entry['label'])
                names.append(entry['filename'])

        return texts, labels, names

    # ------------------------------------------------------------------ #
    #  Master dataset loader
    # ------------------------------------------------------------------ #
    def load_dataset(self):
        """Combine all data sources and extract feature vectors"""
        print("\n" + "=" * 60)
        print("LOADING ALL DATASETS")
        print("=" * 60)

        all_texts, all_labels, all_names = [], [], []

        # --- Source 1: jsonresume-fake JSON ---
        print("\n[1/3] jsonresume-fake JSON files")
        t, l, n = self._load_jsonresume_fake()
        all_texts += t; all_labels += l; all_names += n

        # --- Source 2: raw text files ---
        print("\n[2/3] Raw text files")
        t, l, n = self._load_raw_text()
        all_texts += t; all_labels += l; all_names += n

        # --- Source 3: synthetic dataset ---
        print("\n[3/3] Synthetic dataset (metadata-labeled)")
        t, l, n = self._load_synthetic_dataset(max_samples=2000)
        all_texts += t; all_labels += l; all_names += n

        # Print dataset summary
        print("\n" + "-" * 40)
        print("DATASET SUMMARY BEFORE FEATURE EXTRACTION")
        print("-" * 40)
        total = len(all_texts)
        genuine = all_labels.count(0)
        fraudulent = all_labels.count(1)
        print(f"  Total resumes collected : {total}")
        print(f"  Genuine  (label=0)      : {genuine}")
        print(f"  Fraudulent (label=1)    : {fraudulent}")
        if total:
            print(f"  Fraud ratio             : {fraudulent/total*100:.1f}%")

        # ---- Feature extraction ----
        print("\nExtracting features from all resumes...")
        X_list, y_list, filenames = [], [], []

        for text, label, name in tqdm(
            zip(all_texts, all_labels, all_names),
            total=total,
            desc="Feature extraction"
        ):
            try:
                features = self.feature_extractor.extract_features(
                    resume_text=text
                )
                vec = self.feature_extractor.features_to_vector(features)
                X_list.append(vec)
                y_list.append(label)
                filenames.append(name)
            except Exception as e:
                # Silently skip problematic resumes
                continue

        X = np.array(X_list)
        y = np.array(y_list)

        print(f"\nDataset after feature extraction:")
        print(f"  Total Samples : {len(X)}")
        print(f"  Features      : {X.shape[1]}")
        print(f"  Genuine   (0) : {int((y == 0).sum())}")
        print(f"  Fraudulent(1) : {int((y == 1).sum())}")

        return X, y, filenames

    # ------------------------------------------------------------------ #
    #  Data preparation
    # ------------------------------------------------------------------ #
    def prepare_data(self, X, y, test_size=0.3):
        """Split and scale the data"""
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42,
            stratify=y if len(np.unique(y)) > 1 else None
        )

        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.2, random_state=42,
            stratify=y_temp if len(np.unique(y_temp)) > 1 else None
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)

        # Save scaler
        scaler_path = self.models_dir / 'scaler.pkl'
        joblib.dump(self.scaler, scaler_path)
        print(f"Scaler saved to: {scaler_path}")

        return (X_train_scaled, X_val_scaled, X_test_scaled,
                y_train, y_val, y_test)

    # ------------------------------------------------------------------ #
    #  Model training
    # ------------------------------------------------------------------ #
    def train_random_forest(self, X_train, y_train, X_val, y_val):
        """Train Random Forest model"""
        print("\n" + "=" * 60)
        print("Training Random Forest...")

        rf_config = config.MODEL_CONFIG['random_forest']
        rf_model = RandomForestClassifier(
            n_estimators=rf_config['n_estimators'],
            max_depth=rf_config['max_depth'],
            min_samples_split=rf_config['min_samples_split'],
            random_state=rf_config['random_state'],
            n_jobs=-1,
            verbose=1
        )
        rf_model.fit(X_train, y_train)

        y_pred = rf_model.predict(X_val)
        y_pred_proba = rf_model.predict_proba(X_val)[:, 1]

        metrics = self._evaluate_model(
            y_val, y_pred, y_pred_proba, "Random Forest"
        )

        model_path = self.models_dir / 'random_forest.pkl'
        joblib.dump(rf_model, model_path)
        print(f"Model saved to: {model_path}")

        self.models['random_forest'] = rf_model
        self.results['random_forest'] = metrics

    def train_xgboost(self, X_train, y_train, X_val, y_val):
        """Train XGBoost model"""
        print("\n" + "=" * 60)
        print("Training XGBoost...")

        xgb_config = config.MODEL_CONFIG['xgboost']
        xgb_model = xgb.XGBClassifier(
            max_depth=xgb_config['max_depth'],
            learning_rate=xgb_config['learning_rate'],
            n_estimators=xgb_config['n_estimators'],
            random_state=xgb_config['random_state'],
            eval_metric='logloss',
            use_label_encoder=False
        )
        xgb_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=True
        )

        y_pred = xgb_model.predict(X_val)
        y_pred_proba = xgb_model.predict_proba(X_val)[:, 1]

        metrics = self._evaluate_model(
            y_val, y_pred, y_pred_proba, "XGBoost"
        )

        model_path = self.models_dir / 'xgboost.pkl'
        joblib.dump(xgb_model, model_path)
        print(f"Model saved to: {model_path}")

        self.models['xgboost'] = xgb_model
        self.results['xgboost'] = metrics

    def train_gradient_boosting(self, X_train, y_train, X_val, y_val):
        """Train Gradient Boosting model"""
        print("\n" + "=" * 60)
        print("Training Gradient Boosting...")

        gb_model = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
            verbose=1
        )
        gb_model.fit(X_train, y_train)

        y_pred = gb_model.predict(X_val)
        y_pred_proba = gb_model.predict_proba(X_val)[:, 1]

        metrics = self._evaluate_model(
            y_val, y_pred, y_pred_proba, "Gradient Boosting"
        )

        model_path = self.models_dir / 'gradient_boosting.pkl'
        joblib.dump(gb_model, model_path)
        print(f"Model saved to: {model_path}")

        self.models['gradient_boosting'] = gb_model
        self.results['gradient_boosting'] = metrics

    # ------------------------------------------------------------------ #
    #  Evaluation
    # ------------------------------------------------------------------ #
    def _evaluate_model(self, y_true, y_pred, y_pred_proba, model_name):
        """Evaluate model and print metrics"""
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        roc_auc = (roc_auc_score(y_true, y_pred_proba)
                   if len(np.unique(y_true)) > 1 else 0)
        cm = confusion_matrix(y_true, y_pred)

        print(f"\n{model_name} Results:")
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1 Score:  {f1:.4f}")
        print(f"  ROC-AUC:   {roc_auc:.4f}")
        print(f"\nConfusion Matrix:\n{cm}")
        print(classification_report(
            y_true, y_pred,
            target_names=['Genuine', 'Fraudulent']
        ))

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': cm.tolist()
        }

    # ------------------------------------------------------------------ #
    #  Ensemble & Comparison
    # ------------------------------------------------------------------ #
    def create_ensemble(self, X_val, y_val):
        """Create ensemble model"""
        print("\n" + "=" * 60)
        print("Creating Ensemble Model...")

        predictions = {}
        for name, model in self.models.items():
            predictions[name] = model.predict_proba(X_val)[:, 1]

        weights = {
            'random_forest': 0.3,
            'xgboost': 0.4,
            'gradient_boosting': 0.3
        }

        ensemble_proba = np.zeros(len(X_val))
        for name, weight in weights.items():
            if name in predictions:
                ensemble_proba += weight * predictions[name]

        y_pred = (ensemble_proba >= 0.5).astype(int)

        metrics = self._evaluate_model(
            y_val, y_pred, ensemble_proba, "Ensemble"
        )
        self.results['ensemble'] = metrics

        # Save ensemble config
        ensemble_config = {'weights': weights}
        config_path = self.models_dir / 'ensemble_config.json'
        with open(config_path, 'w') as f:
            json.dump(ensemble_config, f, indent=2)
        print(f"Ensemble config saved to: {config_path}")

    def _save_comparison_chart(self):
        """Generate and save a model comparison bar chart"""
        if not self.results:
            return

        model_names = list(self.results.keys())
        metrics_keys = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
        x = np.arange(len(model_names))
        bar_width = 0.15

        fig, ax = plt.subplots(figsize=(12, 6))
        for i, metric in enumerate(metrics_keys):
            values = [self.results[m].get(metric, 0) for m in model_names]
            ax.bar(x + i * bar_width, values, bar_width, label=metric.upper())

        ax.set_ylabel('Score')
        ax.set_title('Model Comparison – Resume Fraud Detection')
        ax.set_xticks(x + bar_width * 2)
        ax.set_xticklabels([n.replace('_', ' ').title() for n in model_names])
        ax.legend()
        ax.set_ylim(0, 1.05)
        plt.tight_layout()

        chart_path = self.models_dir / 'model_comparison.png'
        plt.savefig(chart_path, dpi=150)
        plt.close()
        print(f"Comparison chart saved to: {chart_path}")

    # ------------------------------------------------------------------ #
    #  Main pipeline
    # ------------------------------------------------------------------ #
    def train_all_models(self):
        """Run complete training pipeline"""
        print("=" * 70)
        print("TRAINING MODELS WITH ALL AVAILABLE DATASETS")
        print("=" * 70)

        # Load data
        X, y, filenames = self.load_dataset()

        if len(X) == 0:
            print("\n❌ No data loaded. Make sure datasets are present.")
            return

        # Prepare data
        (X_train, X_val, X_test,
         y_train, y_val, y_test) = self.prepare_data(X, y)

        print(f"\nData split:")
        print(f"  Training:   {len(X_train)} samples")
        print(f"  Validation: {len(X_val)} samples")
        print(f"  Test:       {len(X_test)} samples")

        # Train models
        self.train_random_forest(X_train, y_train, X_val, y_val)
        self.train_xgboost(X_train, y_train, X_val, y_val)
        self.train_gradient_boosting(X_train, y_train, X_val, y_val)

        # Create ensemble
        self.create_ensemble(X_val, y_val)

        # Final test evaluation
        print("\n" + "=" * 70)
        print("FINAL EVALUATION ON TEST SET")
        print("=" * 70)

        for name, model in self.models.items():
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            self._evaluate_model(
                y_test, y_pred, y_pred_proba, f"{name} (Test)"
            )

        # Save results
        results_path = self.models_dir / 'training_results.json'
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {results_path}")

        # Save comparison chart
        self._save_comparison_chart()

        print("\n" + "=" * 70)
        print("TRAINING COMPLETE!")
        print("=" * 70)


def main():
    trainer = JSONResumeTrainer()
    trainer.train_all_models()


if __name__ == "__main__":
    main()
