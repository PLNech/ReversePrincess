from abc import ABC

import dspy
from dspy import Signature
from textstat import textstat


class StorySignature(Signature, ABC):
    # Inputs
    answer = dspy.OutputField(desc="often between 5 and 50 words.")
    objective = dspy.InputField(desc="The heroin's current objective")
    location = dspy.InputField(desc="The heroin's current location")
    # task = dspy.InputField(desc="A task to execute to based on the current story.")

    # Outputs
    story = dspy.InputField(desc="The story so far")


class LocatorSignature(StorySignature):
    # V1:
    # """
    # You must determine the current location of the princess.
    # Where is the princess? Reply in a few words. Examples: \"In the wine cellar\",
    # or \"On the roof under strong winds\", or \"In the kitchen\".
    # Return a JSON object describing her current location. You must include at top-level
    # a 'short_description' under 20 words and a 'long_description' under 100 words.
    # """

    # V2 Optimized with COPRO:
    """
    You must determine the current situation of the princess.
    Return a JSON object describing her current situation. You must include at top-level
    'short_description' under 20 words and a 'long_description' under 100 words.
    """


class SituatorSignature(StorySignature):
    """
    You must determine the current situation of the princess.
    Return a JSON object describing her current situation. You must include at top-level
    'short_description' under 20 words and a 'long_description' under 100 words.
    """


class CoTPipeline(dspy.Module):
    def __init__(self, signature: type[dspy.Signature]):
        super().__init__()

        self.signature = signature
        self.predictor = dspy.ChainOfThought(self.signature)

    def forward(self, story, location, objective):
        result = self.predictor(story=story, location=location, objective=objective)

        whitelist = ["short_description", "long_description"]
        bad_words = textstat.difficult_words_list(result.answer, 3)
        bad_words = [w for w in bad_words if w not in whitelist]

        dspy.Suggest(
            len(bad_words) <= 5,
            msg=f"Answer should have less complicated words, such as {','.join(bad_words)}",
        )

        return dspy.Prediction(
            answer=result.answer,
            reasoning=result.rationale,
        )


if __name__ == "__main__":
    print("Example usage of optimized Locator:")
    model = CoTPipeline(LocatorSignature)
    model.forward("")
