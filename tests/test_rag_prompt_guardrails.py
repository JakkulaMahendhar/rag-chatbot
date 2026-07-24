from app.services.prompt_builder import PromptBuilder


def test_prompt_has_hallucination_rules():

    prompt = PromptBuilder.build(

        question="Explain Kubernetes",

        contexts=[
            "Android services run background operations"
        ]

    )

    assert "Do not use external knowledge" in prompt

    assert (
        "I don't have enough information from the provided documents."
        in prompt
    )