import argparse
from typing import TypedDict, Sequence, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.messages import BaseMessage, message_to_dict
from langchain.callbacks.base import BaseCallbackHandler
import time
import requests


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    api_call_count: int


class APICallbackHandler(BaseCallbackHandler):
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.current_node = None
        self.last_inputs = {}
        self.last_outputs = {}
        self.reset_graph()

    def reset_graph(self):
        try:
            response = requests.delete(f"{self.api_url}/reset_graph/")
            if response.status_code != 200:
                print(f"Failed to reset graph: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to reset graph due to request exception: {e}")

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        node_name = self.extract_node_name(serialized)
        if self.should_log_node(node_name):
            self.current_node = node_name
            if not self.is_duplicate_input(self.current_node, inputs):
                self.send_node_data(f"input {self.current_node}", inputs)
                self.last_inputs[self.current_node] = inputs

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        if self.current_node:
            if not self.is_duplicate_output(self.current_node, outputs):
                self.send_node_data(f"output {self.current_node}", outputs)
                self.last_outputs[self.current_node] = outputs
            self.current_node = None

    def is_duplicate_input(self, node_name: str, inputs: Dict[str, Any]) -> bool:
        return self.last_inputs.get(node_name) == inputs

    def is_duplicate_output(self, node_name: str, outputs: Dict[str, Any]) -> bool:
        return self.last_outputs.get(node_name) == outputs

    def send_node_data(self, description: str, data: Dict[str, Any]):
        serialized_data = self.serialize_data(data)
        try:
            response = requests.post(
                f"{self.api_url}/add_node/",
                json={"description": description, "data": serialized_data},
            )
            if response.status_code != 200:
                print(f"Failed to send data: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send data due to request exception: {e}")

    def serialize_data(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {key: self.serialize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.serialize_data(item) for item in data]
        elif isinstance(data, BaseMessage):
            return message_to_dict(data)
        elif hasattr(data, "__dict__"):
            return self.serialize_data(data.__dict__)
        else:
            return data

    def extract_node_name(self, serialized: Dict[str, Any]) -> str:
        if "repr" in serialized:
            repr_str = serialized["repr"]
            if "<" in repr_str and ">" in repr_str:
                node_name = repr_str.split("<")[1].split(",")[0]
                return node_name.split(":")[1] if ":" in node_name else node_name
        if "id" in serialized:
            id_list = serialized["id"]
            return id_list[-1] if id_list else "Unknown Node"
        return "Unknown Node"

    def should_log_node(self, node_name: str) -> bool:
        exclude_nodes = {
            "messages",
            "CompiledStateGraph",
            "RunnableSequence",
            "RunnableCallable",
        }
        return node_name not in exclude_nodes


class PrintStateCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.current_node = None
        self.last_inputs = {}
        self.last_outputs = {}

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        node_name = self.extract_node_name(serialized)
        if self.should_log_node(node_name):
            self.current_node = node_name
            if not self.is_duplicate_input(self.current_node, inputs):
                print(f"input {self.current_node}: {inputs}")
                self.last_inputs[self.current_node] = inputs

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        if self.current_node:
            if not self.is_duplicate_output(self.current_node, outputs):
                print(f"output {self.current_node}: {outputs}")
                self.last_outputs[self.current_node] = outputs
            self.current_node = None

    def is_duplicate_input(self, node_name: str, inputs: Dict[str, Any]) -> bool:
        return self.last_inputs.get(node_name) == inputs

    def is_duplicate_output(self, node_name: str, outputs: Dict[str, Any]) -> bool:
        return self.last_outputs.get(node_name) == outputs

    def extract_node_name(self, serialized: Dict[str, Any]) -> str:
        if "repr" in serialized:
            repr_str = serialized["repr"]
            if "<" in repr_str and ">" in repr_str:
                node_name = repr_str.split("<")[1].split(",")[0]
                return node_name.split(":")[1] if ":" in node_name else node_name
        if "id" in serialized:
            id_list = serialized["id"]
            return id_list[-1] if id_list else "Unknown Node"
        return "Unknown Node"

    def should_log_node(self, node_name: str) -> bool:
        exclude_nodes = {
            "messages",
            "CompiledStateGraph",
            "RunnableSequence",
            "RunnableCallable",
        }
        return node_name not in exclude_nodes


def should_continue(state: AgentState):
    if state["api_call_count"] >= 8:
        return "final_node"
    else:
        return "branch_d"


def add_one(state: AgentState):
    time.sleep(0.25)
    state["messages"][-1].content += "a"
    state["api_call_count"] += 1
    return state


def final_node_function(state: AgentState):
    return state


graph = StateGraph(AgentState)

graph.add_node("branch_a", add_one)
graph.add_edge("branch_a", "branch_b")

graph.add_node("branch_b", add_one)
graph.add_edge("branch_b", "branch_c")

graph.add_node("branch_c", add_one)
graph.add_conditional_edges(
    "branch_c",
    should_continue,
    {
        "final_node": "final_node",
        "branch_d": "branch_d",
    },
)

graph.add_node("branch_d", add_one)
graph.add_edge("branch_d", "branch_c")

graph.add_node("final_node", final_node_function)
graph.add_edge("final_node", END)

graph.set_entry_point("branch_a")

app = graph.compile()

# Argument parsing to choose the callback handler
parser = argparse.ArgumentParser(description="Choose the callback handler to use.")
parser.add_argument(
    "--callback",
    choices=["api", "print"],
    default="print",
    help="Choose the callback handler: 'api' for APICallbackHandler or 'print' for PrintStateCallbackHandler.",
)
args = parser.parse_args()

if args.callback == "api":
    callback_handler = APICallbackHandler(api_url="http://localhost:8000")
else:
    callback_handler = PrintStateCallbackHandler()

inputs = {"messages": [HumanMessage(content="a")], "api_call_count": 0}
config = {"callbacks": [callback_handler]}

result = app.invoke(inputs, config=config)

print(result)
