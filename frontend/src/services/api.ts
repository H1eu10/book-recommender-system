type ErrorCode = 'validation' | 'notFound' | 'unavailable' | 'network' | 'server'

export class ApiRequestError extends Error {
  code: ErrorCode
  constructor(code: ErrorCode) {
    super(code)
    this.code = code
  }
}

export async function requestJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(url, options)
  } catch (error) {
    if (options.signal?.aborted) throw error
    throw new ApiRequestError('network')
  }
  if (!response.ok) {
    throw new ApiRequestError(response.status === 422 ? 'validation'
      : response.status === 404 ? 'notFound'
        : response.status === 503 ? 'unavailable' : 'server')
  }
  return response.json() as Promise<T>
}

export function errorKey(error: unknown): string {
  return `errors.${error instanceof ApiRequestError ? error.code : 'server'}`
}
