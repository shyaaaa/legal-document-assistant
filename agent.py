from typing import TypedDict, List
from langgraph.graph import StateGraph   #type:ignore
from sentence_transformers import SentenceTransformer  #type:ignore
                                         
from datetime import datetime  

# =========================
# STATE DEFINITION
# =========================
class CapstoneState(TypedDict):
    question: str
    messages: List[str]
    route: str
    retrieved: str
    sources: List[str]
    tool_result: str
    answer: str
    faithfulness: float
    eval_retries: int


# =========================
# KNOWLEDGE BASE
# =========================
DOCUMENTS = [
    {"id": "doc1", "text": "A contract is a legally binding agreement requiring offer, acceptance, and consideration."},
    {"id": "doc2", "text": "Contracts may be written or oral, but written contracts are easier to enforce."},
    {"id": "doc3", "text": "Breach of contract occurs when one party fails to fulfill obligations."},
    {"id": "doc4", "text": "Legal remedies include damages, injunctions, and specific performance."},
    {"id": "doc5", "text": "Tort law deals with civil wrongs like negligence and defamation."},
    {"id": "doc6", "text": "Negligence is failure to exercise reasonable care resulting in damage."},
    {"id": "doc7", "text": "Intellectual property includes patents, copyrights, and trademarks."},
    {"id": "doc8", "text": "Criminal law deals with offenses against the state such as theft or assault."},
    {"id": "doc9", "text": "Legal procedures include filing cases, presenting evidence, and hearings."},
    {"id": "doc10", "text": "Evidence law governs admissibility and reliability of proof in court."},
]

# =========================
# VECTOR DB SETUP
# =========================
def retrieval_node(state):
    query = state["question"].lower()

    matched_docs = []

    for doc in DOCUMENTS:
        if any(word in doc["text"].lower() for word in query.split()):
            matched_docs.append(doc["text"])

    context = "\n".join(matched_docs[:3])

    return {
        **state,
        "retrieved": context,
        "sources": []
    }



# =========================
# NODES
# =========================
def memory_node(state: CapstoneState):
    messages = state.get("messages", [])
    messages.append(state["question"])
    return {**state, "messages": messages[-6:]}


def router_node(state: CapstoneState):
    query = state["question"].lower()

    if "time" in query or "date" in query:
        return {**state, "route": "tool"}
    else:
        return {**state, "route": "retrieve"}


def retrieval_node(state):
    query = state["question"].lower()

    matched_docs = []

    for doc in DOCUMENTS:
        if any(word in doc["text"].lower() for word in query.split()):
            matched_docs.append(doc["text"])

    context = "\n".join(matched_docs[:3])

    return {
        **state,
        "retrieved": context,
        "sources": []
    }

    context = "\n".join(results["documents"][0])

    return {
        **state,
        "retrieved": context,
        "sources": results["ids"][0],
    }


def tool_node(state: CapstoneState):
    try:
        return {**state, "tool_result": str(datetime.now())}
    except Exception:
        return {**state, "tool_result": "Error fetching time"}


def answer_node(state: CapstoneState):
    context = state.get("retrieved", "")

    if not context:
        answer = "I don't know based on the provided documents."
    else:
        answer = f"Answer based on documents:\n{context}"

    return {**state, "answer": answer}


def eval_node(state: CapstoneState):
    return {**state, "faithfulness": 0.9}


def save_node(state: CapstoneState):
    messages = state.get("messages", [])
    messages.append(state["answer"])
    return {**state, "messages": messages}


# =========================
# GRAPH BUILDING
# =========================
graph = StateGraph(CapstoneState)

graph.add_node("memory", memory_node)
graph.add_node("router", router_node)
graph.add_node("retrieve", retrieval_node)
graph.add_node("tool", tool_node)
graph.add_node("answer", answer_node)
graph.add_node("eval", eval_node)
graph.add_node("save", save_node)

graph.set_entry_point("memory")

graph.add_edge("memory", "router")
graph.add_edge("router", "retrieve")
graph.add_edge("retrieve", "answer")
graph.add_edge("tool", "answer")
graph.add_edge("answer", "eval")
graph.add_edge("eval", "save")

app = graph.compile()


# =========================
# FUNCTION
# =========================
def ask(question: str):
    result = app.invoke({
        "question": question,
        "messages": [],
    })
    return result["answer"]