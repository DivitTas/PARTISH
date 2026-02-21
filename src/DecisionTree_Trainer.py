import pandas as pd
import numpy as np
import os
import pickle
import spacy
import re
from typing import List, Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# --- Configuration ---
# Models will be saved here
MODEL_DIR = 'models'
MODEL_PATH = os.path.join(MODEL_DIR, 'urgency_model.pkl')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')

# Feature Extraction Settings
TFIDF_MAX_FEATURES = 96  # 100 total - 4 manual features

# Intent to Urgency Mapping
INTENT_URGENCY_MAP = {
    'marketing': 0, 'newsletter': 0, 'social': 0, 'informational': 0,
    'followup': 1, 'support': 1, 'recruiter': 1, 'scheduling': 1, 'invoice': 1,
    'legal': 2, 'investor': 2, 'urgent_deadline': 2
}

# Keyword Dictionaries
VERY_URGENT_TERMS = ["critical", "immediate", "asap", "urgent", "now", "crucial"]
URGENT_TERMS = ["important", "deadline", "soon", "tomorrow", "end of day", "eod", "priority"]
PROMO_TERMS = ["newsletter", "promo", "discount", "offer", "sale", "free"]

# Initialize NLP tools globally for the script
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("Downloading spaCy model 'en_core_web_md'...")
    spacy.cli.download("en_core_web_md")
    nlp = spacy.load("en_core_web_md")

analyzer = SentimentIntensityAnalyzer()

def check_semantic_similarity(text_lower: str, doc, target_words: List[str], threshold: float = 0.7) -> bool:
    """
    Checks for semantic similarity or exact regex match.
    Optimized to use the already processed doc if possible, but mainly uses simple text check + vectors.
    """
    # Fast regex check first
    if any(re.search(r'\b' + re.escape(word) + r'\b', text_lower) for word in target_words):
        return True
    
    # Semantic check
    # Note: iterating through every token for every target word is expensive. 
    # For training, we'll stick to a simplified check or the full check if dataset is small.
    # Given dataset is small (100 items), full check is fine.
    
    for token in doc:
        # filter out stops and punctuation for efficiency
        if token.is_stop or token.is_punct:
            continue
            
        for target_word in target_words:
            if token.has_vector and nlp.vocab[target_word].has_vector:
                if token.similarity(nlp.vocab[target_word]) > threshold:
                    return True
    return False

def extract_manual_features(body: str, subject: str) -> List[float]:
    """
    Extracts the 4 heuristic features:
    1. Sentiment Score
    2. Has Deadline (0 or 1)
    3. Number of Keywords (heuristic count)
    4. Number of Named Entities
    """
    doc = nlp(body)
    body_lower = body.lower()
    
    # 1. Sentiment
    sentiment_score = analyzer.polarity_scores(body)['compound']
    
    # 2. Deadline
    # Check for DATE entities or regex patterns
    has_date_entity = any(ent.label_ == "DATE" for ent in doc.ents)
    has_deadline_regex = bool(re.search(r'(?:deadline|due|by)\s+', body_lower))
    has_deadline = 1.0 if (has_date_entity or has_deadline_regex) else 0.0
    
    # 3. Keywords Count
    # We check each category. If match found, increment 'intensity' counter.
    keyword_intensity = 0.0
    if check_semantic_similarity(body_lower, doc, VERY_URGENT_TERMS):
        keyword_intensity += 1.0
    if check_semantic_similarity(body_lower, doc, URGENT_TERMS):
        keyword_intensity += 1.0
    if check_semantic_similarity(body_lower, doc, PROMO_TERMS):
        keyword_intensity += 1.0
        
    # 4. Num Entities
    num_entities = float(len(doc.ents))
    
    return [sentiment_score, has_deadline, keyword_intensity, num_entities]

def train_decision_tree():
    csv_path = 'dataset/synthetic_emails_500.csv'
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # --- 1. Label Generation ---
    df['urgency_score'] = df['intent'].map(INTENT_URGENCY_MAP).fillna(0)
    y = df['urgency_score'].values
    
    # --- 2. Feature Extraction ---
    print("Extracting NLP features...")
    manual_features = []
    full_texts = []
    
    for index, row in df.iterrows():
        body = str(row.get('body', ''))
        subject = str(row.get('subject', ''))
        
        # Manual features
        feats = extract_manual_features(body, subject)
        manual_features.append(feats)
        
        # Text for TF-IDF
        full_texts.append(f"{subject} {body}")
        
    X_manual = np.array(manual_features)
    
    print("Vectorizing text...")
    vectorizer = TfidfVectorizer(max_features=TFIDF_MAX_FEATURES, stop_words='english')
    X_tfidf = vectorizer.fit_transform(full_texts).toarray()
    
    # Combine
    # Shape: (N_samples, 96 + 4) = (N_samples, 100)
    X = np.hstack([X_tfidf, X_manual])
    
    print(f"Feature matrix shape: {X.shape}")
    
    # --- 3. Split Data ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # --- 4. Train Model ---
    print("Training Decision Tree...")
    clf = DecisionTreeClassifier(max_depth=5, random_state=42)
    clf.fit(X_train, y_train)
    
    # --- 5. Evaluate ---
    print("\n--- Model Evaluation ---")
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.2f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # --- 6. Save Artifacts ---
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    print(f"Saving models to {MODEL_DIR}...")
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(clf, f)
    with open(VECTORIZER_PATH, 'wb') as f:
        pickle.dump(vectorizer, f)
        
    print("Done.")

if __name__ == "__main__":
    train_decision_tree()
