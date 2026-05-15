/**
 * Turns stored knowledge-graph JSON (array of LangChain GraphDocument-shaped chunks:
 * `nodes`, `relationships`, optional `source`) into a friendly view model for non-technical users.
 */
import { parseGraphData } from './graphData.js'
import { getNodeColor } from './graphData.js'

const LABEL_MAX = 72
const CONNECTIONS_PREVIEW = Infinity
const TOP_ENTITY_COUNT = 14

function shortenLabel(value, max = LABEL_MAX) {
  const t = String(value ?? '').trim()
  if (!t) return '—'
  if (t.length <= max) return t
  return `${t.slice(0, Math.max(0, max - 1))}…`
}

function humanizeRelationType(raw) {
  if (raw == null || raw === '') return 'is connected to'
  const s = String(raw).replace(/_/g, ' ').trim()
  const lower = s.toLowerCase()
  const hints = [
    ['contract number', 'references contract number'],
    ['signed', 'relates to signing'],
    ['date', 'references a date'],
    ['party', 'involves party'],
    ['located', 'location link'],
    ['part of', 'is part of'],
    ['defines', 'defines'],
    ['requires', 'requires'],
    ['govern', 'governs'],
  ]
  for (const [needle, phrase] of hints) {
    if (lower.includes(needle)) return phrase
  }
  return lower
}

/**
 * @param {unknown[]} graphChunks - raw JSON from GET …/knowledge-graph
 * @returns {{
 *   hasData: boolean,
 *   intro: string,
 *   stats: { nodeCount: number, linkCount: number, categoryCount: number },
 *   typesByCount: Array<{ type: string, count: number, color: string, pct: number }>,
 *   topEntities: Array<{ id: string, type: string, label: string, connections: number, color: string }>,
 *   connections: Array<{ fromLabel: string, toLabel: string, relation: string, fromType?: string, toType?: string }>,
 * }}
 */
export function buildGraphInsights(graphChunks) {
  const { nodes, links } = parseGraphData(Array.isArray(graphChunks) ? graphChunks : [])
  const nodeCount = nodes.length
  const linkCount = links.length

  if (nodeCount === 0) {
    return {
      hasData: false,
      intro:
        'No facts were found in the saved graph yet. Build the knowledge graph after your document has been chunked.',
      stats: { nodeCount: 0, linkCount: 0, categoryCount: 0 },
      typesByCount: [],
      topEntities: [],
      connections: [],
    }
  }

  const degree = new Map()
  for (const n of nodes) degree.set(n.id, 0)
  for (const l of links) {
    const sid = typeof l.source === 'object' && l.source != null ? l.source.id : l.source
    const tid = typeof l.target === 'object' && l.target != null ? l.target.id : l.target
    if (sid) degree.set(sid, (degree.get(sid) || 0) + 1)
    if (tid) degree.set(tid, (degree.get(tid) || 0) + 1)
  }

  const typeMap = new Map()
  for (const n of nodes) {
    const t = (n.type && String(n.type).trim()) || 'Other'
    const cur = typeMap.get(t) || { type: t, count: 0, color: getNodeColor(t) }
    cur.count += 1
    typeMap.set(t, cur)
  }
  const typesByCount = [...typeMap.values()].sort((a, b) => b.count - a.count)
  const maxType = typesByCount[0]?.count || 1
  for (const row of typesByCount) {
    row.pct = Math.round((row.count / maxType) * 100)
  }

  const topEntities = [...nodes]
    .sort((a, b) => (degree.get(b.id) || 0) - (degree.get(a.id) || 0))
    .slice(0, TOP_ENTITY_COUNT)
    .map((n) => ({
      id: n.id,
      type: n.type || 'Other',
      label: shortenLabel(n.id),
      connections: degree.get(n.id) || 0,
      color: getNodeColor(n.type),
    }))

  const nodeById = new Map(nodes.map((n) => [n.id, n]))
  const connections = []
  for (const l of links) {
    if (connections.length >= CONNECTIONS_PREVIEW) break
    const sid = typeof l.source === 'object' && l.source != null ? l.source.id : l.source
    const tid = typeof l.target === 'object' && l.target != null ? l.target.id : l.target
    const sn = nodeById.get(sid)
    const tn = nodeById.get(tid)
    connections.push({
      fromLabel: shortenLabel(sid),
      toLabel: shortenLabel(tid),
      relation: humanizeRelationType(l.type),
      fromType: sn?.type,
      toType: tn?.type,
    })
  }

  return {
    hasData: true,
    stats: {
      nodeCount,
      linkCount,
      categoryCount: typesByCount.length,
    },
    typesByCount,
    topEntities,
    connections,
  }
}

/**
 * Build SVG donut segments from `typesByCount` rows.
 * R=54, C≈339.3, start at 12-o'clock (caller applies rotate(-90 80 80)).
 */
export function buildDonutSegments(typesByCount) {
  if (!typesByCount?.length) return []
  const total = typesByCount.reduce((s, t) => s + t.count, 0)
  if (!total) return []
  const R = 54
  const C = +(2 * Math.PI * R).toFixed(2)
  const GAP = 3
  let accumulated = 0
  return typesByCount.slice(0, 10).map((t) => {
    const raw = (t.count / total) * C
    const dash = +Math.max(0, raw - GAP).toFixed(2)
    const seg = {
      type: t.type,
      count: t.count,
      color: t.color,
      pct: Math.round((t.count / total) * 100),
      dash,
      C,
      dashoffset: +(-accumulated).toFixed(2),
    }
    accumulated += raw
    return seg
  })
}
