import dspy
from textstat import textstat

HISTORY_INTRO = """
This is the story of a Russian princess in Paris for the Exposition Universelle. 
She has been captured by an unknown foe and is restrained in an Hotel Particulier!  
Her prince can't help her, he's become a nihilist who believes in nothing.  
He got drunk and is lost somewhere in Paris... 
She clearly is the stronger one. This is it, she must escape the house and rescue him !
Locked in her room, she packed her belongings in a backpack and starts looking for a way out.
"""
HISTORY_STANDARD = (
    f"This is the story of a lonely princess, locked away in the highest room of a tall castle.\n"
    f"In the tower lives a dragon that guard the castle. "
    f"She was expecting her prince to save her, passing time by reading her various books.\n"
    f"But the poor lad is not a hero and is himself in need of help! She clearly is the stronger one. "
    f"This is it, she must escape the dungeon and rescue him!\n"
    f"Locked in her room, she packed her belongings in a backpack and starts looking for a way out."
)
HISTORY_STANDARD_FULL = (
    f"This is the story of a lonely princess, locked away in the highest room of a tall castle.\n"
    f"In the tower lives a dragon that guard the castle. "
    f"She was expecting her prince to save her, passing time by reading her various books.\n"
    f"But the poor lad is not a hero and is himself in need of help! She clearly is the stronger one. "
    f"This is it, she must escape the dungeon and rescue him!\n"
    f"She was expecting her prince to save her, passing time by reading Simone De Beauvoir.\n"
    f"Yet, when she learned the poor lad spent too much time on 4chan "
    f"and might become a dumb masculinist if nothing is done, she took things in her hands.\n"
    f"This is it, she must rescue him from the patriarchy !\n"
    f"Locked in her room, she packed her belongings in a backpack and starts looking for a way out."
)
ALL_HISTORIES = [HISTORY_INTRO, HISTORY_STANDARD, HISTORY_STANDARD_FULL]

LOCATION = "Starting point"
OBJECTIVE = "Escape then save the prince"
f"Return a JSON object describing her current situation. "
f"You must include at top-level a 'short_description' under 20 words and a 'long_description' under 100 words."

TASK_SITUATION = ("determine the current situation of the princess."
                  "Return a JSON object describing her current situation. You must include at top-level "
                  "a 'short_description' under 20 words and a 'long_description' under 100 words."
                  )
TASK_LOCATION = ("determine the current location of the princess."
                 "Where is the princess? Reply in a few words. Examples: \"In the wine cellar\", "
                 "or \"On the roof under strong winds\", or \"In the kitchen\"."
                 "Return a JSON object describing her current location. You must include at top-level "
                 "a 'short_description' under 20 words and a 'long_description' under 100 words."
                 )
TASK_GOAL = ("determine the current goal of the princess."
             "What is the short-term goal of the princess? Reply in a few words. "
             "Examples: \"Getting out of the room\", or \"Opening the treasure chest\", or \"Solving the enigma\".\n")
ALL_TASKS = [TASK_SITUATION, TASK_LOCATION, TASK_GOAL]
dev_raw = [[(history, LOCATION, OBJECTIVE, task)]
           for task in ALL_TASKS
           for history in ALL_HISTORIES
           ]
print(f"Loaded dataset with {len(dev_raw)} samples.")

dev = [dspy.Example(story=story, location=location, objective=objective, task=task)
       .with_inputs("story", "location", "objective", "task")
       for raw in dev_raw for (story, location, objective, task) in raw]


