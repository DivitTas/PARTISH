import re
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import pandas as pd
import pickle
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import numpy as np
from typing import List

# Load the spaCy medium model
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("Downloading spaCy model 'en_core_web_md'...")
    spacy.cli.download("en_core_web_md")
    nlp = spacy.load("en_core_web_md")

# Initialize VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Mapping intents to urgency scores (0: Regular, 1: Urgent, 2: Very Urgent)
INTENT_URGENCY_MAP = {
    'marketing': 0,
    'newsletter': 0,
    'social': 0,
    'informational': 0,
    'followup': 1,
    'support': 1,
    'recruiter': 1,
    'scheduling': 1,
    'invoice': 1,
    'legal': 2,
    'investor': 2,
    'urgent_deadline': 2
}

def check_semantic_similarity(text: str, target_words: List[str], threshold: float = 0.7) -> bool:
    """
    Checks if the given text has semantic similarity with any of the target words.
    Requires a spaCy model with word vectors (e.g., en_core_web_md or lg).
    """
    doc = nlp(text.lower())
    for token in doc:
        for target_word in target_words:
            if token.has_vector and nlp.vocab[target_word].has_vector:
                if token.similarity(nlp.vocab[target_word]) > threshold:
                    return True
    return False

def train_decision_tree():
    csv_path = 'dataset/synthetic_emails_100.csv'
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)
    
    # Feature extraction using direct NLP logic
    print("Extracting features using direct NLP...")
    features = []

    # Define terms for keyword extraction (from JSON_Extracter)
    very_urgent_terms = ["critical", "immediate", "asap", "urgent", "now", "crucial"]
    urgent_terms = ["important", "deadline", "soon", "tomorrow", "end of day", "eod", "priority"]
    promo_terms = ["newsletter", "promo", "discount", "offer", "sale", "free"]
    
    for _, row in df.iterrows():
        email_body = row['body']
        doc = nlp(email_body)
        email_lower = email_body.lower()

        # Sentiment Score
        sentiment_scores = analyzer.polarity_scores(email_body)
        sentiment_score = sentiment_scores['compound']

        # Has Deadline (simplified for training)
        has_deadline = 1 if any(ent.label_ == "DATE" for ent in doc.ents) or \
                            re.search(r'(?:deadline|due|by)', email_lower, re.IGNORECASE) else 0

        # Number of Keywords
        found_keywords_count = 0
        if check_semantic_similarity(email_lower, very_urgent_terms) or \
           any(re.search(r'\b' + word + r'\b', email_lower, re.IGNORECASE) for word in very_urgent_terms):
            found_keywords_count += 1
        if check_semantic_similarity(email_lower, urgent_terms) or \
           any(re.search(r'\b' + word + r'\b', email_lower, re.IGNORECASE) for word in urgent_terms):
            found_keywords_count += 1
        if check_semantic_similarity(email_lower, promo_terms) or \
           any(re.search(r'\b' + word + r'\b', email_lower, re.IGNORECASE) for word in promo_terms):
            found_keywords_count += 1

        # Number of Entities
        num_entities = len(doc.ents)

        features.append({
            'sentiment_score': sentiment_score,
            'has_deadline': has_deadline,
            'num_keywords': found_keywords_count,
            'num_entities': num_entities
        })
    
    df_features = pd.DataFrame(features)
    
    # Text features
    df['full_text'] = df['subject'] + " " + df['body']
    vectorizer = TfidfVectorizer(max_features=96, stop_words='english')
    X_text = vectorizer.fit_transform(df['full_text']).toarray()
    
    # Combine all features
    X = np.hstack([X_text, df_features.values])
    
    # Label
    df['urgency_score'] = df['intent'].map(INTENT_URGENCY_MAP).fillna(0)
    y = df['urgency_score'].values

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Train Decision Tree
    clf = DecisionTreeClassifier(max_depth=5, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate the model
    y_pred = clf.predict(X_test)
    print("\nModel Evaluation:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save the model and vectorizer
    model_dir = 'models'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        
    with open(os.path.join(model_dir, 'urgency_model.pkl'), 'wb') as f:
        pickle.dump(clf, f)
    with open(os.path.join(model_dir, 'vectorizer.pkl'), 'wb') as f:
        pickle.dump(vectorizer, f)
        
    print("Enhanced Decision Tree model and vectorizer saved to 'models/' directory.")

if __name__ == "__main__":
    train_decision_tree()
