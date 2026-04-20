const API_URL = import.meta.env.VITE_API_URL

export type CompanyStatus = "pending" | "ready" | "failed"

export type Competitor = {
  name: string
  summary: string[]
  known_company_id: number | null
}

export type Company = {
  id: number
  name: string
  hq: string
  website: string
  status: CompanyStatus
  summary: string[] | null
  competitors: Competitor[] | null
  error: string | null
  created_at: string
}

export type CompanyCreate = {
  name: string
  hq: string
  website: string
}

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

export function fetchCompanies(): Promise<Company[]> {
  return apiFetch<Company[]>("/companies")
}

export function createCompany(body: CompanyCreate): Promise<Company> {
  return apiFetch<Company>("/companies", {
    method: "POST",
    body: JSON.stringify(body),
  })
}