# PARTISH
An AI helper that prioritizes mails on urgency, with notification support for extremely urgent mails, and integration with your favourite workflows like notion.
It stands for Personal Assistant for Random Trivial Inbox Supplemental Helper.
PS. This is also a homage to our good friend Partish. 

## Project Structure
- `src/gmail_access.py`: Handles Gmail API authentication and fetching.
- `src/DecisionTree_Trainer.py`: Independent script to train the Decision Tree model for urgency classification. It saves the trained model and vectorizer to `models/`.
- `src/JSON_Extracter.py`: Core logic for analyzing email content. Uses NLP (spaCy + Vader) and the trained Decision Tree model (loaded lazily) to predict urgency and extract metadata.
- `src/data_generator.py`: Generates synthetic email data (`dataset/synthetic_emails_500.csv`) for model training.
- `dataset/`: Contains synthetic training data (`synthetic_emails_100.csv` and `synthetic_emails_500.csv`).
- `models/`: Directory where trained models (`urgency_model.pkl`, `vectorizer.pkl`) are saved (ignored by git).

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Download spaCy model: `python -m spacy download en_core_web_md`

## Usage
1. **Train the Model:**
   ```bash
   python src/DecisionTree_Trainer.py
   ```
   This will generate `models/urgency_model.pkl` and `models/vectorizer.pkl`.

2. **Run Analysis (for Test Emails in JSON_Extracter.py):**
   You can test the extraction logic directly on predefined examples:
   ```bash
   python src/JSON_Extracter.py
   ```

3. **Analyze a Custom Email:**
   To analyze a single email you provide:
   1. Open `src/analyze_my_email.py` and modify `your_email_subject` and `your_email_body` variables.
   2. Run the script:
      ```bash
      python src/analyze_my_email.py
      ```

