import { createContext, useContext, useState, type ReactNode } from "react"
import { apiLogin } from "./api"

type AuthContextValue = {
  token: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem("token"),
  )

  async function login(username: string, password: string) {
    const newToken = await apiLogin(username, password)
    localStorage.setItem("token", newToken)
    setToken(newToken)
  }

  function logout() {
    localStorage.removeItem("token")
    setToken(null)
  }

  const value: AuthContextValue = {
    token,
    isAuthenticated: token !== null,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (ctx === null) {
    throw new Error("useAuth must be used inside <AuthProvider>")
  }
  return ctx
}