import { useQuery } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { CompanyCard } from "@/components/ui/CompanyCard"
import { fetchCompanies } from "@/lib/api"
import type { Company } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { useState } from "react"
import { CreateCompanyModal } from "@/components/CreateCompanyModal"

export function HomePage() {
  const { logout } = useAuth()
  const [createOpen, setCreateOpen] = useState(false)

  const { data, isLoading, error } = useQuery<Company[]>({
    queryKey: ["companies"],
    queryFn: fetchCompanies,
    refetchInterval: (query) =>
      query.state.data?.some((c) => c.status === "pending") ? 2000 : false,
  })

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl items-center justify-between p-4">
          <h1 className="text-xl font-semibold">Revo Case</h1>
          <div className="flex items-center gap-2">
            <Button onClick={() => setCreateOpen(true)}>Create</Button>
            <Button variant="outline" onClick={logout}>
              Log out
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl p-4">
        {isLoading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Loading…</span>
          </div>
        )}

        {error && (
          <p className="text-sm text-destructive">
            {error instanceof Error ? error.message : "Failed to load companies"}
          </p>
        )}

        {data && data.length === 0 && (
          <p className="text-muted-foreground">
            No companies yet. Click Create to add one.
          </p>
        )}

        {data && data.length > 0 && (
          <div className="flex flex-col gap-4">
            {data.map((company) => (
              <CompanyCard key={company.id} company={company} />
            ))}
          </div>
        )}
      </main>
      <CreateCompanyModal open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  )
}