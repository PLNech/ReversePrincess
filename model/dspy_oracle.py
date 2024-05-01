import dspy
from dspy.evaluate import answer_exact_match, Evaluate
from dspy.teleprompt import BootstrapFewShot


class BasicOracle(dspy.Signature):
    """Generate content from a simple prompt."""

    prompt = dspy.InputField()
    response = dspy.OutputField(desc="often between 1 and 5 words")


class CoT(dspy.Module):  # let's define a new module
    def __init__(self):
        super().__init__()

        # here we declare the chain of thought sub-module, so we can later compile it (e.g., teach it a prompt)
        self.generate_answer = dspy.ChainOfThought('question -> answer')

    def forward(self, question):
        return self.generate_answer(question=question)  # here we use the module


INTRO_OPTIONS = "The year is 1900 and the whole western world is delighted by the Paris _Exposition Universelle_. " \
                "But you are a princess, and you're imprisoned by a bad guy in a Hotel Particulier in Paris!" \
                "And worse, your beloved prince got trapped - he doesn't seem so good at saving anyone, even his ass. " \
                "Can you escape the castle to go rescue this cute loser?" \
                "\n You start your journey in the following room:" \
                " The story starts with just three options of rooms in the castle where the princess could be locked in."


def main_dspy():
    print("Hello DSPY :)")
    # With local Ollama
    lm = dspy.OllamaLocal(model='dolphin-mistral:latest')

    # Configure with their Retrieval Model based on wiki abstracts
    colbertv2_wiki17_abstracts = dspy.ColBERTv2(url='http://20.102.90.50:2017/wiki17_abstracts')
    dspy.settings.configure(lm=lm, rm=colbertv2_wiki17_abstracts)

    # Define the predictor.
    generate_answer = dspy.Predict(BasicOracle)

    prompt = (INTRO_OPTIONS)
    # Call the predictor on a particular input.
    pred = generate_answer(prompt=prompt)

    # Print the input and the prediction.
    print(f"Question: {prompt}")
    print(f"Gen response: {pred.response}")

    train = [
        ('In what year was the star of To Hell and Back born?', '1925'),
        # ('Which award did the first book of Gary Zukav receive?', 'U.S. National Book Award'),
        ('What documentary about the Gilgo Beach Killer debuted on A&E?', 'The Killing Season'),
        # ('Which author is English: John Braine or Studs Terkel?', 'John Braine'),
        # ('Who produced the album that included a re-recording of "Lithium"?', 'Butch Vig')
    ]

    train = [dspy.Example(question=question, answer=answer).with_inputs('question') for question, answer in train]

    # https://github.com/stanfordnlp/dspy/blob/main/skycamp2023.ipynb
    dev = [('Who has a broader scope of profession: E. L. Doctorow or Julia Peterkin?', 'E. L. Doctorow'),
           ('Right Back At It Again contains lyrics co-written by the singer born in what city?',
            'Gainesville, Florida'),
           ('What year was the party of the winner of the 1971 San Francisco mayoral election founded?', '1828'),
           ('Anthony Dirrell is the brother of which super middleweight title holder?', 'Andre Dirrell'),
           ('The sports nutrition business established by Oliver Cookson is based in which county in the UK?',
            'Cheshire'),
           ('Find the birth date of the actor who played roles in First Wives Club and Searching for the Elephant.',
            'February 13, 1980'),
           ('Kyle Moran was born in the town on what river?', 'Castletown River'),
           ("The actress who played the niece in the Priest film was born in what city, country?", 'Surrey, England'),
           ('Name the movie in which the daughter of Noel Harrison plays Violet Trefusis.', 'Portrait of a Marriage'),
           ('What year was the father of the Princes in the Tower born?', '1442'),
           ('What river is near the Crichton Collegiate Church?', 'the River Tyne'),
           ('Who purchased the team Michael Schumacher raced for in the 1995 Monaco Grand Prix in 2000?', 'Renault'),
           (
               'André Zucca was a French photographer who worked with a German propaganda magazine published by what Nazi organization?',
               'the Wehrmacht')]

    dev = [dspy.Example(question=question, answer=answer).with_inputs('question') for question, answer in dev]

    metric_EM = answer_exact_match
    metric_similarity = answer_exact_match

    teleprompter = BootstrapFewShot(metric=metric_EM, max_bootstrapped_demos=2)
    cot_compiled = teleprompter.compile(CoT(), trainset=train)

    cot_compiled("What is the capital of Germany?")

    lm.inspect_history(n=1)

    evaluate_hotpot = Evaluate(devset=dev, metric=metric_EM, num_threads=32, display_progress=True, display_table=15)

    evaluate_hotpot(cot_compiled)


if __name__ == '__main__':
    print("YO Pythonista")
    main_dspy()
