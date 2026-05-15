/** Parsed from clm/graph_data.json (array of chunks with nodes + relationships). */

export const NODE_TYPE_COLORS = {
  Document: '#60a5fa',
  Contract: '#34d399',
  Date: '#fbbf24',
  Organization: '#a78bfa',
  Address: '#f472b6',
  Identifier: '#2dd4bf',
  Work: '#fb923c',
  Building: '#94a3b8',
  Place: '#22d3ee',
  Money: '#4ade80',
  Duration: '#facc15',
  Concept: '#c084fc',
  Value: '#38bdf8',
  Time: '#a3e635',
  Material: '#fb7185',
  Grade: '#e879f9',
  Standard: '#5eead4',
  Process: '#fdba74',
  Item: '#bae6fd',
  Role: '#ddd6fe',
  Requirement: '#fde68a',
  Law: '#fca5a5',
  Insurance: '#86efac',
  Guarantee: '#93c5fd',
  Period: '#d8b4fe',
  Coverage: '#67e8f9',
  Approval: '#fcd34d',
  Quantity: '#6ee7b7',
  Activity: '#c4b5fd',
  Event: '#fda4af',
}

const DEFAULT_NODE_COLOR = '#64748b'

export function getNodeColor(type) {
  return NODE_TYPE_COLORS[type] ?? DEFAULT_NODE_COLOR
}

export function parseGraphData(chunks) {
  const nodeMap = new Map()
  const linkSet = new Set()
  const links = []

  for (const chunk of chunks) {
    for (const node of chunk.nodes || []) {
      if (!nodeMap.has(node.id)) {
        nodeMap.set(node.id, {
          id: node.id,
          type: node.type,
          label: node.id,
          properties: node.properties || {},
        })
      }
    }

    for (const rel of chunk.relationships || []) {
      const key = `${rel.source.id}->${rel.target.id}:${rel.type}`
      if (!linkSet.has(key)) {
        linkSet.add(key)
        const srcNode = nodeMap.get(rel.source.id)
        const tgtNode = nodeMap.get(rel.target.id)
        if (srcNode && tgtNode) {
          links.push({
            source: srcNode,
            target: tgtNode,
            type: rel.type,
          })
        }
      }
    }
  }

  return {
    nodes: Array.from(nodeMap.values()),
    links,
  }
}
