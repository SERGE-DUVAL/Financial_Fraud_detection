"""
Financial Fraud Intelligence - Main Entry Point
Allows running the complete workflow from command line
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config
from src.utils.logger import setup_logger
from src.data.load_data import load_kaggle_creditcard_fraud
from src.data.validation import DataValidator
from src.data.preprocessing import DataPreprocessor
from src.models.train import ModelTrainer
from src.models.predict import ModelPredictor
from src.models.evaluate import ModelEvaluator
from src.models.model_selection import ModelSelector


def main():
    """Main workflow execution"""
    parser = argparse.ArgumentParser(description='Financial Fraud Intelligence - Credit Card Fraud Detection')
    parser.add_argument('--config', type=str, default='config/config.yaml', help='Path to config file')
    parser.add_argument('--data', type=str, default='data/raw/creditcard.csv', help='Path to dataset')
    parser.add_argument('--mode', type=str, default='train', choices=['train', 'predict'], help='Execution mode')
    args = parser.parse_args()

    # Setup configuration and logger
    config = get_config()
    logger = setup_logger(__name__, log_file='project.log')
    logger.info("Starting Financial Fraud Intelligence workflow")

    try:
        if args.mode == 'train':
            train_workflow(args.data, config, logger)
        elif args.mode == 'predict':
            predict_workflow(config, logger)
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        raise


def train_workflow(data_path, config, logger):
    """Execute training workflow"""
    logger.info("=== TRAINING WORKFLOW ===")

    # Load data
    logger.info(f"Loading data from {data_path}")
    df = load_kaggle_creditcard_fraud(data_path)

    # Validate data
    validator = DataValidator(target_column=config.get_target_column())
    validation_results = validator.validate_dataset(df)
    logger.info(f"Data validation: {validation_results['is_valid']}")

    # Preprocess data
    preprocessor = DataPreprocessor(
        target_column=config.get_target_column(),
        test_size=config.get_test_size(),
        random_state=config.get_random_state()
    )

    X_train, X_test, y_train, y_test, feature_names = preprocessor.preprocess_pipeline(
        df,
        remove_dup=True,
        handle_missing=True,
        scale=True,
        scaler_type=config.get('data.scaler_type', 'robust')
    )

    logger.info(f"Training set: {X_train.shape}")
    logger.info(f"Test set: {X_test.shape}")

    # Train models
    trainer = ModelTrainer(random_state=config.get_random_state())

    # Logistic Regression
    log_reg_params = config.get_model_params('logistic_regression')
    trainer.create_logistic_regression(log_reg_params)
    trainer.train_model('logistic_regression', X_train, y_train)

    # Random Forest
    rf_params = config.get_model_params('random_forest')
    trainer.create_random_forest(rf_params)
    trainer.train_model('random_forest', X_train, y_train)

    # Make predictions
    predictor = ModelPredictor(trainer.trained_models)
    y_pred_log = predictor.predict('logistic_regression', X_test)
    y_proba_log = predictor.predict_proba('logistic_regression', X_test)
    y_pred_rf = predictor.predict('random_forest', X_test)
    y_proba_rf = predictor.predict_proba('random_forest', X_test)

    # Evaluate models
    evaluator = ModelEvaluator()
    metrics_log = evaluator.evaluate_model(y_test, y_pred_log, y_proba_log, 'logistic_regression')
    metrics_rf = evaluator.evaluate_model(y_test, y_pred_rf, y_proba_rf, 'random_forest')

    # Select best model
    selector = ModelSelector()
    selector.set_selection_criteria(config.get('evaluation.primary_metric', 'f1'))
    comparison = selector.compare_models(evaluator.get_all_results())
    best_model = selector.select_best_model()

    logger.info("=== MODEL COMPARISON ===")
    logger.info(f"\n{comparison}")
    logger.info(f"\nBest model: {best_model['name']}")

    # Save best model
    models_path = config.get_models_path()
    trainer.save_model(best_model['name'], str(models_path / f"{best_model['name']}.joblib"))

    logger.info("Training workflow completed successfully")


def predict_workflow(config, logger):
    """Execute prediction workflow"""
    logger.info("=== PREDICTION WORKFLOW ===")
    logger.info("This workflow requires transaction data to predict")
    logger.info("For demonstration, use the notebook instead")


if __name__ == '__main__':
    main()
