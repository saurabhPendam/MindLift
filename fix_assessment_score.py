def calculate_phq9_score(responses):
    """Calculate PHQ-9 total score from responses"""
    if not responses:
        return 0
    return sum(int(response.get('score', 0)) for response in responses)

def calculate_gad7_score(responses):
    """Calculate GAD-7 total score from responses"""
    if not responses:
        return 0
    return sum(int(response.get('score', 0)) for response in responses)

def save_assessment(assessment_type, responses, user_id):
    """Save assessment with calculated total_score"""
    if assessment_type == 'PHQ-9':
        total_score = calculate_phq9_score(responses)
    elif assessment_type == 'GAD-7':
        total_score = calculate_gad7_score(responses)
    else:
        total_score = 0
    
    # Ensure total_score is not None
    if total_score is None:
        total_score = 0
    
    # Your database INSERT code here with total_score included
    # Example:
    # cursor.execute(
    #     "INSERT INTO assessments (user_id, assessment_type, total_score, responses) VALUES (%s, %s, %s, %s)",
    #     (user_id, assessment_type, total_score, json.dumps(responses))
    # )
