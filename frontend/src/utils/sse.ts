// SSE 流式消费工具：用于 AI 应急方案生成进度推送
// 后端/AI 服务应以 text/event-stream 输出，每行格式：data: {json}\n\n

export interface SseOptions {
  /** 收到一个 chunk 的回调 */
  onMessage: (data: unknown) => void
  /** 连接建立 */
  onOpen?: () => void
  /** 出错 */
  onError?: (err: Event) => void
  /** 连接关闭 */
  onClose?: () => void
}

export interface SseController {
  close: () => void
}

/**
 * 打开一个 SSE 连接（GET 方式，token 通过 header 由浏览器自动携带 cookie；
 * 若后端要求 Authorization，可通过 withCredentials + 代理透传）。
 */
export function openSse(url: string, options: SseOptions): SseController {
  const source = new EventSource(url, { withCredentials: true })

  source.onopen = () => options.onOpen?.()

  source.onmessage = (ev: MessageEvent) => {
    try {
      const payload = JSON.parse(ev.data)
      options.onMessage(payload)
    } catch {
      // 非 JSON 文本直接透传
      options.onMessage(ev.data)
    }
  }

  source.onerror = (err: Event) => {
    options.onError?.(err)
    source.close()
  }

  return {
    close: () => source.close()
  }
}

/**
 * POST 方式的 SSE（部分 AI 服务需要 POST + body）。
 * 浏览器原生 EventSource 仅支持 GET，故用 fetch + ReadableStream 解析。
 */
export async function postSse(
  url: string,
  body: Record<string, unknown>,
  options: SseOptions,
  token?: string | null
): Promise<SseController> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }
  if (token) headers.Authorization = `Bearer ${token}`

  const resp = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body)
  })

  if (!resp.ok || !resp.body) {
    options.onError?.(new Event('fetch failed'))
    return { close: () => {} }
  }

  options.onOpen?.()
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const read = (): Promise<void> =>
    reader.read().then(({ done, value }) => {
      if (done) {
        options.onClose?.()
        return
      }
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() ?? ''
      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith('data:')) continue
        const json = line.slice(5).trim()
        if (!json) continue
        try {
          options.onMessage(JSON.parse(json))
        } catch {
          options.onMessage(json)
        }
      }
      return read()
    })

  void read()

  return {
    close: () => reader.cancel()
  }
}
