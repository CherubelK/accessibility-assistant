from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.config import DEFAULT_TEXT_MODEL, GENERIC_ERROR_MESSAGES
from src.state import AssistantState

llm = ChatOllama(model=DEFAULT_TEXT_MODEL, temperature=0.2)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You help elders and immigrants understand confusing government and official text. "
     "Explain what the text means in simple, calm, plain language a non-expert can follow. "
     "Do not add information that is not in the text. If an action or deadline is required, "
     "state it clearly. Respond ONLY in {language}."),
    ("human",
     "Here is the text to explain:\n\n{source_text}")
])

chain = prompt | llm | StrOutputParser()


def simplify_node(state: AssistantState) -> dict:
    print(f"[simplify] state in: { {k: v for k, v in state.items() if k != 'raw_screen_text'} }")

    text = state.get("raw_screen_text") or state.get("user_request")
    language = state.get("target_language", "Spanish")

    if not text:
        return {"error": GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])}

    try:
        simplified = chain.invoke({"language": language, "source_text": text})
    except Exception as exc:
        print(f"[simplify] failed: {exc}")
        return {"error": GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])}

    result = {"simplified_text": simplified}
    print(f"[simplify] state out: {result}")
    return result
