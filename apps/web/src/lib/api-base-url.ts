const localApiBaseUrl = "http://localhost:8000";

export function getServerApiBaseUrl() {
  return (
    process.env.API_URL ??
    process.env.API_INTERNAL_BASE_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    localApiBaseUrl
  );
}

export function getPublicApiBaseUrl() {
  return (
    process.env.NEXT_PUBLIC_API_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    localApiBaseUrl
  );
}

export function buildApiUrl(baseUrl: string, path: string) {
  return `${baseUrl.replace(/\/$/, "")}${path}`;
}
