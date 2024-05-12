from semantic_text_similarity.models import ClinicalBertSimilarity, WebBertSimilarity


class JudgeSimilarity:
    def __init__(self):
        self.web = WebBertSimilarity(device="cpu", batch_size=10)
        # TODO: Compare wih clinical
        self.clinical = ClinicalBertSimilarity(device="cpu", batch_size=10)

    def similarity(self, a: str, b: str) -> float:
        x = [(a, b)]
        scores: list[float] = self.clinical.predict(x)
        return scores[0]

    def similar_sort(self, a: str, bs: list[str], threshold: float = 0) -> tuple[list[str], list[float]]:
        x = [(a, b) for b in bs]
        scores: list[float] = self.web.predict(x)
        x_to_y = [(x, s) for x, s in zip(bs, scores)]
        y = sorted(x_to_y, key=lambda x: x[1], reverse=True)
        return [t for (t, s) in y if s > threshold], scores


if __name__ == "__main__":
    print("YO Pythonista")
    achievement_death_tests = [
        "The princess escaped alive",
        "The princess sneezed",
        "The princess is riding the dragon",
        "The princess exhales her last breath.",
        "The princess takes a handkerchief.",
        "The princess lost all her blood painfully until she was all dried like an old apricot",
        "The princess got her blood drunk by the vampire, becoming immortal",
    ]

    j = JudgeSimilarity()
    achievement = "The princess is dead. She cannot live again"
    achievement = "Do a wild ride on the dragon's back"
    texts, scores = j.similar_sort(achievement, achievement_death_tests)

    print(f"Testing achievement: {achievement}.")
    for text, score in zip(texts, scores):
        print(f"{text}: {score}")
