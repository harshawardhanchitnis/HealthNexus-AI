export function operationalError(error: {error?: {detail?: unknown}}, fallback: string): string {
  const detail = error.error?.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object' && 'message' in detail && typeof detail.message === 'string') return detail.message;
  return fallback;
}
