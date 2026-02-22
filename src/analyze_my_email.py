from src.JSON_Extracter import analyze_email_sentiment
import json
import os

# Ensure models are trained and available
MODEL_PATH = 'models/urgency_model.pkl'
VECTORIZER_PATH = 'models/vectorizer.pkl'

if not (os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH)):
    print("Warning: Trained models not found. Please run src/DecisionTree_Trainer.py first to train the model.")
    print("Proceeding with rule-based analysis only (no ML predictions).")

# --- Example Email Content ---
# Replace these with the subject and body of any email you want to analyze.
your_email_subject = "Example Subject for Analysis"
your_email_body = "This is an example email body. It contains some text that can be analyzed for sentiment and urgency."

# Combine subject and body for analysis, as the model was trained on both.
email_to_analyze = your_email_subject + " " + your_email_body

print(f"Analyzing email with subject: '{your_email_subject}'")

# Run the analysis
analysis_result = analyze_email_sentiment(email_to_analyze)

# Print the results in a readable JSON format
print("
--- Analysis Result ---")
print(json.dumps(analysis_result.dict(), indent=2))
