let ws: WebSocket | null = null

export function connectWs(onMessage: (data: any) => void) {
  if (ws && ws.readyState === WebSocket.OPEN) return
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${proto}://${location.host}/ws/events`)
  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data))
    } catch (_) {
      /* ignore */
    }
  }
  ws.onclose = () => {
    setTimeout(() => connectWs(onMessage), 3000)
  }
}
