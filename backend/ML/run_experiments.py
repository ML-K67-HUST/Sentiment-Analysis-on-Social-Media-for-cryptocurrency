#!/usr/bin/env python3
"""
Main Experiment Script - Quick Win
Run Naive Bayes + SVM comparison with evaluation

Usage:
    python run_experiments.py
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_preparation import load_labeled_data, prepare_train_test_split
from feature_extraction import FeatureExtractor
from models import train_all_models
from evaluation import (
    evaluate_model,
    compare_models,
    plot_confusion_matrix,
    plot_model_comparison,
    print_summary
)


def main():
    """Main experiment pipeline"""
    
    print("\n" + "="*80)
    print("🚀 SENTIMENT CLASSIFICATION - ML MODEL COMPARISON")
    print("="*80)
    print("\nThis experiment compares multiple ML models for crypto sentiment analysis.")
    print("Models: Naive Bayes, SVM (Linear), SVM (RBF), Logistic Regression")
    print("="*80)
    
    # =========================================================================
    # STEP 1: LOAD DATA
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 1: DATA LOADING")
    print("="*80)
    
    try:
        df = load_labeled_data(collection_name='cmc_news')
    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        print("\n💡 Make sure you have labeled data in MongoDB!")
        print("   Run: docker exec sentiman_backend_api python label_existing_data.py")
        return
    
    if len(df) < 50:
        print(f"\n⚠️  Warning: Only {len(df)} labeled samples found.")
        print("   For reliable results, you should have at least 200-300 samples.")
        print("   Continue anyway? (y/n)")
        # Auto-continue for now
        # response = input().strip().lower()
        # if response != 'y':
        #     return
    
    # =========================================================================
    # STEP 2: TRAIN/TEST SPLIT
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 2: TRAIN/TEST SPLIT")
    print("="*80)
    
    X_train, X_test, y_train, y_test = prepare_train_test_split(
        df,
        test_size=0.3,
        random_state=42
    )
    
    # =========================================================================
    # STEP 3: FEATURE EXTRACTION
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 3: FEATURE EXTRACTION (TF-IDF)")
    print("="*80)
    
    # Initialize feature extractor
    extractor = FeatureExtractor(
        max_features=5000,
        ngram_range=(1, 2)  # Unigram + Bigram
    )
    
    # Fit on training data and transform both sets
    X_train_tfidf = extractor.fit_transform(X_train)
    X_test_tfidf = extractor.transform(X_test)
    
    print(f"\n✅ Feature extraction complete!")
    print(f"   Training features shape: {X_train_tfidf.shape}")
    print(f"   Test features shape: {X_test_tfidf.shape}")
    
    # Show top features per class
    print(f"\n📊 Top 10 TF-IDF features per class:")
    top_features = extractor.get_top_features_by_class(X_train_tfidf, y_train, top_n=10)
    for cls, features in top_features.items():
        print(f"\n   {cls.capitalize()}:")
        for word, score in features:
            print(f"      {word}: {score:.4f}")
    
    # =========================================================================
    # STEP 4: TRAIN MODELS
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 4: TRAIN ALL MODELS")
    print("="*80)
    
    models = train_all_models(X_train_tfidf, y_train, X_test_tfidf, y_test)
    
    # =========================================================================
    # STEP 5: EVALUATE MODELS
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 5: MODEL EVALUATION")
    print("="*80)
    
    class_names = sorted(list(set(y_train)))
    results_list = []
    
    # Create results directory
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    for model_name, model in models.items():
        result = evaluate_model(model, X_test_tfidf, y_test, class_names=class_names)
        results_list.append(result)
        
        # Plot confusion matrix
        fig = plot_confusion_matrix(
            result['confusion_matrix'],
            class_names,
            model_name,
            save_path=os.path.join(results_dir, f'confusion_matrix_{model_name.replace(" ", "_")}.png')
        )
        fig.close()
    
    # =========================================================================
    # STEP 6: COMPARE MODELS
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 6: MODEL COMPARISON")
    print("="*80)
    
    # Create comparison table
    df_comparison = compare_models(
        results_list,
        save_path=os.path.join(results_dir, 'model_comparison.csv')
    )
    
    # Plot comparison chart
    fig = plot_model_comparison(
        df_comparison,
        save_path=os.path.join(results_dir, 'model_comparison.png')
    )
    fig.close()
    
    # Print summary
    print_summary(results_list)
    
    # =========================================================================
    # STEP 7: SAVE RESULTS
    # =========================================================================
    print("\n" + "="*80)
    print("STEP 7: SAVE RESULTS")
    print("="*80)
    
    # Save detailed results
    import json
    
    # Convert numpy arrays to lists for JSON serialization
    results_json = []
    for result in results_list:
        result_copy = result.copy()
        result_copy['confusion_matrix'] = result['confusion_matrix'].tolist()
        result_copy['precision_per_class'] = result['precision_per_class'].tolist()
        result_copy['recall_per_class'] = result['recall_per_class'].tolist()
        result_copy['f1_per_class'] = result['f1_per_class'].tolist()
        result_copy['support_per_class'] = result['support_per_class'].tolist()
        result_copy.pop('predictions', None)  # Remove predictions (too large)
        results_json.append(result_copy)
    
    with open(os.path.join(results_dir, 'detailed_results.json'), 'w') as f:
        json.dump(results_json, f, indent=2)
    
    print(f"\n💾 All results saved to: {results_dir}")
    print(f"   • Confusion matrices (PNG)")
    print(f"   • Model comparison table (CSV)")
    print(f"   • Model comparison chart (PNG)")
    print(f"   • Detailed results (JSON)")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "="*80)
    print("✅ EXPERIMENT COMPLETE!")
    print("="*80)
    
    best_model = df_comparison.iloc[0]
    print(f"\n🏆 Best Model: {best_model['Model']}")
    print(f"   Accuracy: {best_model['Accuracy']:.4f}")
    print(f"   Precision (Macro): {best_model['Precision (Macro)']:.4f}")
    print(f"   Recall (Macro): {best_model['Recall (Macro)']:.4f}")
    print(f"   F1-Score (Macro): {best_model['F1-Score (Macro)']:.4f}")
    
    print(f"\n📊 Results Summary:")
    print(f"   • Trained {len(models)} models")
    print(f"   • Evaluated on {len(X_test)} test samples")
    print(f"   • Best F1-Score (Macro): {best_model['F1-Score (Macro)']:.4f}")
    
    print(f"\n📂 Check results directory for detailed outputs:")
    print(f"   {results_dir}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Experiment interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

