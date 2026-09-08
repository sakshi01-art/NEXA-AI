import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Play, Save, Plus, Trash2 } from 'lucide-react';

interface WorkflowBuilderProps {
  onSave: (workflow: any) => void;
  onExecute: (workflow: any) => void;
}

const nodeTypes = {
  trigger: TriggerNode,
  action: ActionNode,
  condition: ConditionNode,
  loop: LoopNode,
};

export const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  onSave,
  onExecute,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [workflowName, setWorkflowName] = useState('New Workflow');

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const addNode = (type: string) => {
    const newNode: Node = {
      id: `${type}-${Date.now()}`,
      type,
      position: { x: 250, y: 100 + nodes.length * 100 },
      data: {
        label: `${type.charAt(0).toUpperCase() + type.slice(1)} ${nodes.length + 1}`,
        config: {},
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const saveWorkflow = () => {
    const workflow = {
      name: workflowName,
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.type,
        data: node.data,
      })),
      edges: edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
      })),
      createdAt: new Date().toISOString(),
    };
    onSave(workflow);
  };

  const executeWorkflow = () => {
    const workflow = {
      nodes,
      edges,
    };
    onExecute(workflow);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="glass-panel p-4 flex items-center justify-between border-b border-gray-700">
        <div className="flex items-center gap-4">
          <input
            type="text"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="bg-gray-800 text-white px-4 py-2 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Workflow Name"
          />
        </div>

        <div className="flex items-center gap-2">
          <motion.button
            onClick={() => addNode('trigger')}
            className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 rounded-lg flex items-center gap-2 text-blue-400 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Plus className="w-4 h-4" />
            Trigger
          </motion.button>

          <motion.button
            onClick={() => addNode('action')}
            className="px-4 py-2 bg-green-500/20 hover:bg-green-500/30 rounded-lg flex items-center gap-2 text-green-400 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Plus className="w-4 h-4" />
            Action
          </motion.button>

          <motion.button
            onClick={() => addNode('condition')}
            className="px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 rounded-lg flex items-center gap-2 text-yellow-400 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Plus className="w-4 h-4" />
            Condition
          </motion.button>

          <div className="w-px h-6 bg-gray-700 mx-2" />

          <motion.button
            onClick={executeWorkflow}
            className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 rounded-lg flex items-center gap-2 text-white transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Play className="w-4 h-4" />
            Execute
          </motion.button>

          <motion.button
            onClick={saveWorkflow}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg flex items-center gap-2 text-white transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Save className="w-4 h-4" />
            Save
          </motion.button>
        </div>
      </div>

      {/* Flow Canvas */}
      <div className="flex-1 bg-gray-950">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background />
          <Controls />
          
          <Panel position="bottom-left" className="glass-panel p-4 m-4 rounded-lg">
            <div className="text-xs text-gray-400 space-y-1">
              <p><strong>Blue:</strong> Triggers (when to run)</p>
              <p><strong>Green:</strong> Actions (what to do)</p>
              <p><strong>Yellow:</strong> Conditions (if/else)</p>
            </div>
          </Panel>
        </ReactFlow>
      </div>
    </div>
  );
};

// Custom Node Components
function TriggerNode({ data }: { data: any }) {
  return (
    <div className="bg-blue-500/20 border-2 border-blue-500 rounded-lg p-4 min-w-[200px]">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-3 h-3 rounded-full bg-blue-500" />
        <p className="text-sm font-semibold text-blue-400">TRIGGER</p>
      </div>
      <p className="text-white text-sm">{data.label}</p>
      
      <select className="mt-2 w-full bg-gray-800 text-white text-xs p-2 rounded">
        <option>On Schedule</option>
        <option>On System Event</option>
        <option>On File Change</option>
        <option>On App Launch</option>
        <option>Manual</option>
      </select>
    </div>
  );
}

function ActionNode({ data }: { data: any }) {
  return (
    <div className="bg-green-500/20 border-2 border-green-500 rounded-lg p-4 min-w-[200px]">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-3 h-3 rounded-full bg-green-500" />
        <p className="text-sm font-semibold text-green-400">ACTION</p>
      </div>
      <p className="text-white text-sm">{data.label}</p>
      
      <select className="mt-2 w-full bg-gray-800 text-white text-xs p-2 rounded">
        <option>Open Application</option>
        <option>Run Command</option>
        <option>Send Notification</option>
        <option>Create File</option>
        <option>HTTP Request</option>
      </select>
    </div>
  );
}

function ConditionNode({ data }: { data: any }) {
  return (
    <div className="bg-yellow-500/20 border-2 border-yellow-500 rounded-lg p-4 min-w-[200px]">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-3 h-3 rounded-full bg-yellow-500" />
        <p className="text-sm font-semibold text-yellow-400">CONDITION</p>
      </div>
      <p className="text-white text-sm">{data.label}</p>
      
      <select className="mt-2 w-full bg-gray-800 text-white text-xs p-2 rounded">
        <option>If file exists</option>
        <option>If CPU &gt; threshold</option>
        <option>If time is</option>
        <option>If app is running</option>
      </select>
    </div>
  );
}

function LoopNode({ data }: { data: any }) {
  return (
    <div className="bg-purple-500/20 border-2 border-purple-500 rounded-lg p-4 min-w-[200px]">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-3 h-3 rounded-full bg-purple-500" />
        <p className="text-sm font-semibold text-purple-400">LOOP</p>
      </div>
      <p className="text-white text-sm">{data.label}</p>
      
      <input
        type="number"
        placeholder="Iterations"
        className="mt-2 w-full bg-gray-800 text-white text-xs p-2 rounded"
      />
    </div>
  );
}
