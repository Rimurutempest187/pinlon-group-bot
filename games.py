import json
from config import QUIZZES_FILE

def get_random_quiz():
    with open(QUIZZES_FILE, "r") as f:
        quizzes = json.load(f)
    import random
    return random.choice(quizzes)
