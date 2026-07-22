// WebSocket 工具：用于灾情事件状态变更实时推送（后端 SSE/WS 二选一，此处用 WS）

export interface WsOptions {
  onOpen?: () => void
  onMessage: (data: unknown) => void
  onError?: (err: Event) => void
  onClose?: () => void
}

export interface WsController {
  send: (data: unknown) => void
  close: () => void
}

export function openWs(url: string, options: WsOptions, token?: string | null): WsController {
  const wsUrl = token ? `${url}?token=${encodeURIComponent(token)}` : url
  const ws = new WebSocket(wsUrl)

  ws.onopen = () => options.onOpen?.()
  ws.onmessage = (ev: MessageEvent) => {
    try {
      options.onMessage(JSON.parse(ev.data))
    } catch {
      options.onMessage(ev.data)
    }
  }
  ws.onerror = (err: Event) => options.onError?.(err)
  ws.onclose = () => options.onClose?.()

  return {
    send: (data: unknown) => ws.send(typeof data === 'string' ? data : JSON.stringify(data)),
    close: () => ws.close()
  }
}
