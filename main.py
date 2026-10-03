from src.candidate import Candidate
from src.evaluator import Evaluator

from src.browser_tools import *


def Evaluate():

    # LOAD CANDIDATE PROFIL
    CANDIDATE = Candidate(candidate_yaml=r"candidate.yaml")

    # LOAD EVALUATOR
    EVALUATOR = Evaluator()

    # OFFERS RETRIEVEMENT
    offre_path = r"tests\offre.txt"
    f = open(offre_path, "r", encoding="utf-8")
    OFFER = f.read()

    # OFFER EVALUATION
    eval = EVALUATOR.evaluate_fitting(OFFER, CANDIDATE)
    print(eval)


if __name__ == "__main__":
    Evaluate()
