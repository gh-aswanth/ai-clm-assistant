/**
 * Shared helpers to locate chunk text in PDF text layers or DOCX HTML previews
 * (same logic as Document Drive record preview).
 */

export const CHUNK_HL_MARK_CLASS = 'ddr-chunk-hl'

/** PDF text-layer spans: soft brand wash (no per-glyph dashed boxes). */
export const PDF_CHUNK_MARK_STYLE =
  'background:rgba(37,99,235,0.2)!important;box-shadow:inset 0 -2px 0 0 rgba(37,99,235,0.55);border-radius:3px;padding:1px 0;color:transparent!important;'

const SMART_SINGLE = '\u2018\u2019\u201A\u201B\u2032\u2035`'
const SMART_DOUBLE = '\u201C\u201D\u201E\u201F\u2033\u2036\u00AB\u00BB'
const DASHES = '\u2013\u2014\u2015\u2212'
const NBSP_CHARS = '\u00A0\u202F\u205F\u3000\uFEFF'

const LIGATURE_MAP = {
  '\ufb00': 'ff',
  '\ufb01': 'fi',
  '\ufb02': 'fl',
  '\ufb03': 'ffi',
  '\ufb04': 'ffl',
  '\ufb05': 'ft',
  '\ufb06': 'st',
}

export async function safeGetTextContent(page) {
  try {
    return await page.getTextContent()
  } catch {
    /* stream fallback */
  }
  try {
    const stream = page.streamTextContent()
    const reader = stream.getReader()
    const items = []
    const styles = Object.create(null)
    let lang = null
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      if (value) {
        lang = lang || value.lang
        Object.assign(styles, value.styles)
        items.push(...value.items)
      }
    }
    return { items, styles, lang }
  } catch (e) {
    console.warn('streamTextContent fallback failed:', e)
    return { items: [], styles: {}, lang: null }
  }
}

export function matMul(m, v) {
  return [
    m[0] * v[0] + m[2] * v[1],
    m[1] * v[0] + m[3] * v[1],
    m[0] * v[2] + m[2] * v[3],
    m[1] * v[2] + m[3] * v[3],
    m[0] * v[4] + m[2] * v[5] + m[4],
    m[1] * v[4] + m[3] * v[5] + m[5],
  ]
}

export function normalizeText(text) {
  for (const [lig, repl] of Object.entries(LIGATURE_MAP)) {
    text = text.replaceAll(lig, repl)
  }
  text = text.replace(/(?<=[a-zA-Z])P(?=[a-z])/g, 'ff')
  return text
}

function replaceChar(ch) {
  if (LIGATURE_MAP[ch]) return LIGATURE_MAP[ch]
  if (SMART_SINGLE.includes(ch)) return "'"
  if (SMART_DOUBLE.includes(ch)) return '"'
  if (DASHES.includes(ch)) return '-'
  if (ch === '\u2026') return '...'
  if (NBSP_CHARS.includes(ch)) return ' '
  const c = ch.charCodeAt(0)
  if (c >= 0x2000 && c <= 0x200b) return ' '
  return ch.toLowerCase()
}

function scrub(s) {
  let out = ''
  for (let i = 0; i < s.length; i++) out += replaceChar(s[i])
  return out.replace(/\s+/g, ' ').trim()
}

function finalizeRawTextMap(entries, raw) {
  const expanded = []
  for (let i = 0; i < raw.length; i++) {
    const rep = replaceChar(raw[i])
    for (let j = 0; j < rep.length; j++) expanded.push({ ch: rep[j], rawIdx: i })
  }

  let scrubbed = ''
  const scrubToRaw = []
  let prevSpace = true
  for (const item of expanded) {
    if (/\s/.test(item.ch)) {
      if (!prevSpace) {
        scrubbed += ' '
        scrubToRaw.push(item.rawIdx)
        prevSpace = true
      }
    } else {
      scrubbed += item.ch
      scrubToRaw.push(item.rawIdx)
      prevSpace = false
    }
  }
  if (scrubbed.endsWith(' ')) {
    scrubbed = scrubbed.slice(0, -1)
    scrubToRaw.pop()
  }

  return { entries, raw, scrubbed, scrubToRaw }
}

