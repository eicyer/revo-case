import { Loader2 } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Company, CompanyStatus, Competitor } from "@/lib/api"

const statusVariant: Record<
  CompanyStatus,
  "default" | "secondary" | "destructive"
> = {
  pending: "secondary",
  ready: "default",
  failed: "destructive",
}

export function CompanyCard({ company }: { company: Company }) {
  const websiteHref = company.website.startsWith("http")
    ? company.website
    : `https://${company.website}`

  return (
    <Card id={`company-${company.id}`} className="scroll-mt-4">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle>{company.name}</CardTitle>
            <CardDescription>
              {company.hq} ·{" "}
              <a
                href={websiteHref}
                target="_blank"
                rel="noreferrer"
                className="underline"
              >
                {company.website}
              </a>
            </CardDescription>
          </div>
          <Badge variant={statusVariant[company.status]}>
            {company.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        {company.status === "pending" && (
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Generating intel…</span>
          </div>
        )}

        {company.status === "failed" && (
          <p className="text-sm text-destructive">
            {company.error ?? "Unknown error"}
          </p>
        )}

        {company.status === "ready" &&
          company.summary &&
          company.competitors && (
            <div className="flex flex-col gap-6">
              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Summary
                </h3>
                <ul className="list-disc pl-5 space-y-1 text-sm">
                  {company.summary.map((bullet, i) => (
                    <li key={i}>{bullet}</li>
                  ))}
                </ul>
              </section>

              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Top competitors
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {company.competitors.map((comp, i) => (
                    <CompetitorMiniCard key={i} competitor={comp} />
                  ))}
                </div>
              </section>
            </div>
          )}
      </CardContent>
    </Card>
  )
}

function CompetitorMiniCard({ competitor }: { competitor: Competitor }) {
  return (
    <div className="rounded-md border p-3">
      {competitor.known_company_id !== null ? (
        <a
          href={`#company-${competitor.known_company_id}`}
          className="font-medium underline"
        >
          {competitor.name}
        </a>
      ) : (
        <span className="font-medium">{competitor.name}</span>
      )}
      <ul className="mt-2 list-disc pl-4 space-y-1 text-xs text-muted-foreground">
        {competitor.summary.map((bullet, i) => (
          <li key={i}>{bullet}</li>
        ))}
      </ul>
    </div>
  )
}