import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.config import DEFAULT_TEXT_MODEL, FORM_REFERENCE_LABEL, GENERIC_ERROR_MESSAGES
from src.nodes._timing import timed_node
from src.state import AssistantState

# Matches "Form RRB-1099", "Form I-9", "Form W-2", etc. Small CPU models can
# garble these while rephrasing (observed: "RRB-1099" -> "RR-BR-1099" with
# phi4-mini, ~1 in 5 runs) -- corrupting a form number is exactly the kind
# of fact-corruption this project's "never invent/corrupt facts" principle
# is meant to prevent, so it's checked deterministically rather than trusted
# to the model.
FORM_NUMBER_PATTERN = re.compile(r"\bForm\s+([A-Za-z0-9][A-Za-z0-9-]*)", re.IGNORECASE)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You help elders and immigrants understand confusing government and official text. "
     "Explain what the text means in simple, calm, plain language a non-expert can follow. "
     "Do not add information that is not in the text. If an action or deadline is required, "
     "state it clearly. Respond ONLY in {language}."),
    ("human",
     "Here is the text to explain:\n\n{source_text}")
])

_chain_cache: dict[str, object] = {}


def get_chain(model_name: str = DEFAULT_TEXT_MODEL):
    """Returns a cached prompt|llm|parser chain for the given Ollama model
    name, building it once per model so switching between "fast" and
    "quality" doesn't reload anything beyond Ollama's own model swap."""
    if model_name not in _chain_cache:
        # reasoning=False disables "thinking" mode on models that default to
        # it (e.g. qwen3) -- a full chain-of-thought before the visible
        # answer adds a lot of latency we don't need for a direct
        # simplify/translate task (observed: 172s vs. a few seconds).
        llm = ChatOllama(model=model_name, temperature=0.2, reasoning=False)
        _chain_cache[model_name] = prompt | llm | StrOutputParser()
    return _chain_cache[model_name]


# Default chain, kept for backwards-compat callers that don't care about
# model choice.
chain = get_chain(DEFAULT_TEXT_MODEL)


@timed_node("simplify")
def simplify_node(state: AssistantState) -> dict:
    print(f"[simplify] state in: { {k: v for k, v in state.items() if k != 'raw_screen_text'} }")

    text = state.get("raw_screen_text") or state.get("user_request")
    language = state.get("target_language", "Spanish")
    model_name = state.get("text_model", DEFAULT_TEXT_MODEL)

    if not text:
        return {"error": GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])}

    try:
        simplified = get_chain(model_name).invoke({"language": language, "source_text": text})
    except Exception as exc:
        print(f"[simplify] failed: {exc}")
        return {"error": GENERIC_ERROR_MESSAGES.get(language, GENERIC_ERROR_MESSAGES["English"])}

    missing_forms = [
        m for m in FORM_NUMBER_PATTERN.findall(text)
        if m.lower() not in simplified.lower()
    ]
    if missing_forms:
        label = FORM_REFERENCE_LABEL.get(language, FORM_REFERENCE_LABEL["English"])
        simplified += f"\n\n({label}: Form {', '.join(missing_forms)})"
        print(f"[simplify] re-appended garbled/missing form number(s): {missing_forms}")

    result = {"simplified_text": simplified}
    print(f"[simplify] state out: {result}")
    return result
