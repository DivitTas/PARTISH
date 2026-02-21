from JSON_Extracter import analyze_email

def test_analyze():
    email_body = """
    From: manager@example.com
    To: dev@example.com
    Subject: Deadline for PARTISH project

    Hi Team,

    Just a reminder that the deadline for the PARTISH project is in 24 hours.
    Please ensure all tests are passing and the code is documented.
    We need to submit the final report by then.

    Thanks,
    Manager
    """
    print("Analyzing email...")
    result = analyze_email(email_body)
    if result:
        print("Analysis successful!")
        print(result.model_dump_json(indent=2))
    else:
        print("Analysis failed.")

if __name__ == "__main__":
    test_analyze()
