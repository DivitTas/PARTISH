import re
from pydantic import BaseModel, Field
from typing import Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class EmailAnalysis(BaseModel):
    """
    Represents the sentiment analysis and keyword extraction from an email.
    """
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    urgency_level: str = "Regular"
    keywords: list[str] = Field(default_factory=list)
    deadline: Optional[str] = None

def analyze_email_sentiment(email_body: str) -> EmailAnalysis:
    """
    Analyzes the email body for sentiment, urgency keywords, and deadlines.
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
    very_urgent_keywords = ["critical", "immediate", "asap"]
    urgent_keywords = ["urgent", "important", "deadline"]
    promo_keywords = ["newsletter", "promo", "discount", "offer"]

    found_keywords = []
    urgency_level = "Regular"

    if any(re.search(r'\b' + word + r'\b', email_body, re.IGNORECASE) for word in very_urgent_keywords):
        urgency_level = "Very Urgent"
        found_keywords.extend(very_urgent_keywords)
    elif any(re.search(r'\b' + word + r'\b', email_body, re.IGNORECASE) for word in urgent_keywords):
        urgency_level = "Urgent"
        found_keywords.extend(urgent_keywords)
    elif any(re.search(r'\b' + word + r'\b', email_body, re.IGNORECASE) for word in promo_keywords):
        urgency_level = "Newsletter/Promo"
        found_keywords.extend(promo_keywords)

    # Basic deadline extraction
    deadline_match = re.search(r'deadline (is|by) (.*?)(?:\n|$)', email_body, re.IGNORECASE)
    deadline = deadline_match.group(2).strip() if deadline_match else None
    
    analysis = EmailAnalysis(
        sentiment=sentiment,
        sentiment_score=sentiment_scores['compound'],
        urgency_level=urgency_level,
        keywords=found_keywords,
        deadline=deadline
    )

    return analysis

if __name__ == '__main__':
    # Example usage with a test email
    test_email = """
    Hi Team,

    This is an URGENT request. We have a critical deadline by Friday. 
    Please prioritize this task. Your immediate attention is required.

    Thanks,
    Management
    """
    
    result = analyze_email_sentiment(test_email)
    print("--- NLP Analysis Result ---")
    print(result.model_dump_json(indent=2))
