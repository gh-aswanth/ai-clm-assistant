import { useCallback, useEffect, useRef, useMemo, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { getNodeColor } from '../../utils/graphData.js'

const NODE_REL_SIZE = 4.6
const LINK_CURVATURE = 0.14
const DRIFT_ALPHA_TARGET = 0.011
const DRIFT_COOLDOWN_MS = 86_400_000
/** Zoomed out: hide noisy labels; zoom in to read the graph */
const ZOOM_NODE_LABELS_ALL = 0.26
const ZOOM_EDGE_LABELS = 0.42

/** Navy + sky — aligned with contract UI (tabs, cards, light blue chrome) */
const PALETTE = {
  light: {
    link: 'rgba(30, 58, 138, 0.14)',
    linkHl: 'rgba(37, 99, 235, 0.62)',
    edgeFill: 'rgba(255, 255, 255, 0.97)',
    edgeStroke: 'rgba(186, 230, 253, 0.98)',
    edgeStrokeHl: 'rgba(59, 130, 246, 0.55)',
    edgeShadow: 'rgba(15, 23, 42, 0.06)',
    edgeText: 'rgba(30, 41, 59, 0.88)',
    edgeTextHl: 'rgba(29, 78, 216, 1)',
    nodeStroke: 'rgba(255, 255, 255, 0.88)',
    nodeFill: 'rgba(15, 23, 42, 0.92)',
    ringHl: 'rgba(59, 130, 246, 0.55)',
    /* Match --clm-bg-page in light theme */
    canvasBg: '#f4f6f9',
    labelShadow: 'rgba(248, 250, 252, 0.96)',
    labelFill: 'rgba(15, 23, 42, 0.91)',
    arrow: 'rgba(37, 99, 235, 0.42)',
    arrowHl: 'rgba(29, 78, 216, 0.88)',
  },
  dark: {
    link: 'rgba(96, 165, 250, 0.12)',
    linkHl: 'rgba(147, 197, 253, 0.72)',
    edgeFill: 'rgba(15, 23, 42, 0.92)',
    edgeStroke: 'rgba(51, 65, 85, 0.92)',
    edgeStrokeHl: 'rgba(96, 165, 250, 0.5)',
    edgeShadow: 'rgba(0, 0, 0, 0.35)',
    edgeText: 'rgba(203, 213, 225, 0.92)',
    edgeTextHl: 'rgba(191, 219, 254, 1)',
    nodeStroke: 'rgba(255, 255, 255, 0.14)',
    nodeFill: 'rgba(248, 250, 252, 0.94)',
    ringHl: 'rgba(147, 197, 253, 0.65)',
    /* Match --clm-bg-page in dark theme */
    canvasBg: '#050f1d',
    labelShadow: 'rgba(15, 23, 42, 0.94)',
    labelFill: 'rgba(241, 245, 249, 0.94)',
    arrow: 'rgba(96, 165, 250, 0.45)',
    arrowHl: 'rgba(191, 219, 254, 0.92)',
  },
}

function parseHexColor(hex) {
  const h = String(hex).replace('#', '')
  if (h.length !== 6) return { r: 100, g: 116, b: 139 }
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  }
}

function rgba(rgb, a) {
  return `rgba(${rgb.r},${rgb.g},${rgb.b},${a})`
}

function useClmDarkMode(forceDark = false) {
  const [dark, setDark] = useState(() =>
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
  )
  useEffect(() => {
    if (forceDark) {
      setDark(true)
      return
    }
    const el = document.documentElement
    const sync = () => setDark(el.classList.contains('dark'))
    const mo = new MutationObserver(sync)
    mo.observe(el, { attributes: true, attributeFilter: ['class'] })
    return () => mo.disconnect()
  }, [forceDark])
  return forceDark || dark
}

function linkLabelPosition(sx, sy, tx, ty, curvature) {
  const l = Math.hypot(tx - sx, ty - sy) || 1
  const a = Math.atan2(ty - sy, tx - sx)
  const d = l * curvature
  const cx = (sx + tx) / 2 + d * Math.cos(a - Math.PI / 2)
  const cy = (sy + ty) / 2 + d * Math.sin(a - Math.PI / 2)
  return {
    midX: 0.25 * sx + 0.5 * cx + 0.25 * tx,
    midY: 0.25 * sy + 0.5 * cy + 0.25 * ty,
  }
}

function getNodeId(n) {
  return typeof n === 'string' ? n : n.id
}

function getLinkKey(link) {
  return `${getNodeId(link.source)}->${getNodeId(link.target)}`
}

