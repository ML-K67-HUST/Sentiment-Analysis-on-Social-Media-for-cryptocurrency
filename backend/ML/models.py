from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC, SVC
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import numpy as np


class SentimentClassifier:    
    def __init__(self, model_name):
        self.model_name = model_name
        self.model = None
    
    def train(self, X_train, y_train):
        print(f"\n🎓 Training {self.model_name}...")
        self.model.fit(X_train, y_train)
        print(f"   ✅ Training complete!")
    
    def predict(self, X):
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict class probabilities"""
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        elif hasattr(self.model, 'decision_function'):
            # For SVM, use decision function
            return self.model.decision_function(X)
        else:
            return None
    
    def cross_validate(self, X, y, cv=5):
        print(f"\n🔄 Running {cv}-fold cross-validation for {self.model_name}...")
        
        scoring = ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro']
        scores = {}
        
        for metric in scoring:
            cv_scores = cross_val_score(
                self.model, X, y,
                cv=cv,
                scoring=metric,
                n_jobs=-1
            )
            scores[metric] = {
                'mean': cv_scores.mean(),
                'std': cv_scores.std(),
                'scores': cv_scores
            }
            print(f"   {metric}: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        return scores


class NaiveBayesClassifier(SentimentClassifier):
    
    def __init__(self, alpha=1.0):
        super().__init__("Naive Bayes")
        self.alpha = alpha
        self.model = MultinomialNB(alpha=alpha)
        
        print(f"📊 {self.model_name} initialized:")
        print(f"   Alpha (Laplace smoothing): {alpha}")
        print(f"   Assumption: Conditional independence of features")


class SVMClassifier(SentimentClassifier):
    
    def __init__(self, kernel='linear', C=1.0, gamma='scale', class_weight='balanced'):
        model_name = f"SVM ({kernel} kernel)"
        super().__init__(model_name)
        
        self.kernel = kernel
        self.C = C
        self.gamma = gamma
        
        if kernel == 'linear':
            self.model = LinearSVC(
                C=C,
                class_weight=class_weight,
                max_iter=2000,
                random_state=42,
                dual=False
            )
        else:
            self.model = SVC(
                kernel=kernel,
                C=C,
                gamma=gamma,
                class_weight=class_weight,
                max_iter=2000,
                random_state=42,
                probability=True 
            )
        
        print(f"📊 {self.model_name} initialized:")
        print(f"   Kernel: {kernel}")
        print(f"   C (regularization): {C}")
        if kernel == 'rbf':
            print(f"   Gamma: {gamma}")
        print(f"   Class weight: {class_weight}")
        print(f"   Note: SVM is a 'blackbox' model (hard to interpret)")


class LogisticRegressionClassifier(SentimentClassifier):
    
    def __init__(self, C=1.0, penalty='l2', class_weight='balanced'):

        super().__init__("Logistic Regression")
        
        self.model = LogisticRegression(
            C=C,
            penalty=penalty,
            class_weight=class_weight,
            max_iter=1000,
            random_state=42,
            solver='saga',  # Supports both l1 and l2
            n_jobs=-1
        )
        
        print(f"📊 {self.model_name} initialized:")
        print(f"   C (inverse regularization): {C}")
        print(f"   Penalty: {penalty}")
        print(f"   Class weight: {class_weight}")


def train_all_models(X_train, y_train, X_test, y_test):
    """
    Train all models and return them
    
    Args:
        X_train, y_train: Training data
        X_test, y_test: Test data
        
    Returns:
        Dictionary of trained models
    """
    models = {}
    
    # 1. Naive Bayes (fast, interpretable)
    print("\n" + "="*60)
    print("MODEL 1: NAIVE BAYES")
    print("="*60)
    nb = NaiveBayesClassifier(alpha=1.0)
    nb.train(X_train, y_train)
    models['Naive Bayes'] = nb
    
    # 2. SVM with Linear Kernel (good for high-dimensional data)
    print("\n" + "="*60)
    print("MODEL 2: SVM (LINEAR KERNEL)")
    print("="*60)
    svm_linear = SVMClassifier(kernel='linear', C=1.0)
    svm_linear.train(X_train, y_train)
    models['SVM (Linear)'] = svm_linear
    
    # 3. SVM with RBF Kernel (non-linear, more powerful)
    print("\n" + "="*60)
    print("MODEL 3: SVM (RBF KERNEL)")
    print("="*60)
    svm_rbf = SVMClassifier(kernel='rbf', C=1.0, gamma='scale')
    svm_rbf.train(X_train, y_train)
    models['SVM (RBF)'] = svm_rbf
    
    # 4. Logistic Regression (baseline, interpretable)
    print("\n" + "="*60)
    print("MODEL 4: LOGISTIC REGRESSION (BASELINE)")
    print("="*60)
    logreg = LogisticRegressionClassifier(C=1.0, penalty='l2')
    logreg.train(X_train, y_train)
    models['Logistic Regression'] = logreg
    
    return models


if __name__ == "__main__":
    # Test with dummy data
    from sklearn.datasets import make_classification
    
    X, y = make_classification(
        n_samples=1000,
        n_features=100,
        n_informative=50,
        n_classes=3,
        random_state=42
    )
    
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    
    # Test Naive Bayes
    nb = NaiveBayesClassifier(alpha=1.0)
    nb.train(X_train, y_train)
    predictions = nb.predict(X_test)
    
    print(f"\n✅ Model testing passed!")
    print(f"Predictions shape: {predictions.shape}")

