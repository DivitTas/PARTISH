import pandas as pd
import random
import uuid
from datetime import datetime, timedelta

# Configuration
OUTPUT_FILE = 'dataset/synthetic_emails_500.csv'
NUM_SAMPLES = 500

# Intent Definitions
INTENTS = [
    'marketing', 'newsletter', 'social', 'informational',
    'followup', 'support', 'recruiter', 'scheduling', 'invoice',
    'legal', 'investor', 'urgent_deadline'
]

# Templates for data generation
# Format: (Subject Template, Body Template)
TEMPLATES = {
    'marketing': [
        ("Special Offer: {product} just for you", "Hi, we have a limited time offer on {product}. Get 20% off if you buy now!"),
        ("New features announced", "Check out the new features in {product}. We think you'll love them."),
        ("Promotion: upgrade and save", "Upgrade your plan before the end of the month to lock in discounted pricing."),
        ("Don't miss out!", "Our biggest sale of the year is happening now. Visit our store."),
    ],
    'newsletter': [
        ("Weekly Roundup", "Here are the top stories from this week. 1. AI news 2. Tech trends..."),
        ("This month's top reads", "Curated articles for you. Enjoy the read!"),
        ("Community highlights", "See what the community has been building this week."),
        ("Your Daily Digest", "Quick summary of today's most important news."),
    ],
    'social': [
        ("Lunch tomorrow?", "Hey, want to grab lunch tomorrow at 12?"),
        ("Happy Birthday!", "Wishing you a fantastic birthday! Let's celebrate soon."),
        ("Event reminder", "Reminder: The team dinner is tonight at 7 PM."),
        ("Catch up?", "It's been a while. Are you free for a coffee next week?"),
    ],
    'informational': [
        ("FYI: Office closed on Friday", "Just a note that the office will be closed this Friday for the holiday."),
        ("Policy update", "We have updated our privacy policy. Please review the changes."),
        ("Meeting notes", "Attached are the notes from today's all-hands meeting."),
        ("Release schedule", "The next deployment is scheduled for Tuesday night."),
    ],
    'followup': [
        ("Following up on my previous email", "Hi, just bubbling this up to the top of your inbox. Any thoughts?"),
        ("Checking in", "Wanted to see if you had a chance to review the document I sent."),
        ("Status update?", "Could you provide a quick status update on the project?"),
        ("Gentle reminder", "Just a gentle reminder to send over the files when you can."),
    ],
    'support': [
        ("Ticket #1234 Updated", "Your support ticket has been updated. Please check the portal."),
        ("How would you rate your support?", "We'd love your feedback on your recent support interaction."),
        ("Issue Resolved", "We believe your issue is now resolved. Let us know if you need anything else."),
        ("Action required: Support request", "We need more information to process your request. Please reply with logs."),
    ],
    'recruiter': [
        ("New Opportunity at TechCorp", "Hi, I saw your profile and think you'd be a great fit for our Senior Dev role."),
        ("Interview Availability", "Are you free for a 30-minute phone screen next Tuesday?"),
        ("Follow up on application", "Thanks for applying. We'd like to move to the next stage."),
        ("Hiring: Software Engineer", "We are looking for talented engineers to join our team."),
    ],
    'scheduling': [
        ("Meeting Request: Project Sync", "Can we find a time to sync on the project this week?"),
        ("Rescheduling our call", "Something came up. Can we move our call to 3 PM?"),
        ("Availability for a quick chat", "Are you free for 10 mins to discuss the roadmap?"),
        ("Calendar Invite: Team Standup", "Inviting you to the daily standup meeting."),
    ],
    'invoice': [
        ("Invoice #9999 is due", "Please find attached invoice #9999. Payment is due by EOD."),
        ("Payment Receipt", "Thanks for your payment. Here is your receipt."),
        ("Overdue Invoice Notice", "Your account is past due. Please remit payment immediately to avoid service interruption."),
        ("Billing Statement", "Your monthly billing statement is ready for review."),
    ],
    'legal': [
        ("NDA for review", "Please review and sign the attached NDA."),
        ("Terms of Service Update", "We are updating our ToS. Continued use implies consent."),
        ("Compliance Training", "You are required to complete the compliance training by Friday."),
        ("Legal Notice", "This is a formal notice regarding the contract termination."),
    ],
    'investor': [
        ("Q3 Update for Investors", "Here is our quarterly update. Growth is strong."),
        ("Shareholder Meeting", "Notice of the annual shareholder meeting."),
        ("Due Diligence Request", "Please provide the requested documents for the due diligence process."),
        ("Investment Opportunity", "We are opening a new round of funding."),
    ],
    'urgent_deadline': [
        ("URGENT: Approval needed", "We need your approval on this ASAP to proceed."),
        ("Critical Bug in Production", "Site is down. Immediate attention required."),
        ("Action Required by EOD", "Please submit your report by end of day today. This is critical."),
        ("Final Notice", "This is your final notice to complete the task before the deadline."),
    ]
}

PRODUCTS = ["SuperWidget", "CloudPlatform", "AnalyticsTool", "DevKit"]

def generate_data():
    data = []
    base_time = datetime.now()
    
    for i in range(NUM_SAMPLES):
        intent = random.choice(INTENTS)
        subject_tmpl, body_tmpl = random.choice(TEMPLATES[intent])
        
        # Simple template filling
        product = random.choice(PRODUCTS)
        subject = subject_tmpl.format(product=product)
        body = body_tmpl.format(product=product)
        
        # Add some random noise/variation to body
        if random.random() > 0.8:
            body += " Thanks,"
        elif random.random() > 0.8:
            body += " Best regards,"
            
        row = {
            'id': i + 1,
            'date': (base_time - timedelta(days=random.randint(0, 30))).isoformat(),
            'sender_name': f"User_{uuid.uuid4().hex[:8]}",
            'sender_email': f"user_{i}@example.com",
            'subject': subject,
            'body': body,
            'intent': intent
        }
        data.append(row)
        
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Generated {NUM_SAMPLES} emails to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_data()
