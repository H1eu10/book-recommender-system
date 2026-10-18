import type {
  RecommendationRequest,
  RecommendationResult,
} from '../types/recommendation'

interface ValidationIssue {
  msg: string
}

interface ApiError {
  detail?: string | ValidationIssue[]
}

export async function getRecommendations(
  preferences: RecommendationRequest,
  signal?: AbortSignal,
): Promise<RecommendationResult[]> {
  const response = await fetch('/api/recommendations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(preferences),
    signal,
  })

  if (!response.ok) {
    const body: ApiError | null = await response
      .json()
      .catch(() => null)

    let message = `Unable to get recommendations (HTTP ${response.status}).`

    if (typeof body?.detail === 'string') {
      message = body.detail
    } else if (Array.isArray(body?.detail)) {
      message = body.detail.map((issue) => issue.msg).join(' ')
    }

    throw new Error(message)
  }

  return response.json()
}