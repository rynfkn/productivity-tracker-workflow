from langgraph.graph import END, START, StateGraph

from workflow.nodes.classify_command import node_classify_command
from workflow.nodes.handle_command import node_handle_command
from workflow.state import CommandState

command_workflow = StateGraph(CommandState)

command_workflow.add_node("classify_command", node_classify_command)
command_workflow.add_node("handle_command", node_handle_command)

command_workflow.add_edge(START, "classify_command")
command_workflow.add_edge("classify_command", "handle_command")
command_workflow.add_edge("handle_command", END)

command_app = command_workflow.compile()
