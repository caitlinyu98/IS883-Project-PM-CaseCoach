"""Keep every submission, grouped by question rather than counting retries as questions."""
def record_submission(transcript, question, question_index, answer, followup=False):
    if followup:
        turn = transcript[-1]
        field = 'follow_up_answer'
    else:
        if not transcript or transcript[-1].get('question_index') != question_index:
            transcript.append(dict(question=question, question_index=question_index, answer=''))
        turn = transcript[-1]
        field = 'answer'
    attempts = turn.setdefault(field + '_submissions', [])
    attempts.append(answer)
    # Keep originals, in order; never replace an early or off-topic submission.
    turn[field] = '\n\n'.join(attempts)
    return turn
