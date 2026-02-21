import re
import spacy
import pickle
import os
from pydantic import BaseModel, Field
from typing import Optional, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load the spaCy medium model
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("Downloading spaCy model 'en_core_web_md'...")
    # Using spacy.cli.download directly
    spacy.cli.download("en_core_web_md")
    nlp = spacy.load("en_core_web_md")

_clf = None
_vectorizer = None

class EmailAnalysis(BaseModel):
    """
    Represents the sentiment analysis, keyword extraction, and NLP-based entity recognition from an email.
    """
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    urgency_level: str = "Regular"
    ml_urgency_score: Optional[int] = None # Urgency score predicted by ML model
    keywords: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None
    named_entities: List[str] = Field(default_factory=list) # New field for named entities
    dates: List[str] = Field(default_factory=list) # New field for dates

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

def analyze_email_sentiment(email_body: str) -> EmailAnalysis:
    """
    Analyzes the email body for sentiment, urgency keywords, deadlines, and named entities using spaCy.
    """
    global _clf, _vectorizer

    if _clf is None or _vectorizer is None:
        MODEL_PATH = 'models/urgency_model.pkl'
        VECTORIZER_PATH = 'models/vectorizer.pkl'
        if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
            with open(MODEL_PATH, 'rb') as f:
                _clf = pickle.load(f)
            with open(VECTORIZER_PATH, 'rb') as f:
                _vectorizer = pickle.load(f)
        else:
            print("Warning: ML models not found. Skipping ML-based urgency prediction.")
            # We can still proceed with rule-based analysis
            
    analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = analyzer.polarity_scores(email_body)

    # Determine sentiment based on compound score
    if sentiment_scores['compound'] >= 0.05:
        sentiment = "positive"
    elif sentiment_scores['compound'] <= -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Urgency keyword detection (now enhanced with semantic similarity)
    very_urgent_terms = ["critical", "immediate", "asap", "urgent", "now", "crucial"]
    urgent_terms = ["important", "deadline", "soon", "tomorrow", "end of day", "eod", "priority"]
    promo_terms = ["newsletter", "promo", "discount", "offer", "sale", "free"]

    found_keywords = []
    urgency_level = "Regular"

    # Use spaCy for more advanced NLP
    doc = nlp(email_body)
    
    named_entities = [ent.text for ent in doc.ents]
    dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]

    # Improve urgency detection using spaCy entities, original keywords, and semantic similarity
    email_lower = email_body.lower()

    if check_semantic_similarity(email_lower, very_urgent_terms) or \
       any(re.search(r'\b' + word + r'\b', email_lower, re.IGNORECASE) for word in very_urgent_terms):
        urgency_level = "Very Urgent"
        found_keywords.extend(very_urgent_terms)
    elif check_semantic_similarity(email_lower, urgent_terms) or \
         any(re.search(r'\b' + word + r'\b', email_lower, re.IGNORECASE) for word in urgent_terms) or \
         any(date for date in dates): # Any date mentioned increases urgency
        urgency_level = "Urgent"
        found_keywords.extend(urgent_terms)
    elif check_semantic_similarity(email_lower, promo_terms) or \
         any(re.search(r'\b' + word + r'\b', email_lower, re.IGNORECASE) for word in promo_terms):
        urgency_level = "Newsletter/Promo"
        found_keywords.extend(promo_terms)
    
    # Basic deadline extraction - can be improved with spaCy date entities
    # Prioritize spaCy extracted dates for deadline if present and relevant
    deadline = next((d for d in dates if any(keyword in d.lower() for keyword in ["tomorrow", "friday", "monday", "week", "day", "eod"])), None)
    
    if not deadline:
        deadline_match = re.search(r'(?:deadline|due|by)\s+(.*?)(?:\.|\n|$)', email_body, re.IGNORECASE)
        if deadline_match:
            deadline_phrase = deadline_match.group(1).strip()
            # Try to parse the deadline phrase with spaCy for better accuracy
            deadline_doc = nlp(deadline_phrase)
            date_ents = [ent.text for ent in deadline_doc.ents if ent.label_ == "DATE"]
            deadline = date_ents[0] if date_ents else deadline_phrase
    
    # ML-based Urgency Prediction
    ml_urgency_score = None
    if _clf and _vectorizer:
        import numpy as np
        # Text features
        X_text = _vectorizer.transform([email_body]).toarray()
        
        # Heuristic features (must match trainer's order)
        h_features = np.array([[
            sentiment_scores['compound'],
            1 if deadline else 0,
            len(found_keywords),
            len(named_entities)
        ]])
        
        X = np.hstack([X_text, h_features])
        ml_urgency_score = int(_clf.predict(X)[0])
        
        # Override or combine with heuristic urgency
        ml_urgency_map = {0: "Regular", 1: "Urgent", 2: "Very Urgent"}
        urgency_level = ml_urgency_map.get(ml_urgency_score, urgency_level)

    analysis = EmailAnalysis(
        sentiment=sentiment,
        sentiment_score=sentiment_scores['compound'],
        urgency_level=urgency_level,
        ml_urgency_score=ml_urgency_score,
        keywords=found_keywords,
        deadline=deadline,
        named_entities=named_entities,
        dates=dates
    )

    return analysis

if __name__ == '__main__':
    # Example usage with a test email
    test_email_1 = """
    Hi Team,

    This is an URGENT request. We have a critical deadline by Friday. 
    Please prioritize this task. Your immediate attention is required.

    Thanks,
    Management
    """
    
    test_email_2 = """
    Hello, check out our latest newsletter for amazing discounts this week!
    Limited time offer.
    """

    test_email_3 = """
    Just a reminder about the meeting tomorrow morning.
    """

    test_email_4 = """
    Important: Your account will be suspended very soon if no action is taken.
    """

    test_email_5 = """
    Friendly reminder: Your invoice is due by the end of next week.
    """

    print("--- NLP Analysis Result for Email 1 (Very Urgent) ---")
    result = analyze_email_sentiment(test_email_1)
    print(result.json(indent=2))

    print("\n--- NLP Analysis Result for Email 2 (Newsletter/Promo) ---")
    result = analyze_email_sentiment(test_email_2)
    print(result.json(indent=2))

    print("\n--- NLP Analysis Result for Email 3 (Urgent - Tomorrow) ---")
    result = analyze_email_sentiment(test_email_3)
    print(result.json(indent=2))

    print("\n--- NLP Analysis Result for Email 4 (Very Urgent - Semantic) ---")
    result = analyze_email_sentiment(test_email_4)
    print(result.json(indent=2))

    print("\n--- NLP Analysis Result for Email 5 (Urgent - EOD) ---")
    result = analyze_email_sentiment(test_email_5)
    print(result.json(indent=2))