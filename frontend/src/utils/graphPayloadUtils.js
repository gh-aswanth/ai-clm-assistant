/** Plain graph clone for react-force-graph-2d / force-graph (mutable x,y on nodes). */

export function prepareForceGraphData(payload) {
  if (!payload?.nodes?.length) return null

  const nodes = payload.nodes.map((n) => ({
    id: n.id,
    type: n.type,
    label: n.label ?? n.id,
    properties: n.properties ? { ...n.properties } : {},
  }))
  const nodeById = new Map(nodes.map((n) => [n.id, n]))
  const links = []
  for (const l of payload.links || []) {
    const sid = typeof l.source === 'object' && l.source != null ? l.source.id : l.source
    const tid = typeof l.target === 'object' && l.target != null ? l.target.id : l.target
    const s = nodeById.get(sid)
    const t = nodeById.get(tid)
    if (s && t) links.push({ source: s, target: t, type: l.type })
  }

  const degree = new Map()
  for (const n of nodes) degree.set(n.id, 0)
  for (const l of links) {
    const s = l.source?.id ?? l.source
    const t = l.target?.id ?? l.target
    if (s) degree.set(s, (degree.get(s) || 0) + 1)
    if (t) degree.set(t, (degree.get(t) || 0) + 1)
  }
  let maxDeg = 1
  for (const d of degree.values()) if (d > maxDeg) maxDeg = d
  for (const n of nodes) {
    const d = degree.get(n.id) || 0
    n.val = 1 + (d / maxDeg) * 2.35
  }

  return { nodes, links }
}
