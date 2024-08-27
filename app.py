from fastapi import FastAPI
from fastapi_socketio import SocketManager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_manager = SocketManager(app=app, socketio_path="/ws/socket.io")


class NodeData(BaseModel):
    description: str
    data: Dict[str, Any]


execution_data = {"nodes": [], "edges": []}


@app.post("/add_node/")
async def add_node(node_data: NodeData):
    execution_data["nodes"].append(
        {
            "description": node_data.description,
            "data": node_data.data,
        }
    )
    await socket_manager.emit("update", execution_data)
    return {"status": "Node added"}


@app.get("/get_graph/")
async def get_graph():
    return execution_data


@app.delete("/reset_graph/")
async def reset_graph():
    execution_data["nodes"].clear()
    execution_data["edges"].clear()
    await socket_manager.emit("update", execution_data)
    return {"status": "Graph reset"}


@socket_manager.on("run_graph_event")
async def run_graph_event(sid, *args, **kwargs):
    print(f"Client {sid} triggered the graph run")
    await socket_manager.emit("acknowledge", {"status": "Graph is running"}, to=sid)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