/** Stable [0,1) per link so particles start out of sync */
function stableOffset01(str) {
  let h = 2166136261
  const s = String(str)
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619)
  return (h >>> 0) / 2 ** 32
}

function roundRectPath(ctx, x, y, w, h, rr) {
  const r = Math.min(rr, w / 2, h / 2)
  ctx.beginPath()
  if (typeof ctx.roundRect === 'function') {
    ctx.roundRect(x, y, w, h, r)
  } else {
    ctx.moveTo(x + r, y)
    ctx.arcTo(x + w, y, x + w, y + h, r)
    ctx.arcTo(x + w, y + h, x, y + h, r)
    ctx.arcTo(x, y + h, x, y, r)
    ctx.arcTo(x, y, x + w, y, r)
    ctx.closePath()
  }
}

export function ContractGraphRfg2d({
  graphData,
  highlightNodeIds = [],
  highlightLinkKeys = [],
  forceDark = false,
  onNodeClick,
  onLinkClick,
  onBackgroundClick,
  onReady,
}) {
  const fgRef = useRef()
  const containerRef = useRef(null)
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 })
  const dataRef = useRef(graphData)
  dataRef.current = graphData

  const isDark = useClmDarkMode(forceDark)
  const c = useMemo(() => (isDark ? PALETTE.dark : PALETTE.light), [isDark])

  const hlN = useMemo(() => new Set(highlightNodeIds), [highlightNodeIds.join('\u0001')])
  const hlL = useMemo(() => new Set(highlightLinkKeys), [highlightLinkKeys.join('\u0001')])

  const nodeCanvasObject = useCallback(
    (node, ctx, globalScale) => {
      if (node.x == null || node.y == null) return
      const val = Math.sqrt(Math.max(0, node.val ?? 1))
      const r = val * NODE_REL_SIZE
      const base = parseHexColor(getNodeColor(node.type))
      const isHl = hlN.has(node.id)

      if (isHl) {
        ctx.beginPath()
        ctx.arc(node.x, node.y, r + 9 / globalScale, 0, 2 * Math.PI)
        const glow = ctx.createRadialGradient(
          node.x,
          node.y,
          r * 0.12,
          node.x,
          node.y,
          r + 9 / globalScale
        )
        glow.addColorStop(0, rgba(base, 0.38))
        glow.addColorStop(1, rgba(base, 0))
        ctx.fillStyle = glow
        ctx.fill()
      }

      const lx = node.x - r * 0.38
      const ly = node.y - r * 0.38
      const grd = ctx.createRadialGradient(lx, ly, Math.max(0.5, r * 0.06), node.x, node.y, r)
      grd.addColorStop(
        0,
        rgba(
          {
            r: Math.min(255, base.r + 44),
            g: Math.min(255, base.g + 40),
            b: Math.min(255, base.b + 34),
          },
          1
        )
      )
      grd.addColorStop(1, rgba(base, 1))

      ctx.beginPath()
      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
      ctx.fillStyle = grd
      ctx.fill()
      ctx.strokeStyle = isDark
        ? rgba({ r: 255, g: 255, b: 255 }, 0.16)
        : rgba({ r: 255, g: 255, b: 255 }, 0.45)
      ctx.lineWidth = Math.max(0.65, 1.05 / globalScale)
      ctx.stroke()
      if (isHl) {
        ctx.strokeStyle = c.ringHl
        ctx.lineWidth = Math.max(0.95, 1.45 / globalScale)
        ctx.beginPath()
        ctx.arc(node.x, node.y, r + 2.4 / globalScale, 0, 2 * Math.PI)
        ctx.stroke()
      }
    },
    [hlN, isDark, c.ringHl]
  )

  const nodePointerAreaPaint = useCallback((node, color, ctx) => {
    if (node.x == null || node.y == null) return
    const val = Math.sqrt(Math.max(0, node.val ?? 1))
    const r = val * NODE_REL_SIZE + 5
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
    ctx.fill()
  }, [])

  /** Comet streak along edge + flicker (direction from link endpoints) */
  const linkDirectionalParticleCanvasObject = useCallback(
    (x, y, link, ctx, globalScale) => {
      const key = getLinkKey(link)
      const isHl = hlL.has(key)
      const s = link.source
      const t = link.target
      const sx = s?.x
      const sy = s?.y
      const tx = t?.x
      const ty = t?.y
      const dx = (tx ?? 0) - (sx ?? 0)
      const dy = (ty ?? 0) - (sy ?? 0)
      const len = Math.hypot(dx, dy) || 1
      const ux = dx / len
      const uy = dy / len

      const phase = stableOffset01(key) * Math.PI * 2
      const now =
        typeof performance !== 'undefined' ? performance.now() : Date.now()
      const flicker = 0.58 + 0.42 * Math.sin(now * 0.0055 + phase)
      const scale = Math.max(0.28, Math.sqrt(globalScale))
      const tailStep = (isHl ? 2.45 : 1.55) / scale
      const coreR = (isHl ? 2.05 : 1.35) / scale

      const tailLayers = isHl ? 5 : 4
      ctx.save()
      ctx.globalCompositeOperation = 'source-over'

      for (let i = tailLayers; i >= 1; i--) {
        const k = i / tailLayers
        const px = x - ux * tailStep * i * 0.92
        const py = y - uy * tailStep * i * 0.92
        const ri = coreR * (0.42 + 0.22 * k)
        const a = (isHl ? 0.3 : 0.16) * flicker * k ** 1.35
        if (isDark) {
          ctx.fillStyle = isHl
            ? `rgba(186, 230, 253, ${a * 0.95})`
            : `rgba(56, 189, 248, ${a * 0.8})`
        } else {
          ctx.fillStyle = isHl
            ? `rgba(59, 130, 246, ${a * 0.85})`
            : `rgba(125, 211, 252, ${a * 0.75})`
        }
        ctx.beginPath()
        ctx.arc(px, py, ri, 0, Math.PI * 2)
        ctx.fill()
      }

      const halo = ctx.createRadialGradient(x, y, 0, x, y, coreR * 2.15)
      if (isDark) {
        if (isHl) {
          halo.addColorStop(0, `rgba(255, 255, 255, ${0.9 * flicker})`)
          halo.addColorStop(0.4, `rgba(147, 197, 253, ${0.5 * flicker})`)
          halo.addColorStop(1, 'rgba(37, 99, 235, 0)')
        } else {
          halo.addColorStop(0, `rgba(248, 250, 252, ${0.85 * flicker})`)
          halo.addColorStop(0.5, `rgba(96, 165, 250, ${0.32 * flicker})`)
          halo.addColorStop(1, 'rgba(30, 58, 138, 0)')
        }
      } else if (isHl) {
        halo.addColorStop(0, `rgba(255, 255, 255, ${0.98 * flicker})`)
        halo.addColorStop(0.4, `rgba(96, 165, 250, ${0.45 * flicker})`)
        halo.addColorStop(1, 'rgba(37, 99, 235, 0)')
      } else {
        halo.addColorStop(0, `rgba(255, 255, 255, ${0.97 * flicker})`)
        halo.addColorStop(0.48, `rgba(125, 211, 252, ${0.38 * flicker})`)
        halo.addColorStop(1, 'rgba(59, 130, 246, 0)')
      }
      ctx.fillStyle = halo
      ctx.beginPath()
      ctx.arc(x, y, coreR * 2.15, 0, Math.PI * 2)
      ctx.fill()

      ctx.fillStyle = isHl
        ? `rgba(255, 255, 255, ${0.98 * flicker})`
        : isDark
          ? `rgba(241, 245, 249, ${0.94 * flicker})`
          : `rgba(255, 255, 255, ${0.99 * flicker})`
      ctx.beginPath()
      ctx.arc(x, y, coreR * 0.55, 0, Math.PI * 2)
      ctx.fill()

      ctx.restore()
    },
    [hlL, isDark]
  )

  const linkDirectionalParticles = useCallback(
    (link) => (hlL.has(getLinkKey(link)) ? 3 : 1),
    [hlL]
  )

  const linkDirectionalParticleSpeed = useCallback(
    (link) => {
      const key = getLinkKey(link)
      const hl = hlL.has(key)
      const j = stableOffset01(`${key}\0spd`)
      return hl ? 0.0039 + j * 0.0016 : 0.00125 + j * 0.00085
    },
    [hlL]
  )

  const linkDirectionalParticleOffset = useCallback(
    (link) => stableOffset01(getLinkKey(link)),
    []
  )

  useEffect(() => {
    if (!graphData?.nodes?.length) return
    const run = () => {
      const fg = fgRef.current
      if (!fg) return
      const link = fg.d3Force('link')
      link?.distance?.(52)
      link?.strength?.(0.76)
      const charge = fg.d3Force('charge')
      charge?.strength?.(-42)
      charge?.distanceMax?.(320)
    }
    run()
    const t = window.setTimeout(run, 100)
    const t2 = window.setTimeout(run, 400)
    return () => {
      window.clearTimeout(t)
      window.clearTimeout(t2)
    }
  }, [graphData])

  useEffect(() => {
    const el = containerRef.current
    if (!el || typeof ResizeObserver === 'undefined') return
    const applyRect = (cr) => {
      if (!cr) return
      const width = Math.max(0, Math.floor(cr.width))
      const height = Math.max(0, Math.floor(cr.height))
      setCanvasSize((prev) =>
        prev.width === width && prev.height === height ? prev : { width, height }
      )
    }
    const ro = new ResizeObserver((entries) => applyRect(entries[0]?.contentRect))
    applyRect(el.getBoundingClientRect())
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (canvasSize.width < 2 || canvasSize.height < 2) return
    const t = window.requestAnimationFrame(() => {
      fgRef.current?.d3ReheatSimulation?.()
    })
    return () => window.cancelAnimationFrame(t)
  }, [canvasSize.width, canvasSize.height])

  useEffect(() => {
    let cancelled = false
    const tryReady = () => {
      if (cancelled || !fgRef.current) return
      onReady?.({
        fitView: () => {
          try {
            fgRef.current?.zoomToFit(400, 56, () => true)
          } catch {
            /* ignore */
          }
        },
        nudgeRedraw: () => fgRef.current?.d3ReheatSimulation?.(),
        d3ReheatSimulation: () => {
          try {
            fgRef.current?.d3ReheatSimulation?.()
          } catch {
            /* ignore */
          }
        },
        pauseAnimation: () => {
          try {
            fgRef.current?.pauseAnimation?.()
          } catch {
            /* ignore */
          }
        },
        resumeAnimation: () => {
          try {
            fgRef.current?.resumeAnimation?.()
          } catch {
            /* ignore */
          }
        },
        reheatSimulation: () => {
          try {
            fgRef.current?.d3ReheatSimulation?.()
          } catch {
            /* ignore */
          }
        },
        focusNodeById: (id) => {
          const tryFocus = () => {
            const fg = fgRef.current
            const node = dataRef.current?.nodes?.find((n) => n.id === id)
            if (!fg || !node || node.x == null || node.y == null) return false
            fg.centerAt(node.x, node.y, 450)
            fg.zoom(3.8, 450)
            return true
          }
          if (tryFocus()) return
          window.setTimeout(tryFocus, 120)
          window.setTimeout(tryFocus, 380)
        },
      })
    }
    const id = window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        tryReady()
        window.setTimeout(tryReady, 120)
        window.setTimeout(tryReady, 600)
      })
    })
    return () => {
      cancelled = true
      window.cancelAnimationFrame(id)
    }
  }, [graphData, onReady])

  const onRenderFramePost = useCallback(
    (ctx, globalScale) => {
      const data = dataRef.current
      if (!data?.nodes?.length) return

      const showAllNodeLabels = globalScale >= ZOOM_NODE_LABELS_ALL
      const showEdgeLabels = globalScale >= ZOOM_EDGE_LABELS

      ctx.save()
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'

      for (const link of data.links) {
        const s = link.source
        const t = link.target
        if (s.x == null || s.y == null || t.x == null || t.y == null) continue

        const isHl = hlL.has(getLinkKey(link))
        if (!showEdgeLabels && !isHl) continue

        const { midX, midY } = linkLabelPosition(s.x, s.y, t.x, t.y, LINK_CURVATURE)
        const label = String(link.type ?? '').replace(/_/g, ' ')
        const edgeFont = Math.max(2.15, Math.min(4, 3.05 / globalScale))
        const fontStack = 'ui-sans-serif, system-ui, "Segoe UI", sans-serif'
        ctx.font = `600 ${edgeFont}px ${fontStack}`
        if ('letterSpacing' in ctx) {
          ctx.letterSpacing = `${0.04 / globalScale}px`
        }
        const padX = 3.6 / globalScale
        const padY = 1.25 / globalScale
        const tw = ctx.measureText(label).width
        const w = tw + padX * 2
        const h = edgeFont + padY * 2
        const x = midX - w / 2
        const y = midY - h / 2
        const rr = Math.min(h / 2, 5.5 / globalScale)

        const ox = 0.4 / globalScale
        const oy = 0.55 / globalScale
        roundRectPath(ctx, x + ox, y + oy, w, h, rr)
        ctx.fillStyle = c.edgeShadow
        ctx.fill()

        ctx.globalAlpha = isHl ? 1 : 0.94
        roundRectPath(ctx, x, y, w, h, rr)
        ctx.fillStyle = c.edgeFill
        ctx.fill()
        ctx.globalAlpha = 1
        roundRectPath(ctx, x, y, w, h, rr)
        ctx.strokeStyle = isHl ? c.edgeStrokeHl : c.edgeStroke
        ctx.lineWidth = Math.max(0.5, 0.85 / globalScale)
        ctx.stroke()
        ctx.fillStyle = isHl ? c.edgeTextHl : c.edgeText
        ctx.fillText(label, midX, midY)
        if ('letterSpacing' in ctx) {
          ctx.letterSpacing = '0px'
        }
      }

      for (const node of data.nodes) {
        const n = node
        if (n.x == null || n.y == null) continue

        const val = Math.sqrt(Math.max(0, n.val ?? 1))
        const r = val * NODE_REL_SIZE
        const isHl = hlN.has(n.id)
        if (!showAllNodeLabels && !isHl) continue

        const idStr = String(n.id)
        const text = idStr.length > 32 ? idStr.slice(0, 32) + '…' : idStr

        const fontSize = Math.max(2.6, Math.min(5.1, 3.95 / globalScale))
        ctx.font = `500 ${fontSize}px ui-sans-serif, system-ui, "Segoe UI", sans-serif`
        const ty = n.y + r + fontSize * 0.52 + 1.2 / globalScale

        ctx.lineJoin = 'round'
        ctx.miterLimit = 2
        ctx.lineWidth = Math.max(2.4, 3.4 / globalScale)
        ctx.strokeStyle = c.labelShadow
        ctx.strokeText(text, n.x, ty)
        ctx.fillStyle = isHl ? c.edgeTextHl : c.labelFill
        ctx.lineWidth = Math.max(0.5, 0.65 / globalScale)
        ctx.fillText(text, n.x, ty)
      }

      ctx.restore()
    },
    [hlN, hlL, c]
  )

  if (!graphData?.nodes?.length) return null

  const ready = canvasSize.width > 2 && canvasSize.height > 2

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 h-full min-h-0 w-full min-w-0 bg-slate-50 dark:bg-[#0f172a]"
    >
      {ready ? (
      <ForceGraph2D
        ref={fgRef}
        width={canvasSize.width}
        height={canvasSize.height}
        graphData={graphData}
        nodeId="id"
        nodeLabel={() => ''}
        linkLabel={() => ''}
        nodeRelSize={NODE_REL_SIZE}
        nodeVal={(n) => Math.sqrt(Math.max(0, n.val ?? 1))}
        nodeCanvasObjectMode={() => 'replace'}
        nodeCanvasObject={nodeCanvasObject}
        nodePointerAreaPaint={nodePointerAreaPaint}
        linkColor={(link) => (hlL.has(getLinkKey(link)) ? c.linkHl : c.link)}
        linkCurvature={LINK_CURVATURE}
        linkDirectionalArrowLength={3.15}
        linkDirectionalArrowRelPos={1}
        linkDirectionalArrowColor={(link) =>
          hlL.has(getLinkKey(link)) ? c.arrowHl : c.arrow
        }
        linkDirectionalParticles={linkDirectionalParticles}
        linkDirectionalParticleSpeed={linkDirectionalParticleSpeed}
        linkDirectionalParticleOffset={linkDirectionalParticleOffset}
        linkDirectionalParticleWidth={4.25}
        linkDirectionalParticleCanvasObject={linkDirectionalParticleCanvasObject}
        linkWidth={(link) => (hlL.has(getLinkKey(link)) ? 1.85 : 0.88)}
        onRenderFramePost={onRenderFramePost}
        onNodeClick={(node) => onNodeClick?.(node)}
        onNodeDragEnd={() => {
          const fg = fgRef.current
          if (fg?.d3AlphaTarget) fg.d3AlphaTarget(DRIFT_ALPHA_TARGET)
          if (fg) {
            const link = fg.d3Force('link')
            link?.distance?.(52)
            link?.strength?.(0.76)
            const charge = fg.d3Force('charge')
            charge?.strength?.(-42)
            charge?.distanceMax?.(320)
          }
        }}
        onLinkClick={(link) => onLinkClick?.(link)}
        onBackgroundClick={() => onBackgroundClick?.()}
        backgroundColor={c.canvasBg}
        enableNodeDrag
        cooldownTime={DRIFT_COOLDOWN_MS}
        d3AlphaDecay={0.014}
        d3VelocityDecay={0.2}
        d3AlphaTarget={DRIFT_ALPHA_TARGET}
      />
      ) : null}
    </div>
  )
}