def my_copro():
    lm = dspy.OllamaLocal(model='dolphin-mistral:latest')
    dspy.settings.configure(lm=lm, bypass_suggest=True)

    class NarratorSignature(dspy.Signature):
        """
        You generate short story bits in simple english and write compelling adventure games
        made of few-sentence descriptions and actions.
        You must always refer to the main character as the princess or she,
        and always describe the scene in her third person subjective voice.
        When possible you use simple words from the basic english vocabulary to keep the story readable for kids.
        """

        # Inputs
        story = dspy.InputField(desc="The story so far")
        location = dspy.InputField(desc="The heroin's current location")
        objective = dspy.InputField(desc="The heroin's current objective")
        task = dspy.InputField(desc="A task to execute to based on the current story.")
        # Outputs
        answer = dspy.OutputField(desc="often between 5 and 10 words.")

    class CoTPipeline(dspy.Module):
        def __init__(self):
            super().__init__()

            self.signature = NarratorSignature
            self.predictor = dspy.ChainOfThought(self.signature)

        def forward(self, story, location, objective, task):
            result = self.predictor(story=story, location=location, objective=objective, task=task)

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

    from dspy.evaluate import Evaluate

    def validate_readable(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
        """ True if the text is at least fairly easy to read.

        Returns:
            A normalized (0.0-1.0) Flesch score.
        """
        return textstat.flesch_reading_ease(pred.answer.lower()) / 100

    def validate_short(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
        """ True if the text is quick to read.

        Returns:
            An inverted reading time in seconds:
            0s = 100
            1s = 90s
            10s = 0
            20s = -100
        """
        return (100 - (10 * textstat.reading_time(pred.answer.lower()))) / 100

    NUM_THREADS = 5
    print("Evaluating raw COT model..")
    evaluate = Evaluate(devset=dev, metric=validate_short, num_threads=NUM_THREADS,
                        display_progress=True, display_table=False)
    cot_baseline = CoTPipeline()

    devset_with_input = [dspy.Example(
        {key: r[key] for key in ["story", "location", "objective", "task"]}
    ).with_inputs("story", "location", "objective", "task") for r in dev]
    evaluate(cot_baseline, devset=devset_with_input)

    from dspy.teleprompt import COPRO

    optimizer = COPRO(
        metric=validate_readable,
        depth=5,
        verbose=True,
    )

    kwargs = dict(num_threads=64, display_progress=True,
                  display_table=0)  # Used in Evaluate class in the optimization process

    print(f"Running COPRO prompt optimizer! Depth={optimizer.depth}, model={optimizer.prompt_model}")
    compiled_prompt_opt: CoTPipeline = optimizer.compile(cot_baseline, trainset=dev, eval_kwargs=kwargs)
    compiled_prompt_opt.save("compiled_cot.json")
    print("Saved compiled model as compiled_cot.json! Evaluating...")
    evaluate(compiled_prompt_opt, devset=devset_with_input)

    input("Do you want to continue?")
    loaded_program = CoTPipeline()
    loaded_program.load(path="compiled_cot.json")

    # raw = dev_raw[0]
    # love = compiled_prompt_opt.forward(story=raw[0], location=raw[1], objective=raw[1], task=raw[3])
    # print(love)
    #
    # # Once the training is done you'll have better instructions and prefixes that you'll need to edit in signature
    # # manually. So let's say the output during optimization is like:
    #  You generate short story bits in simple english and write compelling adventure games
    #         made of few-sentence descriptions and actions.
    #         You must always refer to the main character as the princess or she,
    #         and always describe the scene in her third person subjective voice.
    #         When possible you use simple words from the basic english vocabulary to keep the story readable for kids.
    # You can then update your optimized module:
    # class NarratorSignatureNew(dspy.Signature):
    #     """ You generate short story bits in simple english and write compelling adventure games
    #         made of few-sentence descriptions and actions.
    #         You must always refer to the main character as the princess or she,
    #         and always describe the scene in her third person subjective voice.
    #         When possible you use simple words from the basic english vocabulary to keep the story readable for kids.
    #     """
    #
    #     # Inputs
    #     story = dspy.InputField(desc="The story so far")
    #     location = dspy.InputField(desc="The heroin's current location")
    #     objective = dspy.InputField(desc="The heroin's current objective")
    #     task = dspy.InputField(desc="A task to execute to based on the current story.")
    #     # Outputs
    #     answer = dspy.OutputField(desc="often between 5 and 10 words.")
    # Reinitialize the Pipeline object and reevaluate the pipeline!
    # And now you have a more powerful predictor with more optimized Signature!


if __name__ == '__main__':
    # main_copro()
    my_copro()
