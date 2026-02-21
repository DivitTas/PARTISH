import re
import spacy
from pydantic import BaseModel, Field
from typing import Optional, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


class EmailAnalysis(BaseModel):
    """
    Represents the sentiment analysis, keyword extraction, and NLP-based entity recognition from an email.
    """
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    urgency_level: str = "Regular"
    keywords: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None
    named_entities: List[str] = Field(default_factory=list) # New field for named entities
    dates: List[str] = Field(default_factory=list) # New field for dates

def analyze_email_sentiment(email_body: str) -> EmailAnalysis:
    """
    Analyzes the email body for sentiment, urgency keywords, deadlines, and named entities using spaCy.
    """
    analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = analyzer.polarity_scores(email_body)

    # Determine sentiment based on compound score
    if sentiment_scores['compound'] >= 0.05:
        sentiment = "positive"
    elif sentiment_scores['compound'] <= -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Urgency keyword detection
    very_urgent_keywords = ["critical", "immediate", "asap", "urgent"] # Added urgent here as well
    urgent_keywords = ["important", "deadline", "soon", "tomorrow"]
    promo_keywords = ["newsletter", "promo", "discount", "offer"]

    found_keywords = []
    urgency_level = "Regular"

    # Use spaCy for more advanced NLP
    doc = nlp(email_body)
    
    named_entities = [ent.text for ent in doc.ents]
    dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]

    # Improve urgency detection using spaCy entities and original keywords
    if any(re.search(r'\b' + word + r'\b', email_body, re.IGNORECASE) for word in very_urgent_keywords):
        urgency_level = "Very Urgent"
        found_keywords.extend(very_urgent_keywords)
    elif any(re.search(r'\b' + word + r'\b', email_body, re.IGNORECASE) for word in urgent_keywords) or any(date for date in dates):
        urgency_level = "Urgent"
        found_keywords.extend(urgent_keywords)
    elif any(re.search(r'\b' + word + r'\b', email_body, re.IGNORECASE) for word in promo_keywords):
        urgency_level = "Newsletter/Promo"
        found_keywords.extend(promo_keywords)
    
    # Basic deadline extraction - can be improved with spaCy date entities
    deadline = next((date for date in dates if "deadline" in email_body.lower() or "by" in email_body.lower()), None)
    if not deadline:
        deadline_match = re.search(r'deadline (is|by) (.*?)(?:\n|$)', email_body, re.IGNORECASE)
        deadline = deadline_match.group(2).strip() if deadline_match else None
    
    analysis = EmailAnalysis(
        sentiment=sentiment,
        sentiment_score=sentiment_scores['compound'],
        urgency_level=urgency_level,
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

    print("--- NLP Analysis Result for Email 1 ---")
    result = analyze_email_sentiment(test_email_1)
    print(result.json(indent=2))

    print("\n--- NLP Analysis Result for Email 2 ---")
    result = analyze_email_sentiment(test_email_2)
    print(result.json(indent=2))

    print("\n--- NLP Analysis Result for Email 3 ---")
    result = analyze_email_sentiment(test_email_3)
    print(result.json(indent=2))
