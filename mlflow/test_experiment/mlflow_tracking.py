import os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import mlflow
import mlflow.sklearn

def load_and_preprocess_titanic():
    """Load and preprocess the Titanic dataset"""
    # Load single dataset
    df = pd.read_csv("./titanic.csv")
    
    # Feature engineering
    df['Title'] = df['Name'].str.extract(' ([A-Za-z]+)\.', expand=False)
    title_mapping = {
        'Lady': 'Rare', 'Countess': 'Rare', 'Capt': 'Rare', 'Col': 'Rare',
        'Don': 'Rare', 'Dr': 'Rare', 'Major': 'Rare', 'Rev': 'Rare', 
        'Sir': 'Rare', 'Jonkheer': 'Rare', 'Dona': 'Rare',
        'Mlle': 'Miss', 'Ms': 'Miss', 'Mme': 'Mrs'
    }
    df['Title'] = df['Title'].replace(title_mapping)    
    df['FamilySize'] = df['SibSp'] + df['Parch'] + 1
    df['IsAlone'] = (df['FamilySize'] == 1).astype(int)
    df['FareCategory'] = pd.qcut(df['Fare'], q=4, labels=['Low', 'Medium', 'High', 'Very High'])
    df['Age'] = df['Age'].fillna(df['Age'].median())
    df['AgeCategory'] = pd.cut(df['Age'], bins=[0, 12, 20, 40, 60, 100], 
                              labels=['Child', 'Teen', 'Adult', 'Middle', 'Senior'])
    df = df.drop(['Name', 'Ticket', 'Cabin', 'PassengerId'], axis=1)
    
    return df

def create_pipeline(model, params):
    """Create a pipeline with preprocessing and model"""
    numeric_features = ['Age', 'Fare', 'FamilySize']
    categorical_features = ['Sex', 'Embarked', 'Title', 'AgeCategory', 'FareCategory']
    
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(drop='first', handle_unknown='ignore'))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    return Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])

# Rest of the code remains the same...

def evaluate_model(model, X_test, y_test):
    """Evaluate model and return metrics dictionary"""
    y_pred = model.predict(X_test)
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, average='weighted'),
        'recall': recall_score(y_test, y_pred, average='weighted'),
        'f1': f1_score(y_test, y_pred, average='weighted')
    }
    
    return metrics, y_pred

def train_and_log_models():
    """Train multiple models and log everything to MLflow"""
    mlflow.set_tracking_uri('http://localhost:5001')
    mlflow.set_experiment("titanic_classification")
    
    print("Loading and preprocessing data...")
    data = load_and_preprocess_titanic()
    
    if not os.path.exists("data"):
        os.makedirs("data")
    data.to_csv("processed_titanic.csv", index=False)
    
    X = data.drop('Survived', axis=1)
    y = data['Survived']
    
    print("Splitting data into train and test sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    models = {
        'random_forest': {
            'model': RandomForestClassifier(random_state=42),
            'params': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 2,
                'class_weight': 'balanced'
            }
        },
        'logistic_regression': {
            'model': LogisticRegression(random_state=42),
            'params': {
                'C': 1.0,
                'max_iter': 1000,
                'class_weight': 'balanced'
            }
        },
        'svm': {
            'model': SVC(random_state=42, probability=True),  # Added probability=True
            'params': {
                'C': 1.0,
                'kernel': 'rbf',
                'class_weight': 'balanced'
            }
        }
    }
    
    # Train and log each model
    for model_name, model_info in models.items():
        print(f"Training {model_name}...")
        
        with mlflow.start_run(run_name=f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"):
            # Log dataset info
            mlflow.log_artifact("processed_titanic.csv", "dataset")
            mlflow.log_param("dataset_shape", X.shape)
            mlflow.log_param("feature_columns", list(X.columns))
            mlflow.log_param("train_size", len(X_train))
            mlflow.log_param("test_size", len(X_test))
            
            # Create and train pipeline
            model_info['model'].set_params(**model_info['params'])
            pipeline = create_pipeline(model_info['model'], model_info['params'])
            
            # Log model parameters
            mlflow.log_params(model_info['params'])
            
            # Train model
            pipeline.fit(X_train, y_train)
            
            # Evaluate model
            metrics, predictions = evaluate_model(pipeline, X_test, y_test)
            
            # Log metrics
            mlflow.log_metrics(metrics)
            
            # Perform cross-validation and log results
            cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5)
            mlflow.log_metric("cv_mean_accuracy", cv_scores.mean())
            mlflow.log_metric("cv_std_accuracy", cv_scores.std())
            
            # Create and log confusion matrix
            cm = confusion_matrix(y_test, predictions)
            cm_df = pd.DataFrame(
                cm, 
                columns=['Predicted Not Survived', 'Predicted Survived'],
                index=['Actually Not Survived', 'Actually Survived']
            )
            
            if not os.path.exists("outputs"):
                os.makedirs("outputs")
            cm_df.to_csv(f"outputs/{model_name}_confusion_matrix.csv")
            mlflow.log_artifact(f"outputs/{model_name}_confusion_matrix.csv", "confusion_matrix")
            
            # For Random Forest, log feature importance
            if model_name == 'random_forest':
                feature_importance = pd.DataFrame({
                    'feature': X.columns,
                    'importance': pipeline.named_steps['classifier'].feature_importances_
                }).sort_values('importance', ascending=False)
                
                feature_importance.to_csv("outputs/feature_importance.csv", index=False)
                mlflow.log_artifact("outputs/feature_importance.csv", "feature_importance")
            
            # Log the model
            mlflow.sklearn.log_model(pipeline, f"{model_name}_model")
            
            # Log sample predictions
            sample_predictions = pd.DataFrame({
                'actual': y_test[:10],
                'predicted': predictions[:10],
                'probability': pipeline.predict_proba(X_test)[:10, 1]  
            })
            sample_predictions.to_csv(f"outputs/{model_name}_sample_predictions.csv", index=False)
            mlflow.log_artifact(f"outputs/{model_name}_sample_predictions.csv", "sample_predictions")
            
            print(f"Completed training {model_name}. Accuracy: {metrics['accuracy']:.4f}")

if __name__ == "__main__":
    try:
        print("Starting model training and logging...")
        train_and_log_models()
        print("Successfully completed training and logging!")
    except Exception as e:
        print(f"Error during training: {str(e)}")