export function buildTextMap(doc, root) {
  const walkRoot = root || doc.body
  const walker = doc.createTreeWalker(walkRoot, NodeFilter.SHOW_TEXT, null)
  const entries = []
  let raw = ''
  let node
  while ((node = walker.nextNode())) {
    const start = raw.length
    raw += node.textContent
    entries.push({ node, start, end: raw.length })
  }

  return finalizeRawTextMap(entries, raw)
}

/**
 * PDF.js text layer: one span per item, joined with single spaces (no interleaved DOM
 * whitespace nodes). Keeps scrubbed text stable across resizes / rebuilds.
 */
export function buildTextMapForPdfTextLayer(root) {
  if (!root?.children?.length) return finalizeRawTextMap([], '')
  const spans = Array.from(root.children).filter((el) => el.tagName === 'SPAN')
  const entries = []
  let raw = ''
  for (let i = 0; i < spans.length; i++) {
    const span = spans[i]
    const node = span.firstChild
    if (!node || node.nodeType !== Node.TEXT_NODE) continue
    if (raw.length > 0) raw += ' '
    const start = raw.length
    raw += node.textContent
    entries.push({ node, start, end: raw.length })
  }
  return finalizeRawTextMap(entries, raw)
}

function pickDisambiguatedScrubStart(exactStarts, needleLen, scrubbedLen, matchHints) {
  if (exactStarts.length <= 1) return exactStarts[0] ?? -1
  const total = matchHints?.totalChunks
  if (total == null || total < 2 || !matchHints) return exactStarts[0]
  const idx = Math.max(0, Number(matchHints.chunkIndex) || 0)
  const denom = Math.max(1, total - 1)
  const target = (idx / denom) * Math.max(0, scrubbedLen - needleLen)
  return exactStarts.reduce((best, st) =>
    Math.abs(st - target) < Math.abs(best - target) ? st : best
  , exactStarts[0])
}

export function findSpan(textMap, needle, matchHints = null) {
  const sNeedle = scrub(needle)
  if (!sNeedle || sNeedle.length < 2) return null

  const rawSpan = (scrubIdx, scrubLen) => {
    const s = Math.min(scrubIdx, textMap.scrubToRaw.length - 1)
    const e = Math.min(scrubIdx + scrubLen - 1, textMap.scrubToRaw.length - 1)
    return { rawStart: textMap.scrubToRaw[s], rawEnd: textMap.scrubToRaw[e] + 1 }
  }

  const exactStarts = []
  let searchPos = 0
  while (searchPos <= textMap.scrubbed.length - sNeedle.length) {
    const i = textMap.scrubbed.indexOf(sNeedle, searchPos)
    if (i === -1) break
    exactStarts.push(i)
    searchPos = i + 1
  }
  if (exactStarts.length) {
    const pick = pickDisambiguatedScrubStart(
      exactStarts,
      sNeedle.length,
      textMap.scrubbed.length,
      matchHints
    )
    if (pick >= 0) return rawSpan(pick, sNeedle.length)
  }

  for (const ratio of [0.9, 0.8, 0.65, 0.5]) {
    const trimLen = Math.max(10, Math.floor(sNeedle.length * ratio))
    const sub = sNeedle.substring(0, trimLen)
    const i = textMap.scrubbed.indexOf(sub)
    if (i !== -1) {
      const tail = sNeedle.substring(sNeedle.length - Math.min(40, Math.floor(sNeedle.length * 0.25)))
      const tailSearch = tail.length >= 6 ? textMap.scrubbed.indexOf(tail, i) : -1
      if (tailSearch !== -1) {
        return rawSpan(i, tailSearch + tail.length - i)
      }
      const estEnd = Math.min(i + sNeedle.length, textMap.scrubbed.length)
      return rawSpan(i, estEnd - i)
    }
  }

  const headFrag = sNeedle.substring(0, Math.min(60, Math.floor(sNeedle.length * 0.35)))
  const tailFrag = sNeedle.substring(Math.max(sNeedle.length - 60, Math.ceil(sNeedle.length * 0.65)))

  const hIdx = headFrag.length >= 6 ? textMap.scrubbed.indexOf(headFrag) : -1
  const tIdx = tailFrag.length >= 6 ? textMap.scrubbed.indexOf(tailFrag, Math.max(0, hIdx)) : -1

  if (hIdx !== -1 && tIdx !== -1) {
    return rawSpan(hIdx, tIdx + tailFrag.length - hIdx)
  }
  if (hIdx !== -1) {
    const estEnd = Math.min(hIdx + sNeedle.length, textMap.scrubbed.length)
    return rawSpan(hIdx, estEnd - hIdx)
  }
  if (tIdx !== -1) {
    const estStart = Math.max(0, tIdx + tailFrag.length - sNeedle.length)
    return rawSpan(estStart, tIdx + tailFrag.length - estStart)
  }

  return null
}

