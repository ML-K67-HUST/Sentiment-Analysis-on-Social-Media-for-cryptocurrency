"""
Model Evaluation and Comparison
Comprehensive evaluation metrics for sentiment classification
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    precision_recall_fscore_support,
    accuracy_score
)


def evaluate_model(model, X_test, y_test, class_names=['negative', 'neutral', 'positive']):
    """
    Comprehensive evaluation for a single model
    
    Args:
        model: Trained model with predict() method
        X_test: Test features
        y_test: Test labels
        class_names: List of class names for display
        
    Returns:
        Dictionary with all evaluation metrics
    """
    print(f"\n📊 Evaluating {model.model_name}...")
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # 1. Accuracy
    accuracy = accuracy_score(y_test, y_pred)
    
    # 2. Per-class metrics
    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, y_pred, average=None, labels=class_names
    )
    
    # 3. Macro-averaged metrics (important for imbalanced data)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_test, y_pred, average='macro'
    )
    
    # 4. Weighted-averaged metrics
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_test, y_pred, average='weighted'
    )
    
    # 5. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=class_names)
    
    # 6. Classification Report
    report = classification_report(
        y_test, y_pred,
        target_names=[name.capitalize() for name in class_names],
        digits=4
    )
    
    # Print results
    print(f"\n📈 Results for {model.model_name}:")
    print(f"   Overall Accuracy: {accuracy:.4f}")
    print(f"   Precision (Macro): {precision_macro:.4f}")
    print(f"   Recall (Macro): {recall_macro:.4f}")
    print(f"   F1-Score (Macro): {f1_macro:.4f}")
    
    print(f"\n   Per-Class Metrics:")
    for i, class_name in enumerate(class_names):
        print(f"   {class_name.capitalize()}:")
        print(f"      Precision: {precision[i]:.4f}")
        print(f"      Recall: {recall[i]:.4f}")
        print(f"      F1-Score: {f1[i]:.4f}")
        print(f"      Support: {support[i]}")
    
    print(f"\n   Classification Report:")
    print(report)
    
    return {
        'model_name': model.model_name,
        'accuracy': accuracy,
        'precision_macro': precision_macro,
        'recall_macro': recall_macro,
        'f1_macro': f1_macro,
        'precision_weighted': precision_weighted,
        'recall_weighted': recall_weighted,
        'f1_weighted': f1_weighted,
        'precision_per_class': precision,
        'recall_per_class': recall,
        'f1_per_class': f1,
        'support_per_class': support,
        'confusion_matrix': cm,
        'classification_report': report,
        'predictions': y_pred
    }


def plot_confusion_matrix(cm, class_names, model_name, save_path=None):
    """
    Plot confusion matrix as heatmap
    
    Args:
        cm: Confusion matrix
        class_names: List of class names
        model_name: Name of the model
        save_path: Path to save figure (optional)
    """
    plt.figure(figsize=(8, 6))
    
    # Create heatmap
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=[name.capitalize() for name in class_names],
        yticklabels=[name.capitalize() for name in class_names],
        cbar_kws={'label': 'Count'}
    )
    
    plt.title(f'Confusion Matrix - {model_name}', fontsize=14, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"   💾 Saved confusion matrix to: {save_path}")
    
    return plt


def compare_models(results_list, save_path=None):
    """
    Create comparison table for all models
    
    Args:
        results_list: List of result dictionaries from evaluate_model()
        save_path: Path to save comparison table (optional)
        
    Returns:
        DataFrame with comparison
    """
    print(f"\n📊 Model Comparison:")
    print("="*80)
    
    comparison_data = []
    
    for result in results_list:
        comparison_data.append({
            'Model': result['model_name'],
            'Accuracy': result['accuracy'],
            'Precision (Macro)': result['precision_macro'],
            'Recall (Macro)': result['recall_macro'],
            'F1-Score (Macro)': result['f1_macro'],
            'Precision (Weighted)': result['precision_weighted'],
            'Recall (Weighted)': result['recall_weighted'],
            'F1-Score (Weighted)': result['f1_weighted']
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Sort by F1-Score (Macro) - best metric for imbalanced data
    df_comparison = df_comparison.sort_values('F1-Score (Macro)', ascending=False)
    
    # Print table
    print(df_comparison.to_string(index=False))
    print("="*80)
    
    # Highlight best model
    best_model = df_comparison.iloc[0]
    print(f"\n🏆 Best Model: {best_model['Model']}")
    print(f"   F1-Score (Macro): {best_model['F1-Score (Macro)']:.4f}")
    
    # Save to CSV
    if save_path:
        df_comparison.to_csv(save_path, index=False)
        print(f"\n💾 Comparison table saved to: {save_path}")
    
    return df_comparison


def plot_model_comparison(df_comparison, save_path=None):
    """
    Plot bar chart comparing models
    
    Args:
        df_comparison: DataFrame from compare_models()
        save_path: Path to save figure (optional)
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    metrics = [
        ('Accuracy', 'Accuracy'),
        ('Precision (Macro)', 'Precision (Macro-Avg)'),
        ('Recall (Macro)', 'Recall (Macro-Avg)'),
        ('F1-Score (Macro)', 'F1-Score (Macro-Avg)')
    ]
    
    for idx, (metric, title) in enumerate(metrics):
        ax = axes[idx // 2, idx % 2]
        
        # Sort by this metric
        df_sorted = df_comparison.sort_values(metric, ascending=True)
        
        # Plot horizontal bar chart
        bars = ax.barh(df_sorted['Model'], df_sorted[metric])
        
        # Color bars by value (green for high, red for low)
        colors = plt.cm.RdYlGn(df_sorted[metric] / df_sorted[metric].max())
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax.set_xlabel(title, fontsize=11, fontweight='bold')
        ax.set_xlim([0, 1.0])
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (model, value) in enumerate(zip(df_sorted['Model'], df_sorted[metric])):
            ax.text(value + 0.02, i, f'{value:.3f}', va='center', fontsize=9)
    
    plt.suptitle('Model Comparison - All Metrics', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"   💾 Saved comparison chart to: {save_path}")
    
    return fig


def print_summary(results_list):
    """
    Print executive summary of all models
    
    Args:
        results_list: List of result dictionaries
    """
    print("\n" + "="*80)
    print("📋 EXECUTIVE SUMMARY")
    print("="*80)
    
    # Find best model for each metric
    best_accuracy = max(results_list, key=lambda x: x['accuracy'])
    best_precision = max(results_list, key=lambda x: x['precision_macro'])
    best_recall = max(results_list, key=lambda x: x['recall_macro'])
    best_f1 = max(results_list, key=lambda x: x['f1_macro'])
    
    print(f"\n🏆 Best Models by Metric:")
    print(f"   Accuracy: {best_accuracy['model_name']} ({best_accuracy['accuracy']:.4f})")
    print(f"   Precision: {best_precision['model_name']} ({best_precision['precision_macro']:.4f})")
    print(f"   Recall: {best_recall['model_name']} ({best_recall['recall_macro']:.4f})")
    print(f"   F1-Score: {best_f1['model_name']} ({best_f1['f1_macro']:.4f}) ⭐")
    
    print(f"\n💡 Recommendation:")
    print(f"   For imbalanced data, F1-Score (Macro) is the most reliable metric.")
    print(f"   Best overall model: {best_f1['model_name']}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Test with dummy data
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.naive_bayes import MultinomialNB
    
    X, y = make_classification(n_samples=300, n_features=50, n_classes=3, n_informative=30)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
    
    # Make features positive for MultinomialNB
    X_train = np.abs(X_train)
    X_test = np.abs(X_test)
    
    # Create a dummy model wrapper
    class DummyModel:
        def __init__(self):
            self.model_name = "Test Model"
            self.model = MultinomialNB()
            self.model.fit(X_train, y_train)
        
        def predict(self, X):
            return self.model.predict(X)
    
    model = DummyModel()
    result = evaluate_model(model, X_test, y_test)
    
    print(f"\n✅ Evaluation testing passed!")

