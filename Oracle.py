import ollama
from functools import lru_cache

model_preferences = [  # Ordered by storytelling capability, prove me wrong
    "dolphin-mistral:latest",
    "llama3:70b-text-q2_K",
    "llama3:latest",
    "dolphin-mistral:7b-v2-q3_K_S",
    "gemma:latest",
    "gemma:7b",
    "llama2-uncensored:70b",
    "llama2-uncensored:latest",
    "stablelm2:latest",
    "wizard-vicuna-uncensored:30b",
    "zephyr:latest",
]


@lru_cache(maxsize=1)
def choose_model() -> str:
    print("Choosing model...")
    models = ollama.list()
    local_models = [
        m["name"]
        for m in sorted(
            models["models"], key=lambda m: m["details"]["parameter_size"], reverse=True
        )
    ]

    for choice in model_preferences:
        if choice in local_models:
            print(f"Found preferred model {choice}!")
            return choice
    print(
        "No preferred model available, returning your local model with highes # of parameters."
    )
    return local_models[0]


class Oracle:
    @staticmethod
    def predict(prompt: str, is_json: bool = False) -> tuple[str, str]:
        response = ollama.chat(
            model=choose_model(),
            format="json" if is_json else "",
            messages=[
                {
                    "role": "user",
                    "max_length": 2000,
                    "content": prompt,
                },
            ],
        )
        response: str = response["message"]
        print(f"\n\n\n{prompt}\n -> {response}")
        content = response["content"] if "content" in response else response
        content = content.strip("\n ")
        return content, response
