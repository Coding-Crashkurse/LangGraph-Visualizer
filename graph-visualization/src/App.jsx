import React, { useEffect, useState, useRef } from "react";
import * as d3 from "d3";
import io from "socket.io-client";
import "./App.css";

const socket = io("http://localhost:8000", {
  transports: ["websocket"],
  upgrade: false,
  path: "/ws/socket.io",
});

const GraphVisualization = () => {
  const [nodesData, setNodesData] = useState([]);
  const [fullRawData, setRawData] = useState({});
  const svgRef = useRef();

  useEffect(() => {
    const handleUpdate = (data) => {
      setRawData((prevData) => ({
        ...prevData,
        ...data,
      }));

      const newNodes = data.nodes.map((node) => {
        const messages = node.data?.messages || [];
        const formattedMessages = messages.map((msg) => ({
          type: msg.type || "unknown",
          content: msg.data?.content || msg.content || "undefined",
        }));

        return {
          description: node.description,
          messages: formattedMessages,
          id: node.description.replace(/input |output /, ""),
          color: node.description.startsWith("input") ? "red" : "green",
        };
      });

      const updatedNodes = [...nodesData];

      newNodes.forEach((newNode) => {
        const existingNodeIndex = updatedNodes.findIndex(
          (node) => node.id === newNode.id
        );

        if (existingNodeIndex !== -1) {
          updatedNodes[existingNodeIndex].color = newNode.color;
        } else {
          updatedNodes.push(newNode);
        }
      });

      setNodesData(updatedNodes);
      createGraph(updatedNodes);
    };

    socket.on("update", handleUpdate);

    return () => {
      socket.off("update", handleUpdate);
    };
  }, []);

  const createGraph = (nodes) => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    if (nodes.length === 0) return;

    const width = 500;
    const height = nodes.length * 100;
    const nodeWidth = 200;
    const nodeHeight = 40;

    svg.attr("width", width).attr("height", height);

    const centerX = (width - nodeWidth) / 2;

    svg
      .append("g")
      .attr("class", "nodes")
      .selectAll("rect")
      .data(nodes)
      .enter()
      .append("rect")
      .attr("x", () => centerX)
      .attr("y", (d, i) => i * 100)
      .attr("width", nodeWidth)
      .attr("height", nodeHeight)
      .attr("fill", (d) => d.color)
      .attr("stroke", "black")
      .attr("rx", 5)
      .attr("ry", 5);

    svg
      .append("g")
      .attr("class", "labels")
      .selectAll("text")
      .data(nodes)
      .enter()
      .append("text")
      .attr("x", () => centerX + nodeWidth / 2)
      .attr("y", (d, i) => i * 100 + 25)
      .attr("text-anchor", "middle")
      .attr("font-size", 12)
      .attr("fill", "white")
      .text((d) => d.id);

    svg
      .append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(nodes.slice(1))
      .enter()
      .append("line")
      .attr("x1", () => centerX + nodeWidth / 2)
      .attr("y1", (d, i) => i * 100 + nodeHeight)
      .attr("x2", () => centerX + nodeWidth / 2)
      .attr("y2", (d, i) => (i + 1) * 100)
      .attr("stroke-width", 2)
      .attr("stroke", "#999");
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-start p-4">
      <h1 className="text-4xl font-bold mt-8 mb-8">Graph Visualization</h1>
      <div className="flex flex-col lg:flex-row bg-white shadow-lg rounded-lg p-6 w-full max-w-screen-lg gap-6">
        <div className="flex-grow lg:w-1/2 flex justify-center items-start">
          <div style={{ paddingTop: "20px" }}>
            {nodesData.length === 0 ? (
              <div className="text-center text-gray-500">No graph run yet</div>
            ) : (
              <svg
                ref={svgRef}
                className="border-2 border-gray-300 shadow-lg rounded-lg"
              ></svg>
            )}
          </div>
        </div>
        <div className="flex-grow lg:w-1/2">
          <div className="card bg-base-100 shadow-lg p-4 h-full rounded-lg">
            <h3 className="text-xl font-semibold mb-4 text-center">
              Graph Output
            </h3>
            <div className="card-body p-0 max-h-96 overflow-y-auto">
              {fullRawData.nodes && fullRawData.nodes.length > 0 ? (
                fullRawData.nodes.map((node, index) => (
                  <div
                    key={index}
                    className="p-4 bg-gray-100 rounded-lg shadow-md mb-4"
                  >
                    <strong className="block text-lg text-left text-gray-800">
                      {node.description}
                    </strong>
                    <div className="mt-2 text-left text-sm text-gray-600">
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(node.data, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500">
                  No graph run yet
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphVisualization;