export function collectSegments(textMap, rawStart, rawEnd) {
  const segments = []
  for (const entry of textMap.entries) {
    if (entry.end <= rawStart) continue
    if (entry.start >= rawEnd) break
    const segStart = Math.max(rawStart, entry.start) - entry.start
    const segEnd = Math.min(rawEnd, entry.end) - entry.start
    if (segEnd > segStart) {
      segments.push({ node: entry.node, offset: segStart, length: segEnd - segStart })
    }
  }
  return segments
}

export function wrapSegments(doc, segments) {
  const marks = []
  for (let i = segments.length - 1; i >= 0; i--) {
    const seg = segments[i]
    try {
      if (!seg.node.parentNode) continue
      const nodeLen = seg.node.textContent.length
      const off = Math.min(seg.offset, nodeLen)
      const end = Math.min(seg.offset + seg.length, nodeLen)
      if (end <= off) continue

      const mark = doc.createElement('mark')
      mark.className = CHUNK_HL_MARK_CLASS

      if (off === 0 && end >= nodeLen) {
        seg.node.parentNode.replaceChild(mark, seg.node)
        mark.appendChild(seg.node)
      } else {
        const range = doc.createRange()
        range.setStart(seg.node, off)
        range.setEnd(seg.node, end)
        try {
          range.surroundContents(mark)
        } catch {
          const fragment = range.extractContents()
          mark.appendChild(fragment)
          range.insertNode(mark)
        }
      }
      marks.unshift(mark)
    } catch {
      /* skip */
    }
  }
  return marks
}

export function clearHighlights(el) {
  try {
    const marks = el.querySelectorAll(`.${CHUNK_HL_MARK_CLASS}`)
    marks.forEach((mark) => {
      const parent = mark.parentNode
      while (mark.firstChild) parent.insertBefore(mark.firstChild, mark)
      parent.removeChild(mark)
      parent.normalize()
    })
  } catch {
    /* ignore */
  }
}

/** Injected into preview iframe `<head>` — shared by Contract detail + Document Drive. */
export function buildChunkHighlightMarkCss() {
  return `
    .${CHUNK_HL_MARK_CLASS} {
      background: linear-gradient(
        180deg,
        rgba(37, 99, 235, 0.11) 0%,
        rgba(37, 99, 235, 0.16) 100%
      ) !important;
      box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.22);
      border-radius: 4px;
      padding: 0.08em 0.14em;
      outline: none !important;
      -webkit-box-decoration-break: clone;
      box-decoration-break: clone;
      animation: clm-chunk-hl-fade 0.45s ease-out;
    }
    @keyframes clm-chunk-hl-fade {
      from { opacity: 0.35; }
      to   { opacity: 1; }
    }
    @media (prefers-reduced-motion: reduce) {
      .${CHUNK_HL_MARK_CLASS} { animation: none !important; }
    }
  `
}

export function injectHighlightStylesIntoDocument(doc) {
  if (!doc || doc.getElementById('ddr-hl-styles')) return
  const style = doc.createElement('style')
  style.id = 'ddr-hl-styles'
  style.textContent = buildChunkHighlightMarkCss()
  doc.head.appendChild(style)
}

export function cleanChunkForSearch(text) {
  return normalizeText(text.replace(/---\s*Page\s+\d+\s*---/gi, '').trim())
}

/** Whether chunk text can be found in the given root (e.g. current PDF text layer). */
export function chunkTextMatchesInRoot(root, chunk) {
  if (!root) return false
  try {
    const searchText = cleanChunkForSearch(chunk.content)
    if (!searchText || searchText.length < 3) return false
    const ownerDoc = root.ownerDocument || document
    const isPdfLayer =
      root.id === 'clm-pdf-text-layer' || root.getAttribute('data-clm-pdf-text-layer') === 'true'
    const textMap = isPdfLayer ? buildTextMapForPdfTextLayer(root) : buildTextMap(ownerDoc, root)
    /* Page scan: any occurrence is enough — no chunk_index disambiguation */
    return findSpan(textMap, searchText, null) !== null
  } catch {
    return false
  }
}

