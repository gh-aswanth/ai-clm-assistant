/**
 * Latest document version on a contract (is_latest row, else last in list).
 * Matches contract detail / Kanban resolution.
 */
export function latestContractVersion(c) {
  const versions = c?.document_versions || []
  if (!versions.length) return null
  return versions.find((v) => v.is_latest) || versions.at(-1) || null
}

export function versionFileTypeLabel(v) {
  if (!v) return '—'
  let ft = (v.file_type || '').toLowerCase()
  if (!ft && v.file_path) {
    const ext = String(v.file_path).split('.').pop()
    ft = ext ? ext.toLowerCase() : ''
  }
  return ft || '—'
}
