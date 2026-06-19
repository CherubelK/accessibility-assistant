"""
Layer 1 of the accessibility assistant.
Takes confusing official text -> returns a plain-language summary in a target language.
Runs entirely locally via Ollama. No API key, no internet.
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- 1. The model -------------------------------------------------------
# This is the ONLY line you change to swap models later:
#   "phi4-mini", "llama3.1:8b", "qwen3:8b", "gemma3:12b", "qwen3:14b"
# temperature=0.2 keeps it focused and literal -- good for translation.
llm = ChatOllama(model="phi4-mini", temperature=0.2)

# --- 2. The prompt ------------------------------------------------------
# A template with two variables: the target language and the source text.
# The system message defines the assistant's job; the human message carries the input.
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You help elders and immigrants understand confusing government and official text. "
     "Explain what the text means in simple, calm, plain language a non-expert can follow. "
     "Do not add information that is not in the text. If an action or deadline is required, "
     "state it clearly. Respond ONLY in {language}."),
    ("human",
     "Here is the text to explain:\n\n{source_text}")
])

# --- 3. The parser ------------------------------------------------------
# Turns the model's message object into a plain string.
parser = StrOutputParser()

# --- 4. The chain -------------------------------------------------------
# The pipe (|) composes the three pieces into one callable pipeline.
# This is LCEL -- the core LangChain pattern you'll reuse everywhere.
chain = prompt | llm | parser

# --- 5. Run it ----------------------------------------------------------
if __name__ == "__main__":
    sample_text = (
        "Your application for benefits has been received. To avoid a lapse in "
        "coverage, you must submit Form RRB-1099 and proof of income within 30 "
        "days of the date on this notice. Failure to respond may result in "
        "termination of benefits."
    )

    print("Translating and simplifying...\n")
    result = chain.invoke({
        "language": "Spanish",
        "source_text": sample_text,
    })
    print(result)