/**
 * Build transparent text spans for one PDF page (for chunk search / highlight).
 */
export async function appendPdfTextLayer(page, cssViewport, containerEl) {
  containerEl.querySelector('#clm-pdf-text-layer')?.remove()

  const textContent = await safeGetTextContent(page)
  if (!textContent.items.length) return

  const w = Math.floor(cssViewport.width)
  const h = Math.floor(cssViewport.height)
  const textDiv = document.createElement('div')
  textDiv.id = 'clm-pdf-text-layer'
  textDiv.setAttribute('data-clm-pdf-text-layer', 'true')
  textDiv.style.cssText = `position:absolute;left:0;top:0;width:${w}px;height:${h}px;overflow:hidden;pointer-events:none;z-index:5`

  const vt = cssViewport.transform
  for (const item of textContent.items) {
    if (!item.str) continue
    const tx = matMul(vt, item.transform)
    const fh = Math.hypot(tx[2], tx[3])
    const ascent = fh * 0.8
    const angle = Math.atan2(tx[1], tx[0])

    const span = document.createElement('span')
    span.textContent = normalizeText(item.str)
    let css = `position:absolute;left:${tx[4].toFixed(1)}px;top:${(tx[5] - ascent).toFixed(1)}px;font-size:${fh.toFixed(1)}px;font-family:sans-serif;color:transparent;white-space:pre;`
    if (Math.abs(angle) > 0.001) css += `transform:rotate(${(angle * 180 / Math.PI).toFixed(2)}deg);transform-origin:0% 0%;`
    span.style.cssText = css
    textDiv.appendChild(span)
  }

  const canvas = containerEl.querySelector('#pdf-canvas')
  if (canvas?.nextSibling) {
    containerEl.insertBefore(textDiv, canvas.nextSibling)
  } else {
    containerEl.appendChild(textDiv)
  }
}

/**
 * Locate chunk in preview: wrap match with highlight and scroll into view.
 * @returns {{ marks: HTMLElement[] }} highlight marks (may be empty)
 */
export function locateChunkInPreview({
  chunk,
  isPdf,
  getHighlightRoot,
  getPdfScrollEl,
  getPreviewIframe,
  matchHints = null,
}) {
  const root = getHighlightRoot()
  if (!root) return { marks: [] }

  try {
    const ownerDoc = root.ownerDocument || document
    clearHighlights(root)

    if (!isPdf) {
      const ifr = getPreviewIframe?.()
      const doc = ifr?.contentDocument || ifr?.contentWindow?.document
      if (doc) injectHighlightStylesIntoDocument(doc)
    }

    const searchText = cleanChunkForSearch(chunk.content)
    if (!searchText || searchText.length < 3) return { marks: [] }

    const isPdfLayer =
      isPdf &&
      (root.id === 'clm-pdf-text-layer' || root.getAttribute('data-clm-pdf-text-layer') === 'true')
    const textMap = isPdfLayer ? buildTextMapForPdfTextLayer(root) : buildTextMap(ownerDoc, root)
    const span = findSpan(textMap, searchText, matchHints)
    if (!span) return { marks: [] }

    const segments = collectSegments(textMap, span.rawStart, span.rawEnd)
    if (!segments.length) return { marks: [] }

    const pdfScrollEl = getPdfScrollEl?.()
    const previewIframe = getPreviewIframe?.()

    const marks = wrapSegments(ownerDoc, segments)
    if (isPdf) {
      marks.forEach((m) => {
        m.style.cssText = PDF_CHUNK_MARK_STYLE
      })
    }
    if (marks.length) {
      const first = marks[0]
      if (isPdf && pdfScrollEl) {
        const rect = first.getBoundingClientRect()
        const cRect = pdfScrollEl.getBoundingClientRect()
        pdfScrollEl.scrollTo({
          top: pdfScrollEl.scrollTop + rect.top - cRect.top - 60,
          behavior: 'smooth',
        })
      } else {
        first.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
    if (!isPdf) {
      previewIframe?.contentWindow?.getSelection()?.removeAllRanges()
    }
    return { marks }
  } catch (e) {
    console.warn('locateChunkInPreview:', e)
    return { marks: [] }
  }
}
