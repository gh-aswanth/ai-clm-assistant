/** Public URL for graph JSON (respects Vite base path). */
export function graphDataPublicUrl() {
  const base = import.meta.env.BASE_URL || '/'
  const normalized = base.endsWith('/') ? base : `${base}/`
  return `${normalized}graph_data.json`
}
