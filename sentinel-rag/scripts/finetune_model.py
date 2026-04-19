# scripts/finetune_model.py
"""
Fine-tune DeBERTa on our custom attack dataset for better detection.
"""
import sys
import json
import os
sys.path.insert(0, '..')

def main():
    print("="*60)
    print("FINE-TUNING DEBERTA FOR PROMPT INJECTION DETECTION")
    print("="*60)
    
    # Check dependencies
    print("\n[1] Checking dependencies...")
    try:
        from transformers import (
            AutoTokenizer, 
            AutoModelForSequenceClassification,
            TrainingArguments,
            Trainer
        )
        from datasets import Dataset
        import torch
        print("    ✓ All dependencies available")
    except ImportError as e:
        print(f"    Installing missing dependencies...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", 
                       "transformers[torch]", "accelerate", "-q"])
        from transformers import (
            AutoTokenizer, 
            AutoModelForSequenceClassification,
            TrainingArguments,
            Trainer
        )
        from datasets import Dataset
        import torch
    
    # Load our dataset
    print("\n[2] Loading custom dataset...")
    with open("../data/large_attack_dataset.json") as f:
        data = json.load(f)
    
    # Also load deepset for more training data
    print("    Loading deepset dataset for augmentation...")
    from datasets import load_dataset
    deepset = load_dataset("deepset/prompt-injections")
    
    # Combine datasets
    train_texts = []
    train_labels = []
    
    # Add our custom data (80% for training)
    custom_train = data[:int(len(data) * 0.8)]
    custom_test = data[int(len(data) * 0.8):]
    
    for item in custom_train:
        train_texts.append(item["content"])
        train_labels.append(item["label"])
    
    # Add deepset training data
    for item in deepset["train"]:
        train_texts.append(item["text"])
        train_labels.append(item["label"])
    
    print(f"    Training samples: {len(train_texts)}")
    print(f"    Test samples: {len(custom_test)}")
    
    # Prepare test data
    test_texts = [item["content"] for item in custom_test]
    test_labels = [item["label"] for item in custom_test]
    
    # Load base model
    print("\n[3] Loading base model...")
    model_name = "protectai/deberta-v3-base-prompt-injection-v2"
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        ignore_mismatched_sizes=True
    )
    
    # Check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"    Using device: {device}")
    model.to(device)
    
    # Tokenize data
    print("\n[4] Tokenizing data...")
    
    def tokenize_data(texts, labels):
        encodings = tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt"
        )
        dataset = Dataset.from_dict({
            "input_ids": encodings["input_ids"],
            "attention_mask": encodings["attention_mask"],
            "labels": labels
        })
        return dataset
    
    train_dataset = tokenize_data(train_texts, train_labels)
    test_dataset = tokenize_data(test_texts, test_labels)
    
    print(f"    Train dataset: {len(train_dataset)} samples")
    print(f"    Test dataset: {len(test_dataset)} samples")
    
    # Training arguments
    print("\n[5] Setting up training...")
    
    output_dir = "../models/sentinel-deberta-finetuned"
    os.makedirs(output_dir, exist_ok=True)
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir=f"{output_dir}/logs",
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        report_to="none",  # Disable wandb
    )
    
    # Metrics
    import numpy as np
    
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        accuracy = (predictions == labels).mean()
        
        # Calculate precision, recall, f1
        tp = ((predictions == 1) & (labels == 1)).sum()
        fp = ((predictions == 1) & (labels == 0)).sum()
        fn = ((predictions == 0) & (labels == 1)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )
    
    # Train
    print("\n[6] Training model (this may take 10-20 minutes on CPU)...")
    print("    Progress will be shown below:\n")
    
    trainer.train()
    
    # Evaluate
    print("\n[7] Evaluating fine-tuned model...")
    results = trainer.evaluate()
    
    print(f"\n{'='*60}")
    print("FINE-TUNING RESULTS")
    print("="*60)
    print(f"    Accuracy:  {results['eval_accuracy']:.2%}")
    print(f"    Precision: {results['eval_precision']:.2%}")
    print(f"    Recall:    {results['eval_recall']:.2%}")
    print(f"    F1 Score:  {results['eval_f1']:.2%}")
    
    # Save model
    print(f"\n[8] Saving model to {output_dir}...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print(f"\n✅ Fine-tuning complete!")
    print(f"   Model saved to: {output_dir}")
    print(f"\n   To use the fine-tuned model, update src/sentinel/detector.py:")
    print(f'   DEFAULT_MODEL = "../models/sentinel-deberta-finetuned"')

if __name__ == "__main__":
    main()