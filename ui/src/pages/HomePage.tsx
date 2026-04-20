import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"

export function HomePage() {
  const { logout } = useAuth()
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-4">
      <h1 className="text-2xl font-semibold">You're in.</h1>
      <Button variant="outline" onClick={logout}>
        Log out
      </Button>
    </div>
  )
}