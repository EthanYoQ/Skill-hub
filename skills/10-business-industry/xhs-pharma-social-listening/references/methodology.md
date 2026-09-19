# Methodology

## Data Model

- Search result: a note row returned by `opencli xiaohongshu search`.
- Note detail: title, author, content, likes, collects, comments, tags returned by `opencli xiaohongshu note`.
- Comment: top-level or reply returned by `opencli xiaohongshu comments`.

Raw item count is `search_results + note_details + comments`.

## Topic Dimensions

The analyzer uses rule-based first-pass tagging so every score is inspectable:

- Career insecurity and job-market friction.
- Sales/admin/KPI/PIP workload.
- Compliance and meeting execution pressure.
- Medical affairs, MSL/MA, clinical, and AI role pressure.
- Role boundary and cross-functional squeeze.
- Company alias, reputation, and information asymmetry.
- Compensation, bonus, welfare, and reimbursement.
- Data/RWE/clinical-domain learning curve.

## Reliability Rules

- High-confidence topics need multiple notes and comment validation.
- Single-note topics remain hypotheses even when the note is high heat.
- High-like low-comment posts can be awareness signals but should not dominate pain severity.
- Comments increase confidence only when they add independent experience, not just tags or jokes.
- Company alias mapping must be treated as ambiguous unless the note content disambiguates it.
