# Custom "LangGraph Studio" with Callbacks

## Project Overview

This is an approach to mimic LangGraph Studio just with Callbacks. It visualizes real-time state transitions in a LangGraph execution graph. It features a FastAPI backend for managing the graph's state and a React frontend with D3.js for dynamic visualization.

## Project Structure

```plaintext
.
├── app.py               # FastAPI backend with Socket.IO for real-time communication
├── graph-visualization/ # React + D3.js frontend for graph visualization
├── script.py            # Python script for invoking LangGraph with callbacks
```

## How to Use

### Backend (`app.py`)

1. **Install dependencies**: Ensure you have all required Python packages installed. You can do this with pip:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the FastAPI server**:

   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

   The server will start on `localhost:8000`, handling HTTP requests and WebSocket connections for real-time updates.

### Frontend (`graph-visualization/`)

1. **Navigate to the frontend directory**:

   ```bash
   cd graph-visualization
   ```

2. **Install frontend dependencies**:

   ```bash
   npm install
   ```

3. **Run the frontend**:

   ```bash
   npm start
   ```

   This will launch the React application, which connects to the backend and visualizes the graph.

### Script (`script.py`)

The `script.py` script demonstrates how to invoke the LangGraph with different callback handlers. These handlers determine how the graph's state transitions are processed and displayed.

#### Callback Handlers

- **`APICallbackHandler`**: Sends the node data to the FastAPI server, allowing real-time updates to be visualized in the frontend.
- **`PrintStateCallbackHandler`**: Prints the state transitions and node data directly to the console.

#### Running the Script with Different Handlers

You can specify which callback handler to use by providing a command-line argument:

1. **Using `APICallbackHandler`**:

   This handler sends updates to the backend for real-time visualization.

   ```bash
   python script.py --callback api
   ```

2. **Using `PrintStateCallbackHandler`**:

   This handler prints the state transitions to the console.

   ```bash
   python script.py --callback print
   ```
