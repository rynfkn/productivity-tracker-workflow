from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from workflow.nodes import (
    node_analyze_intent,
    node_send_message,
    node_update_activity,
)
from workflow.state import ProductivityState


workflow = StateGraph(ProductivityState)

workflow.add_node("send_message", node_send_message)
workflow.add_node("analyze_intent", node_analyze_intent)
workflow.add_node("update_activity", node_update_activity)

workflow.add_edge(START, "send_message")
workflow.add_edge("send_message", "analyze_intent")
workflow.add_edge("analyze_intent", "update_activity")
workflow.add_edge("update_activity", END)

app = workflow.compile(checkpointer=MemorySaver())