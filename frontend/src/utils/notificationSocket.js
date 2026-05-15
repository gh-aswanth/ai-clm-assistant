/**
 * Singleton WebSocket client for background-task notifications.
 *
 * Multiple Vue components can call startNotifications() / onNotification()
 * independently; a single underlying WebSocket connection is shared and
 * automatically reconnected on disconnect.
 *
 * Inbound message schema:
 *   {
 *     type:        "chunking_started"|"chunking_done"|"chunking_failed"
 *                | "compliance_started"|"compliance_done"|"compliance_failed"
 *                | "scoring_started"|"scoring_done"|"scoring_failed"
 *                | "graph_build_started"|"graph_build_done"|"graph_build_failed",
 *     file_id:     number,
 *     contract_id: number | null,
 *     folder_id:   number | null,
 *     filename:    string,
 *     message:     string
 *   }
 */

const LISTENERS = new Set()

let _ws = null
let _reconnectTimer = null
let _shouldReconnect = false
let _refCount = 0

function _wsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/notifications`
}

function _connect() {
  if (_ws && (_ws.readyState === WebSocket.CONNECTING || _ws.readyState === WebSocket.OPEN)) return

  _ws = new WebSocket(_wsUrl())

  _ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      LISTENERS.forEach((fn) => {
        try { fn(msg) } catch (_) { /* listener errors must not crash the socket */ }
      })
    } catch (_) { /* ignore non-JSON frames */ }
  }

  _ws.onclose = () => {
    _ws = null
    if (_shouldReconnect) {
      _reconnectTimer = setTimeout(_connect, 3000)
    }
  }

  _ws.onerror = () => {
    _ws?.close()
  }
}

/** Call when a component mounts and wants to receive notifications. */
export function startNotifications() {
  _refCount++
  _shouldReconnect = true
  clearTimeout(_reconnectTimer)
  _connect()
}

/** Call when a component unmounts. Disconnects when no consumers remain. */
export function stopNotifications() {
  _refCount = Math.max(0, _refCount - 1)
  if (_refCount === 0) {
    _shouldReconnect = false
    clearTimeout(_reconnectTimer)
    _ws?.close()
    _ws = null
  }
}

/**
 * Register a callback for incoming notifications.
 * Returns an unsubscribe function.
 */
export function onNotification(fn) {
  LISTENERS.add(fn)
  return () => LISTENERS.delete(fn)
}
