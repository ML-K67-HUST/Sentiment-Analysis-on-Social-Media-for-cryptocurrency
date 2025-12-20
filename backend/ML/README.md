# ML Module - Sentiment Classification

Machine Learning models for cryptocurrency sentiment analysis.

## 📁 Structure

```
ML/
├── __init__.py                 # Package initializer
├── data_preparation.py         # Data loading from MongoDB
├── feature_extraction.py       # TF-IDF vectorization
├── models.py                   # ML model implementations
├── evaluation.py               # Metrics and comparison
├── run_experiments.py          # Main experiment script
├── results/                    # Generated outputs
│   ├── confusion_matrix_*.png
│   ├── model_comparison.csv
│   ├── model_comparison.png
│   └── detailed_results.json
└── README.md                   # This file
```

## 🚀 Quick Start

### Run Experiment

```bash
# Inside backend container:
cd /src
python ML/run_experiments.py
```

### Or from host:

```bash
docker exec sentiman_backend_api python /src/ML/run_experiments.py
```

## 📊 Implemented Models

1. **Naive Bayes** - Fast, interpretable baseline
2. **SVM (Linear)** - Strong high-dimensional performance
3. **SVM (RBF)** - Non-linear kernel variant
4. **Logistic Regression** - Simple linear baseline

## 🎯 Features

- ✅ TF-IDF vectorization (unigram + bigram)
- ✅ Text preprocessing (cleaning, stopwords removal)
- ✅ Stratified train/test split
- ✅ Class weight balancing for imbalanced data
- ✅ Comprehensive evaluation (Confusion Matrix, P/R/F1)
- ✅ Model comparison with visualizations

## 📈 Results

Check `ML_EXPERIMENT_RESULTS.md` in project root for full analysis.

**Best Model:** SVM (Linear)
- F1-Score (Macro): 0.317
- Accuracy: 65.2%

## 🔧 Dependencies

```
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
nltk>=3.8.0
```

## 📝 Usage

### Load Data

```python
from ML.data_preparation import load_labeled_data, prepare_train_test_split

df = load_labeled_data(collection_name='cmc_news')
X_train, X_test, y_train, y_test = prepare_train_test_split(df)
```

### Extract Features

```python
from ML.feature_extraction import FeatureExtractor

extractor = FeatureExtractor(max_features=5000, ngram_range=(1, 2))
X_train_tfidf = extractor.fit_transform(X_train)
X_test_tfidf = extractor.transform(X_test)
```

### Train Models

```python
from ML.models import NaiveBayesClassifier, SVMClassifier

nb = NaiveBayesClassifier(alpha=1.0)
nb.train(X_train_tfidf, y_train)

svm = SVMClassifier(kernel='linear', C=1.0)
svm.train(X_train_tfidf, y_train)
```

### Evaluate

```python
from ML.evaluation import evaluate_model, compare_models

result_nb = evaluate_model(nb, X_test_tfidf, y_test)
result_svm = evaluate_model(svm, X_test_tfidf, y_test)

df_comparison = compare_models([result_nb, result_svm])
```

## 🎓 For Course Submission

This module demonstrates:

✅ **Multiple ML algorithms** (Naive Bayes, SVM, Logistic Regression)  
✅ **Feature engineering** (TF-IDF with preprocessing)  
✅ **Proper evaluation** (Confusion Matrix, P/R/F1)  
✅ **Imbalanced data handling** (Class weights, stratified split)  
✅ **Model comparison** (Comparison table + visualizations)

## 📊 Next Steps for Higher Score

1. **Label more data** (current: 152 → target: 500-1000)
2. **Add ensemble methods** (Random Forest, XGBoost)
3. **Cross-validation** (5-fold CV)
4. **Deep Learning** (CNN/LSTM for text)

## 📧 Support

Check main project documentation for setup and troubleshooting.

