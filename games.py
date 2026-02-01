# utils/games.py
import json
import random

def get_random_quiz(quizzes_file="data/quizzes.json"):
    with open(quizzes_file, "r") as f:
        quizzes = json.load(f)
    return random.choice(quizzes)
