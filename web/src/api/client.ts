import { API_URL } from '../config'
import { readAdminToken } from '../lib/adminToken'
import type {
  EvalRun,
  LlmCall,
  Market,
  Overview,
  RequestSummary,
  ShoppingRequest,
  ShoppingRequestBody,
} from './types'
import { parse, parseList, type SchemaName, type SchemaOf } from './validate'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function send(path: string, init?: RequestInit): Promise<Response> {
  const token = readAdminToken()
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null
    const detail = typeof body?.detail === 'string' ? body.detail : `request failed (${response.status})`
    throw new ApiError(response.status, detail)
  }
  return response
}

async function one<Name extends SchemaName>(name: Name, path: string, init?: RequestInit): Promise<SchemaOf<Name>> {
  return parse(name, await (await send(path, init)).json())
}

async function many<Name extends SchemaName>(name: Name, path: string, init?: RequestInit): Promise<SchemaOf<Name>[]> {
  return parseList(name, await (await send(path, init)).json())
}

export const api = {
  listMarkets: (signal?: AbortSignal): Promise<Market[]> => many('Market', '/markets', { signal }),

  submitRequest: (body: ShoppingRequestBody): Promise<ShoppingRequest> =>
    one('ShoppingRequest', '/shopping-requests', { method: 'POST', body: JSON.stringify(body) }),

  listRequests: (signal?: AbortSignal): Promise<RequestSummary[]> =>
    many('RequestSummary', '/shopping-requests?limit=200', { signal }),

  getRequest: (requestId: string, signal?: AbortSignal): Promise<ShoppingRequest> =>
    one('ShoppingRequest', `/shopping-requests/${encodeURIComponent(requestId)}`, { signal }),

  deleteRequest: async (requestId: string): Promise<void> => {
    await send(`/shopping-requests/${encodeURIComponent(requestId)}`, { method: 'DELETE' })
  },

  getObservability: (signal?: AbortSignal): Promise<Overview> => one('Overview', '/observability', { signal }),

  listEvalRuns: (signal?: AbortSignal): Promise<EvalRun[]> => many('EvalRun', '/observability/evals', { signal }),

  getRequestCalls: (requestId: string, signal?: AbortSignal): Promise<LlmCall[]> =>
    many('LlmCall', `/observability/requests/${encodeURIComponent(requestId)}/calls`, { signal }),
}
