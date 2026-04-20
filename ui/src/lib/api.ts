const API_URL = import.meta.env.VITE_API_URL

function authHeader(): Record<string, string> {
  const token = localStorage.getItem("token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
      ...(options.headers || {}),
    },
  })

  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `HTTP ${res.status}`)
  }

  return res.json() as Promise<T>
}

export async function apiLogin(username: string, password: string): Promise<string> {
  // OAuth2PasswordRequestForm = form-encoded, NOT JSON
  const body = new URLSearchParams({ username, password })

  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  })

  if (!res.ok) {
    throw new Error("Invalid username or password")
  }

  const data = (await res.json()) as { access_token: string }
  return data.access_token
}