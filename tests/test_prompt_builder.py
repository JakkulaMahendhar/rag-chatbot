from app.services.prompt_builder import PromptBuilder


def test_rag_prompt_generation():

    prompt = PromptBuilder.build(

        question="What is a background service?",

        contexts=
            "A service is a component that runs in the background to perform long running operations."

    )


    print(prompt)


    assert "Answer only using the provided context" in prompt

    assert "background service" in prompt

    assert "A service is a component" in prompt