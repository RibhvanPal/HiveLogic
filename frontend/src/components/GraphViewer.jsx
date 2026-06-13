import React, { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
} from "reactflow";
import "reactflow/dist/style.css";

export default function GraphViewer({
  nodes = [],
  edges = [],
}) {
  const flowNodes = useMemo(() => {
    return nodes.map((node, index) => ({
      id: node.id,
      data: {
        label: node.label,
      },
      position: {
        x: (index % 4) * 250,
        y: Math.floor(index / 4) * 150,
      },
      style: {
        padding: 10,
        borderRadius: 10,
        border:
          node.type === "company"
            ? "2px solid #2563eb"
            : "1px solid #475569",
        background:
          node.type === "company"
            ? "#dbeafe"
            : "#ffffff",
        minWidth: 120,
        textAlign: "center",
        fontWeight: 600,
      },
    }));
  }, [nodes]);

  const flowEdges = useMemo(() => {
    return edges.map((edge, idx) => ({
      id: `e-${idx}`,
      source: edge.source,
      target: edge.target,
      label: edge.relation,
      animated: edge.weight >= 0.75,
    }));
  }, [edges]);

  if (!nodes.length) return null;

  return (
    <div
      style={{
        height: "600px",
        marginTop: "24px",
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        overflow: "hidden",
      }}
    >
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        fitView
      >
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}