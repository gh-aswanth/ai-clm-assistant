/**
 * Layout engine for the "Contract Universe" visualization —
 * polar placement by entity type + curved edges for a memorable SVG scene.
 */
import { parseGraphData } from './graphData.js'
import { getNodeColor } from './graphData.js'

const LABEL_MAX = 48
const NODE_CAP = 52
const EDGE_CAP = 70

function shorten(value, max = LABEL_MAX) {
  const t = String(value ?? '').trim()
  if (!t) return '—'
  if (t.length <= max) return t
  return `${t.slice(0, Math.max(0, max - 1))}…`
}

function hashStr(s) {
  let h = 0
  for (let i = 0; i < String(s).length; i++) h = (Math.imul(31, h) + String(s).charCodeAt(i)) | 0
  return (Math.abs(h) % 1000) / 1000
}

function computeDegree(nodes, links) {
  const d = new Map()
  for (const n of nodes) d.set(n.id, 0)
  for (const l of links) {
    const sid = typeof l.source === 'object' && l.source != null ? l.source.id : l.source
    const tid = typeof l.target === 'object' && l.target != null ? l.target.id : l.target
    if (sid) d.set(sid, (d.get(sid) || 0) + 1)
    if (tid) d.set(tid, (d.get(tid) || 0) + 1)
  }
  return d
}

function quadPath(x1, y1, x2, y2) {
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2
  const dx = x2 - x1
  const dy = y2 - y1
  const len = Math.hypot(dx, dy) || 1
  const bend = 38 + Math.min(55, len * 0.18)
  const ox = (-dy / len) * bend
  const oy = (dx / len) * bend
  return `M ${round(x1)} ${round(y1)} Q ${round(mx + ox)} ${round(my + oy)} ${round(x2)} ${round(y2)}`
}

function round(n) {
  return Math.round(n * 10) / 10
}

/**
 * @param {unknown[]} graphChunks
 * @returns {null | {
 *   width: number,
 *   height: number,
 *   cx: number,
 *   cy: number,
 *   orbitRings: number[],
 *   edges: Array<{ d: string, opacity: number }>,
 *   bodies: Array<{ id: string, x: number, y: number, r: number, color: string, label: string, type: string }>,
 * }}
 */
export function buildUniverseScene(graphChunks) {
  const { nodes, links } = parseGraphData(Array.isArray(graphChunks) ? graphChunks : [])
  if (!nodes.length) return null

  const degree = computeDegree(nodes, links)
  const sorted = [...nodes].sort((a, b) => (degree.get(b.id) || 0) - (degree.get(a.id) || 0))
  const picked = sorted.slice(0, NODE_CAP)

  const byType = new Map()
  for (const n of picked) {
    const t = (n.type && String(n.type).trim()) || 'Other'
    if (!byType.has(t)) byType.set(t, [])
    byType.get(t).push(n)
  }

  const typesOrdered = [...byType.entries()].sort((a, b) => b[1].length - a[1].length)
  const nTypes = Math.max(1, typesOrdered.length)

  const W = 920
  const H = 520
  const CX = W / 2
  const CY = H / 2 + 8

  const orbitRings = [88, 158, 228, 298]

  const bodies = []
  const pos = new Map()

  let sectorStart = -Math.PI / 2
  for (const [type, arr] of typesOrdered) {
    const sector = (2 * Math.PI) / nTypes
    const base = sectorStart
    sectorStart += sector
    const nIn = arr.length
    arr.forEach((node, i) => {
      const spread = nIn <= 1 ? 0.5 : 0.06 + (i / Math.max(1, nIn - 1)) * 0.88
      const angle = base + sector * spread
      const jitter = hashStr(`${node.id}|${type}`) * 26 - 13
      const ringIdx = Math.min(orbitRings.length - 1, Math.floor(hashStr(node.id) * 1.7 + (degree.get(node.id) || 0) * 0.15))
      const ring = orbitRings[ringIdx] + jitter
      const x = CX + Math.cos(angle) * ring
      const y = CY + Math.sin(angle) * ring
      const deg = degree.get(node.id) || 0
      const r = 3.2 + Math.min(11, 2 + deg * 0.85 + hashStr(node.id) * 2)
      const color = getNodeColor(node.type)
      const b = {
        id: node.id,
        x,
        y,
        r,
        color,
        label: shorten(node.id),
        type,
      }
      bodies.push(b)
      pos.set(node.id, b)
    })
  }

  const edges = []
  const seen = new Set()
  for (const l of links) {
    if (edges.length >= EDGE_CAP) break
    const sid = typeof l.source === 'object' && l.source != null ? l.source.id : l.source
    const tid = typeof l.target === 'object' && l.target != null ? l.target.id : l.target
    const a = pos.get(sid)
    const b = pos.get(tid)
    if (!a || !b || sid === tid) continue
    const key = sid < tid ? `${sid}|${tid}` : `${tid}|${sid}`
    if (seen.has(key)) continue
    seen.add(key)
    const opacity = 0.07 + hashStr(key) * 0.11
    edges.push({
      d: quadPath(a.x, a.y, b.x, b.y),
      opacity,
    })
  }

  return {
    width: W,
    height: H,
    cx: CX,
    cy: CY,
    orbitRings,
    edges,
    bodies,
  }
}
