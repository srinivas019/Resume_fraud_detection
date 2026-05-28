"""
Configuration settings for Resume Fraud Detection System
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Data directories
DATA_DIR = BASE_DIR / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
SYNTHETIC_DATA_DIR = DATA_DIR / 'synthetic'

# Model directories
MODELS_DIR = BASE_DIR / 'models'

# Web directories
WEB_DIR = BASE_DIR / 'web'
UPLOAD_DIR = WEB_DIR / 'uploads'
STATIC_DIR = WEB_DIR / 'static'
TEMPLATES_DIR = WEB_DIR / 'templates'

# Create directories if they don't exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, SYNTHETIC_DATA_DIR, 
                  MODELS_DIR, UPLOAD_DIR, STATIC_DIR, TEMPLATES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Dataset configuration
DATASET_CONFIG = {
    'total_resumes': 10000,
    'train_split': 0.70,
    'val_split': 0.15,
    'test_split': 0.15,
    'fraud_ratio': 0.50,  # 50% fraudulent, 50% genuine
    'formats': ['pdf', 'docx'],
}

# NLP configuration
NLP_CONFIG = {
    'spacy_model': 'en_core_web_lg',
    'max_sequence_length': 512,
    'embedding_dim': 300,
}

# Model configuration
MODEL_CONFIG = {
    'random_forest': {
        'n_estimators': 500,
        'max_depth': 30,
        'min_samples_split': 2,
        'random_state': 42,
    },
    'xgboost': {
        'max_depth': 10,
        'learning_rate': 0.1,
        'n_estimators': 300,
        'random_state': 42,
    },
    'lstm': {
        'units': 128,
        'dropout': 0.3,
        'epochs': 50,
        'batch_size': 32,
    },
    'bert': {
        'model_name': 'bert-base-uncased',
        'max_length': 512,
        'epochs': 3,
        'batch_size': 8,
        'learning_rate': 2e-5,
    },
    'ensemble': {
        'weights': {
            'bert': 0.4,
            'xgboost': 0.3,
            'random_forest': 0.2,
            'lstm': 0.1,
        }
    }
}

# Fraud scoring configuration
FRAUD_SCORING = {
    'timeline_weight': 0.25,
    'credential_weight': 0.25,
    'language_weight': 0.25,
    'anomaly_weight': 0.25,
    'risk_thresholds': {
        'low': 30,
        'medium': 60,
        'high': 100,
    }
}

# Flask configuration
FLASK_CONFIG = {
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
    'ALLOWED_EXTENSIONS': {'pdf', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'},
    'HOST': '0.0.0.0',
    'PORT': 5000,
    'DEBUG': True,
}

# Database configuration
DATABASE_CONFIG = {
    'type': 'sqlite',  # Change to 'postgresql' for production
    'sqlite_path': BASE_DIR / 'resume_fraud.db',
    'postgresql': {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', 5432),
        'database': os.environ.get('DB_NAME', 'resume_fraud_db'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', ''),
    }
}

# Feature extraction configuration
FEATURE_CONFIG = {
    'min_resume_length': 100,
    'max_resume_length': 10000,
    'suspicious_keywords': [
        'best', 'greatest', 'expert', 'guru', 'ninja', 'rockstar',
        'world-class', 'top', 'leading', 'premier', 'elite'
    ],
    'vague_quantifiers': [
        'many', 'several', 'numerous', 'various', 'multiple',
        'significant', 'substantial', 'extensive'
    ],
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'app.log',
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}
