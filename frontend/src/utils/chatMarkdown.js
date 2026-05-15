import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.use({ gfm: true, breaks: true })

const MD_PURIFY = {
  USE_PROFILES: { html: true },
  ADD_TAGS: ['input'],
  ADD_ATTR: ['checked', 'disabled', 'type'],
}

/**
 * Wrap GFM tables for horizontal scroll (string-only — no DOM during render).
 */
function wrapChatMdTables(html) {
  if (!html || typeof html !== 'string') return html
  try {
    return html.replace(/<table\b[^>]*>[\s\S]*?<\/table>/gi, (block) =>
      block.includes('chat-md-table-wrap') ? block : `<div class="chat-md-table-wrap">${block}</div>`
    )
  } catch {
    return html
  }
}

export function renderMd(text) {
  const raw = marked.parse(typeof text === 'string' ? text : '', { async: false })
  return DOMPurify.sanitize(wrapChatMdTables(raw), MD_PURIFY)
}
