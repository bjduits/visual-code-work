# SAP Job Search — Belgium & Netherlands

## Goal
A repeatable process for finding currently-open SAP job opportunities (consultant,
functional, technical, project management) in Belgium and the Netherlands: which sites
to check, which specialist recruitment partners to contact, and how to determine when
each vacancy was posted so stale listings can be skipped.

## Inputs
- None (manual/browser-driven search — no API keys required for the sites below)
- Optional: a CV/profile to submit to recruiter portals once a target role is chosen

## Sources to check

### General job boards (both countries)
- **LinkedIn Jobs** — linkedin.com/jobs — filter by "Date posted" (past 24h / week / month).
  Best signal for freshness; every listing shows an exact relative post time.
- **Indeed** — be.indeed.com (Belgium) / nl.indeed.com (Netherlands) — search "SAP", filter
  by date posted.
- **Glassdoor** — glassdoor.com — good for salary context alongside listings.
- **StepStone** — stepstone.be / stepstone.nl — large local board, strong in BeLux/NL,
  shows "geplaatst op" (posted on) per listing.

### Belgium-specific
- **VDAB** (public employment service) — vdab.be
- **Jobat** — jobat.be (De Persgroep) — strong IT/SAP presence
- **References.be** — references.lesoir.be

### Netherlands-specific
- **Nationale Vacaturebank** — nationalevacaturebank.nl
- **Werkenvoor.nl / ICTerGezocht** — werkenvoor.nl, ictergezocht.nl — IT-focused
- **eXpatJobs Netherlands** — netherlands.expatjobs.eu — useful for non-Dutch-speaking
  candidates

### SAP-specialist boards
- **Eursap** — eursap.eu/sap-recruitment/belgium and /netherlands — SAP-only recruiter
  with a dedicated live vacancy feed; register a CV for automatic alerts.
- **SAP Careers** — careers.sap.com — SAP SE's own open roles (not client-side consultant
  roles, but relevant for in-house SAP positions).

## Specialist SAP recruitment partners (agencies)
Contact these directly and ask to be added to their SAP candidate pool — much of the SAP
contractor/permanent market in BE/NL moves through agencies rather than public postings.
See `SAP_Job_Search/findings/` for the current partner directory with names, phone
numbers, and addresses gathered on a given date — re-verify before calling, contact
details and staffing turn over.

Categories to search each time this directive is run:
1. SAP-only boutique recruiters (e.g. Eursap, GS-IT Recruitment) — smaller pool, deeper
   SAP-specific screening.
2. Generalist IT/professional recruiters with an SAP practice (e.g. Michael Page, Hays,
   Robert Half, Approach People) — broader client base, useful for permanent roles.
3. Dutch/Belgian staffing firms (e.g. YER, Yacht, USG Professionals, Randstad
   Professionals) — strong for interim/contract SAP roles specifically in the local
   market.

## Process
1. Run broad searches on the general boards (LinkedIn, Indeed, StepStone) filtered to
   "SAP" + country, sorted/filtered by most-recent posting date.
2. Check the SAP-specialist boards (Eursap, SAP Careers) for roles not mirrored on the
   general boards.
3. Re-verify each recruitment partner's current contact details (phone/email churn is
   common) via their own "Contact us" page before calling — do not rely on cached
   directory data older than ~a few months.
4. Call or email 2–3 relevant partners directly, referencing the specific SAP module/role
   of interest (e.g. SAP FI/CO, MM, S/4HANA, BTP, CPI) — specialist recruiters often have
   unlisted/unposted roles.
5. Record findings (site, role, location, posted date, contact used) in a dated file
   under `SAP_Job_Search/findings/`.

## Outputs
- A dated findings file: `SAP_Job_Search/findings/sap_jobs_be_nl_<YYYY-MM-DD>.md`
  containing the job board list, current open roles seen with posting dates, and the
  partner/contact directory as of that date.

## Edge Cases
- **Posting dates not shown**: many recruiter sites (Eursap included) show a job's
  **start date** or **Job ID**, not the date it was posted — don't confuse the two. LinkedIn
  and Indeed are the most reliable for an actual "posted X days ago" signal.
- **JS-heavy boards resist automated fetching**: StepStone and similar boards can time out
  or block non-browser fetches — treat those as "check manually in a browser" sources
  rather than something to scrape each run.
- **Stale directory data**: recruiter phone numbers/offices change; always confirm via the
  agency's own current "Contact us" page rather than trusting an old findings file.

## Notes
- This is a research aid for a personal job search, not a scraper/automation pipeline —
  each run is a manual pass through the sources above, refreshed and re-saved as a new
  dated findings file.
