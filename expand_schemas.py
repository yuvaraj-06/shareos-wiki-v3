#!/usr/bin/env python3
"""Expand schema pages with detailed descriptions and nested object documentation."""

import json, re, sys

html = open('index.html').read()
for line in html.split('\n'):
    if line.strip().startswith('const PAGES'):
        data = line.strip()[len('const PAGES = '):]
        if data.endswith(';'):
            data = data[:-1]
        pages = json.loads(data)
        break

# Use unicode left single quote (char 8216) for code fences - wiki convention
Q = '\u2018'
QQ = Q*3  # triple quotes for code blocks

# ============================================================
# GOAL SCHEMA - EXPANDED
# ============================================================
GOAL_SCHEMA = f"""Goals are the primary valuation drivers in ShareOS. Every goal **IS a KPI** — quantifiable, measurable, with a target metric. Goals sit inside workstreams and contain milestones, which in turn contain tasks.

## Rules
- Every goal MUST be quantifiable and measurable
- ONE KPI per goal (no compound goals)
- Format: {Q}[Metric] [Target]{Q} — e.g., "ARR $2M", "D30 Retention 30%"
- If you can't measure it, it's not a goal
- Goals drive **performanceScore** (aggregate dollar valuation of goals completed)

## MongoDB Location
{QQ}
deals_internal.{{company}}.os_share.workstreams[].goals[]
{QQ}

## Complete Goal Fields (146 keys)

### Identity & Naming

| Key | Type | Description |
|-----|------|-------------|
| {Q}id{Q} | string | 8-character hex unique identifier (e.g., "a1b2c3d4"). Auto-generated on creation. Used for cross-referencing in depends_on, unlocks, and dependency arrays. |
| {Q}name{Q} | string | Goal name. Must be a measurable KPI expressed in under 5 words. Format: "[Metric] [Target]" e.g., "ARR $2M", "D30 Retention 30%", "LTV:CAC 3:1". This is the primary display label in dashboards and reports. |
| {Q}goal_description{Q} | string | Detailed paragraph (50+ words recommended) explaining what this goal measures, why it matters strategically, how it connects to the venture's stage and vertical, and what success looks like. Should provide enough context for any team member to understand the goal without additional explanation. |
| {Q}description{Q} | string | Alternate description field. Some ventures use this instead of goal_description. Contains the same type of content: strategic context, measurement criteria, and success definition. |
| {Q}goal_name{Q} | string | Alternate name field used by some data ingestion pipelines. Contains the same KPI-format name as the primary {Q}name{Q} field. |
| {Q}goal_id{Q} | string | Alternate ID field used by some external integrations. Maps to the primary {Q}id{Q} field for cross-system reconciliation. |

### Workstream & Classification

| Key | Type | Description |
|-----|------|-------------|
| {Q}WorkstreamName{Q} | string | Parent workstream name. One of: Product, Demand, Operations, Team, Partnerships, Investors, Synergy. This determines which execution lane the goal belongs to and affects weight calculations and agent routing. |
| {Q}workstream{Q} | string | Alternate workstream reference field. Contains the same workstream name in lowercase format (e.g., "product", "demand"). Used by some API endpoints. |
| {Q}workstreamIndex{Q} | integer | Zero-based numeric index of the parent workstream (0=Product, 1=Demand, 2=Operations, 3=Team, 4=Partnerships, 5=Investors, 6=Synergy). Used for array positioning and display ordering. |
| {Q}category{Q} | string | Goal category for grouping related goals within a workstream. Examples: "revenue", "retention", "acquisition", "infrastructure". Optional field used by some planning pipelines. |
| {Q}domain{Q} | string | Domain classification mapping to one of the seven performance verticals (Physical, Cognitive, Emotional, Social, Biological, Organizational, Financial). Links the goal to ShareOS's outcome framework. |
| {Q}vertical{Q} | string | Performance vertical this goal impacts. Same values as domain. Some ventures use vertical, others use domain — both map to the same seven verticals. |
| {Q}subdomain{Q} | string | Sub-domain within the vertical for more granular classification. Examples under Physical: "strength", "endurance", "recovery". Under Financial: "cash_flow", "risk", "allocation". |
| {Q}stage{Q} | string | Lifecycle stage this goal is appropriate for. One of: Explore, Generate, Validate, Pilot, Launch, Scale, Exit. Goals should match the venture's current stage per the KPI Matrix. |
| {Q}tags{Q} | array of strings | Classification tags for filtering and search. Examples: ["revenue", "q2", "high-priority", "ai-assisted"]. Free-form strings, no controlled vocabulary. |

### Status & Progress

| Key | Type | Description |
|-----|------|-------------|
| {Q}status{Q} | string | Current goal status. Values: "active" (being worked on), "completed" (KPI target achieved), "pending" (not yet started), "in-progress" (work underway but not complete), "blocked" (cannot proceed due to dependency or issue). Drives dashboard filtering and agent prioritization. |
| {Q}current_goal_metric_status{Q} | string | Current KPI value or narrative status. For numeric goals: the actual number (e.g., "1,247 MAU"). For qualitative goals: a status narrative (e.g., "Beta deployed, collecting feedback"). This is the primary "where are we now" indicator. |
| {Q}current_metric{Q} | string | Alternate current metric field. Contains the same measurement as current_goal_metric_status. Used by API responses and some dashboard components. |
| {Q}current{Q} | string | Shorthand alternate for current metric value. Typically just the number or short status. |
| {Q}target_goal_metric{Q} | string | Target KPI value that defines goal completion. For numeric goals: the target number (e.g., "10,000 MAU"). For qualitative goals: the success criterion (e.g., "PMF Score > 40%"). This is what "done" looks like. |
| {Q}target_metric{Q} | string | Alternate target metric field with the same target value. |
| {Q}target{Q} | string | Shorthand alternate for target value. |
| {Q}progress{Q} | number | 0-100 percentage indicating how close the goal is to completion. Calculated as (current_metric / target_metric) * 100 for numeric goals, or manually set for qualitative goals. |
| {Q}completionPercentage{Q} | number | Alternate completion percentage field. Same semantics as progress. Some pipelines write here instead. |
| {Q}goal_health{Q} | string | Health status indicator. Values: "on_track" (progressing as expected), "at_risk" (may miss target), "pivot_recommended" (strategy change needed), "pivoted" (strategy already changed), "paused" (temporarily halted), "killed" (abandoned). Drives alerting and escalation logic. |
| {Q}draft{Q} | boolean | Whether this goal is still in draft mode. Draft goals are not included in valuation calculations or agent assignments. Set to false when the goal is finalized and approved. |
| {Q}archived{Q} | boolean | Whether this goal has been archived. Archived goals are excluded from active dashboards and calculations but preserved for historical analysis and audit trails. |
| {Q}locked_by{Q} | string or null | Username or agent name that has locked this goal for editing. Prevents concurrent modifications. null means unlocked. Set automatically by the editing interface and released on save or timeout. |

### Rationale & Strategy

| Key | Type | Description |
|-----|------|-------------|
| {Q}rational_goal_reasoning{Q} | string | Detailed rationale (50+ words) for why this specific goal was chosen. Should reference market data, competitive positioning, stage-appropriate KPIs from the KPI Matrix, and how this goal moves the venture forward. Written by Planning Intelligence or human reviewers. |
| {Q}why{Q} | string | Strategic rationale in shorter form. Explains the "why" behind this goal's existence — what problem it solves, what opportunity it captures, or what risk it mitigates. |
| {Q}market_rationale{Q} | string | Market-level justification referencing TAM, competitive landscape, comparable companies, or industry benchmarks. Example: "Dental AI market growing at 23% CAGR; 10K providers represents 0.3% penetration of addressable market." |
| {Q}action_plan{Q} | string | High-level action plan describing the approach to achieve this goal. Not the granular task list (that's in milestones/tasks), but the strategic approach. Example: "Focus on dentist referral network with 3-tier pricing model." |
| {Q}strategicAlignment{Q} | string | How this goal aligns with the venture's overall strategy and ShareOS's mission. References the relevant vertical and horizontal intersection. |

### Priority & Ordering

| Key | Type | Description |
|-----|------|-------------|
| {Q}priority{Q} | string | Priority level: "high", "medium", or "low". This is a human override only — the system calculates priority mathematically from valuation impact. Only set when a human explicitly overrides the computed priority. |
| {Q}priority_order{Q} | number | Numeric rank within the workstream. 1 = highest priority. Computed from valuation impact, ROI, and strategic alignment. Used for ordering goals in dashboards and determining agent allocation. |
| {Q}priority_override{Q} | string or null | Human P0-P8 override label. null means the math decides priority. When set (e.g., "P0"), this takes absolute precedence over computed priority. Only Hamet or designated leads can set this. |
| {Q}order{Q} | integer | Display order for UI rendering. Separate from priority — this controls visual layout position. May differ from priority_order when goals are manually reordered in the dashboard. |
| {Q}position{Q} | integer | Position in list. Alternate ordering field. Some UI components use position instead of order. |
| {Q}ranking{Q} | integer | 1-10 ranking within the workstream based on valuation contribution. 1 = most valuable. Recalculated weekly by Planning Intelligence. |
| {Q}ranking_justification{Q} | string | Explanation of why this goal has its current ranking. References revenue potential, competitive advantage, strategic urgency, and dependency position. |
| {Q}rank{Q} | integer | Alternate ranking field. Same semantics as ranking. |
| {Q}rank_reasoning{Q} | string | Alternate ranking reasoning field. |
| {Q}overall_rank{Q} | integer | Global rank across ALL workstreams for this venture. 1 = single most valuable goal in the entire venture. Used for cross-workstream prioritization. |
| {Q}overall_rank_reasoning{Q} | string | Global rank reasoning explaining cross-workstream comparison. |
| {Q}overall_ranking{Q} | string | Overall ranking label (e.g., "Top 5", "Top 10"). Human-readable version of overall_rank. |

### Dependencies & Relationships

| Key | Type | Description |
|-----|------|-------------|
| {Q}depends_on{Q} | string, array, or null | Prerequisite goal ID(s) that must be completed before this goal can meaningfully begin. Can be a single ID string ("a1b2c3d4"), an array of IDs, or null if no dependencies. Critical for goal sequencing enforcement — revenue goals require prerequisite product and validation goals. |
| {Q}unlocks{Q} | array of strings | Goal IDs that become achievable after this goal completes. The inverse of depends_on. Example: completing "Product MVP Deployed" unlocks "First 100 Users" and "Beta Feedback Score". Used by the dependency graph visualizer. |
| {Q}dependencies{Q} | array of objects | Rich dependency objects with full context. See **Dependency Object** below. |
| {Q}relatedGoals{Q} | array of strings | Goal IDs that are related but not dependent. These goals inform each other or share resources but don't block each other. Used for contextual linking in the dashboard. |
| {Q}childGoals{Q} | array of strings | Sub-goal IDs if this goal has been decomposed. Rare — most decomposition happens at the milestone level. |
| {Q}parentWorkstreamId{Q} | string | ID of the parent workstream this goal belongs to. Used for upward traversal in the hierarchy. |

#### Dependency Object (inside {Q}dependencies{Q} array)

| Key | Type | Description |
|-----|------|-------------|
| {Q}goal_id{Q} | string | 8-char hex ID of the prerequisite goal. |
| {Q}goal_name{Q} | string | Human-readable name of the prerequisite goal for display. |
| {Q}type{Q} | string | "hard" (must complete first, blocks status transition) or "soft" (should complete first but generates warnings rather than blocking). |
| {Q}status{Q} | string | Current status of the prerequisite goal. Allows quick dependency health checks without additional queries. |
| {Q}workstream{Q} | string | Workstream of the prerequisite goal. Enables cross-workstream dependency visualization. |

### Timeline & Scheduling

| Key | Type | Description |
|-----|------|-------------|
| {Q}quarter{Q} | string | Target quarter: "Q1", "Q2", "Q3", "Q4", or empty string if not quarter-bound. Used for quarterly planning views and OKR alignment. |
| {Q}target_quarter{Q} | string | Alternate target quarter field. Same values as quarter. |
| {Q}estimated_deadline{Q} | string | Target completion date in MM/DD/YYYY format. Used for schedule tracking and executionScore calculation. |
| {Q}deadline{Q} | string | Alternate deadline field. Same format as estimated_deadline. |
| {Q}startDate{Q} | string | Date when work on this goal began or is planned to begin. ISO format or MM/DD/YYYY. Used for duration calculations. |
| {Q}endDate{Q} | string | Actual or planned end date. ISO format or MM/DD/YYYY. |
| {Q}estimated_time{Q} | string | Total hours estimate as a string (e.g., "120 hours"). Used when the estimate is provided as text rather than a number. |
| {Q}estimated_hours{Q} | number | Total hours estimate as a numeric value. Used for resource planning and cost calculations. Represents total effort across all milestones and tasks. |
| {Q}estimated_duration{Q} | string | Calendar duration estimate (e.g., "6 weeks", "3 months"). Distinct from hours — this accounts for parallel work and waiting time. |
| {Q}paybackPeriod{Q} | string | Estimated time to recoup the investment in this goal. Example: "4 months post-launch". Used in ROI analysis. |

### Cost & Budget

| Key | Type | Description |
|-----|------|-------------|
| {Q}estimated_cost{Q} | integer | Total estimated cost in USD to achieve this goal. Includes both agent and human costs. Used for budget planning and ROI calculations. |
| {Q}estimated_agent_cost{Q} | integer | Estimated cost of AI agent compute, API calls, and tooling in USD. Separated from human cost for AI vs human cost efficiency analysis. |
| {Q}estimated_human_cost{Q} | integer | Estimated cost of human labor in USD. Includes salaries, contractor fees, and external services. |
| {Q}cost_breakdown{Q} | object | Detailed cost breakdown object. Structure varies by venture but typically includes subcategories like development, marketing, infrastructure, and personnel with USD amounts for each. |
| {Q}costEstimate{Q} | integer | Alternate cost estimate field in USD. Same value as estimated_cost. Used by some dashboard components. |
| {Q}actual_cost{Q} | integer | Actual cost incurred to date in USD. Updated as milestones and tasks are completed. Used for budget variance analysis (actual vs estimated). |
| {Q}budgetAllocated{Q} | integer | Total budget allocated to this goal in USD. May differ from estimated_cost if budget was adjusted after initial planning. |
| {Q}budgetSpent{Q} | integer | Total budget spent to date in USD. Should equal or be less than budgetAllocated. Overspend triggers alerts in the QA pipeline. |

### Valuation & Scoring

| Key | Type | Description |
|-----|------|-------------|
| {Q}targetValuation{Q} | number | Dollar value (USD) this goal contributes to enterprise valuation if fully achieved. Calculated top-down: company targetValuation x workstream weight x goal's share within workstream. This is the primary valuation driver. |
| {Q}targetValuation_reasoning{Q} | string (50+ words) | Step-by-step valuation calculation. Must reference comparable companies, market multiples, or revenue projections. Example: "Based on dental AI SaaS comps at 12x revenue multiple, 10K providers at $200/mo ARPU = $24M ARR x 12x = $288M. This goal captures 15% of total value = $43.2M." |
| {Q}currentValuation{Q} | integer | Current valuation contribution in USD based on progress. Calculated as targetValuation x (performanceScore / 100). Represents what this goal has "earned" so far. Always say "current valuation" — never "realized valuation." |
| {Q}currentContribution{Q} | integer | Alternate field for current value contribution. Same semantics as currentValuation. |
| {Q}valuationImpact{Q} | number | Enterprise value impact in USD. This is Valuation Impact (Track 1) — what investors would pay. Distinct from socialValuationImpact. Never use bare "Impact" as a monetary metric label. |
| {Q}valuationImpactReasoning{Q} | string | Detailed explanation of enterprise value impact. References market multiples, revenue contribution, strategic positioning, and competitive moat building. |
| {Q}valuation_impact{Q} | integer | Legacy valuation impact field. Same as valuationImpact. Kept for backward compatibility with older data pipelines. |
| {Q}valuation_note{Q} | string | Additional notes about valuation methodology or assumptions for this goal. Free-form annotation for auditors. |
| {Q}valuation_rank{Q} | integer | Rank by valuation contribution within the workstream. 1 = highest valuation contributor. |
| {Q}socialValuationImpact{Q} | number | Societal value impact in USD. This is Social Valuation Impact (Track 2) — dollar contribution to health, wellbeing, avoided harm, or societal productivity outside the firm. Parallel to but independent from valuationImpact. |
| {Q}socialValuationImpactReasoning{Q} | string | Explanation of societal impact in dollar terms. Example: "Improving oral health for 10K patients reduces emergency dental visits by 30%, saving $2.4M in healthcare costs annually." |
| {Q}performanceScore{Q} | number | 0-100 score. Calculated as (current_metric / target_metric) x 100, weighted by goal importance. Reflects how well this goal is tracking against its KPI target. Not point-based scoring — derives from dollar valuation. |
| {Q}executionScore{Q} | number | 0-100 score. Formula: 50% milestone completion + 25% budget adherence + 25% schedule adherence. Measures execution quality independent of outcome. High execution + low performance = milestones aren't moving high-value goals. |
| {Q}roi{Q} | integer | Return on investment as a multiple (e.g., 10 = 10x return). Calculated as targetValuation / estimated_cost. Venture-stage goals should target 10x+. |
| {Q}roi_reasoning{Q} | string (50+ words) | Boardroom-grade financial reasoning. Must include specific numbers, named comparable companies, and defensible assumptions. Not generic statements. |
| {Q}roiPercentage{Q} | number | ROI expressed as a percentage (e.g., 1000 for 10x). Alternate representation for dashboards that prefer percentages. |

### Ownership & Assignment

| Key | Type | Description |
|-----|------|-------------|
| {Q}owner{Q} | object | The person responsible for this goal's success. Every goal MUST have an owner. Assigned by Planning Intelligence based on team roles and expertise. See **Owner Object** below. |
| {Q}assignee{Q} | string | Alternate assignee field. Just the person's name as a string (e.g., "Yuvaraj Tankala"). Used by integrations that don't support the full owner object. |
| {Q}humanReviewRequired{Q} | boolean | Whether this goal requires human review before key decisions. true for high-stakes goals (P0/P1 priority, >$1M valuation impact). Triggers review workflow notifications. |
| {Q}humanReviewStatus{Q} | string | Human review status: "pending", "approved", "rejected", "changes_requested". Only populated when humanReviewRequired is true. |
| {Q}humanResources{Q} | array of objects | Additional human resources needed beyond the owner. Each object: {{name, role, hours_needed, skills}}. Used for resource planning and workload balancing. |

#### Owner Object (inside {Q}owner{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}personId{Q} | string | UUID of the owner (e.g., "2b7496c1-xxxx-xxxx-xxxx-xxxxxxxxxxxx"). Links to the team directory for contact info, workload tracking, and cross-goal assignment audits. |
| {Q}name{Q} | string | Full name of the owner (e.g., "Yuvaraj Tankala", "Andreas Dierks"). Displayed in dashboards, reports, and notifications. |
| {Q}role{Q} | string | Role title or workstream assignment (e.g., "AI Engineering Lead", "Head of Operations", "Product"). Used for role-based filtering, capability matching, and workload balancing across goals. |

### KPIs & Metrics

| Key | Type | Description |
|-----|------|-------------|
| {Q}kpis{Q} | array of strings | List of KPI names tracked by this goal. Examples: ["Feature completion rate", "User satisfaction score", "Bug resolution time"]. Each KPI should correspond to a measurable, trackable metric. |
| {Q}kpi{Q} | object | KPI definition object with primary and secondary metrics. See **KPI Object** below. |
| {Q}kpi_target{Q} | string | Target value for the primary KPI (e.g., "95%", "$500K", "4.5 stars"). Human-readable target that maps to target_goal_metric. |
| {Q}kpiType{Q} | string | Type of KPI measurement: "revenue", "retention", "engagement", "satisfaction", "efficiency", "growth". Used for KPI categorization in cross-venture reports. |
| {Q}metric_type{Q} | string | Measurement type: "quantitative" (numbers), "qualitative" (assessments), "binary" (yes/no). Determines how progress and performanceScore are calculated. |
| {Q}metrics{Q} | object | Additional metrics object. Structure varies — may contain supplementary measurements relevant to this goal beyond the primary KPI. |
| {Q}metricUnit{Q} | string | Unit of measurement for the primary metric. Examples: "USD", "users", "percentage", "days", "score". Used for consistent formatting across dashboards. |
| {Q}keyResults{Q} | array of strings | OKR-style key results indicating goal progress. Example: ["Launch beta to 50 users", "Achieve 4.0+ rating", "Reach $10K MRR"]. More granular than the goal KPI but less granular than milestones. |

#### KPI Object (inside {Q}kpi{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}primary{Q} | string | Primary KPI metric name and target (e.g., "Monthly Active Users: 10,000"). The north star metric for this goal. This is the single number the goal lives or dies by. |
| {Q}secondary{Q} | string | Secondary KPI that supports the primary (e.g., "D7 Retention: 40%"). Provides additional context for goal health and helps detect gaming of the primary metric. |

### Source & Type

| Key | Type | Description |
|-----|------|-------------|
| {Q}source{Q} | string | Origin of this goal. Values: "planning-intelligence-step4" (auto-generated by PI), "human" (manually created), "gap-analysis" (identified by gap finder), "meeting-transcript" (extracted from meeting), "clawos-sync" (synced from WhatsApp). Enables audit trail. |
| {Q}type{Q} | string | "suggested" (AI-proposed, awaiting approval) or "existing" (confirmed and active). Suggested goals appear in review queues; existing goals are in active tracking and valuation calculations. |
| {Q}source_description{Q} | string | Additional detail about the source. Example: "Generated by Planning Intelligence Step 4 during weekly run on 2026-03-15. Based on gap analysis identifying missing demand metrics for Feno." |

### Quality & Risk

| Key | Type | Description |
|-----|------|-------------|
| {Q}confidenceScore{Q} | number | 0-100 confidence that this goal will be achieved by its deadline. Based on current progress rate, resource availability, dependency health, and identified risk factors. Updated weekly by Planning Intelligence. |
| {Q}qualityScore{Q} | number | 0-100 quality assessment of how well this goal is defined. Checks: measurability (is it a real KPI?), specificity (clear target?), owner assigned?, deadline present?, milestone coverage adequate? |
| {Q}riskLevel{Q} | string | Risk level: "low", "medium", "high", "critical". Assessed from dependency health, resource constraints, timeline pressure, and external factors. |
| {Q}riskMitigation{Q} | string | Documented mitigation strategy. Example: "If CAC exceeds $50, pivot to organic acquisition via content marketing and referral program." |
| {Q}risks{Q} | array of strings | Individual risk items. Each string describes one specific risk (e.g., "Key hire may not close by Q2", "API dependency on third party with no SLA"). |
| {Q}assumptions{Q} | array of strings | Key assumptions underlying this goal. If any proves false, the goal needs re-evaluation. Example: ["Market size >$1B", "CAC < $30", "Team ships MVP in 8 weeks"]. |

### Deliverables & Evidence

| Key | Type | Description |
|-----|------|-------------|
| {Q}deliverables{Q} | array | Deliverable items. Can be strings (simple descriptions like "Completed: Launch beta") or objects with structured fields. Must show WHO did WHAT, HOW, the RESPONSE, and the OUTCOME per the Deliverable Evidence Requirements. |
| {Q}deliverable{Q} | string | Legacy single deliverable field. Brief description of the primary deliverable. Superseded by the deliverables array for multiple items. |
| {Q}evidence{Q} | array of strings | Supporting evidence for progress/completion. Links to documents, screenshots, metrics dashboards, or external references that prove the claimed progress. |
| {Q}successCriteria{Q} | array of strings | Explicit criteria defining "done." Each criterion is testable. Example: ["NPS > 50", "Zero P1 bugs", "100% feature parity with v1"]. |

### AI & Automation

| Key | Type | Description |
|-----|------|-------------|
| {Q}aiTools{Q} | array of objects | AI tools and agents used for this goal. See **AI Tool Object** below. Tracks which AI capabilities are leveraged and their specific role in achieving the goal. |
| {Q}attributed_agents{Q} | array of strings | Names of AI agents that contributed work. Example: ["retention-churn-analyzer", "demand-signal-tester"]. Links to agent_matrix.agent_org_chart_v2 for agent details. |

#### AI Tool Object (inside {Q}aiTools{Q} array)

| Key | Type | Description |
|-----|------|-------------|
| {Q}name{Q} | string | Name of the AI tool or agent (e.g., "GPT-4", "retention-churn-analyzer", "SuperDesign", "Perplexity"). |
| {Q}type{Q} | string | Role classification: "automation" (executes tasks autonomously), "analysis" (provides insights and recommendations), "documentation" (generates documents/reports), "generation" (creates content, designs, or code). |

### Quality Audit & Adaptation

| Key | Type | Description |
|-----|------|-------------|
| {Q}syntax_warning{Q} | object | Automated naming and ordering warnings from the QA pipeline. See **Syntax Warning Object** below. Generated during Planning Intelligence quality checks. |
| {Q}goal_quality_audit{Q} | object | Comprehensive quality audit results from the QA agent. Contains scores, suggestions, and compliance checks against the KPI Matrix. Structure varies by audit version. |
| {Q}adaptations{Q} | array of objects | Append-only decision trail recording changes to this goal over time. Each entry records what changed, why, who decided, and when. Immutable once written — used for audit compliance and organizational learning. |
| {Q}pivot_signals{Q} | array of objects | Early warning signals that may indicate the need to pivot. Each entry includes signal type, severity, data source, and recommended action. |
| {Q}demotion_reason{Q} | string | Reason if this goal was demoted from a higher priority or moved to a lower-impact position. Recorded for accountability and post-mortem learning. |
| {Q}lessons_learned{Q} | array of strings | Lessons learned from working on this goal. Captured on completion or pivot. Fed back into Planning Intelligence for future goal generation improvement. |

#### Syntax Warning Object (inside {Q}syntax_warning{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}suggestion{Q} | string | Human-readable suggestion text explaining the issue (e.g., "Review task name — ensure it follows 'Active verb + specific deliverable' format (3-7 words)."). |
| {Q}nameChange{Q} | boolean | Whether the QA system recommends changing the goal's name. true = current name doesn't follow the "[Metric] [Target]" naming convention. |
| {Q}new_suggestion{Q} | string | Suggested replacement name if nameChange is true (e.g., "Achieve 10K Monthly Active Users"). Ready to apply directly. |
| {Q}reorder_change{Q} | boolean | Whether the QA system recommends reordering this goal within the workstream. true = current position doesn't match valuation-based rank. |
| {Q}reorder_reasoning{Q} | string | Explanation of why reordering is recommended. References valuation impact delta and priority calculations that drove the suggestion. |

### Feedback & Discussion

| Key | Type | Description |
|-----|------|-------------|
| {Q}feedback_summary{Q} | string | Consolidated evaluation with recommendations from reviewers or the QA agent. Summarizes strengths, weaknesses, and specific suggested improvements for this goal. |
| {Q}feedback{Q} | string or array | Feedback entries. Single string for simple feedback, or array of feedback objects with author, timestamp, and content for structured feedback trails. |
| {Q}feedbackHistory{Q} | array of objects | Complete chronological history of all feedback on this goal. Each entry preserves the reviewer name, timestamp, and full feedback text. Never deleted — append only. |
| {Q}comments{Q} | array of strings | Informal discussion comments from team members. Notes, questions, or observations that don't fit structured feedback. |
| {Q}notes{Q} | string | Free-form notes for anything that doesn't fit other fields. Often used for context humans want to preserve that has no dedicated field. |

### Output & Results

| Key | Type | Description |
|-----|------|-------------|
| {Q}output{Q} | string | Final output or deliverable description when the goal is completed. Summarizes what was produced and any artifacts created. |
| {Q}result{Q} | string | Result description documenting the outcome. Includes quantitative results (actual metrics achieved vs target) and qualitative assessment of success or failure. |
| {Q}thinking{Q} | string | AI reasoning trace. Contains the chain-of-thought or reasoning process used by AI agents when analyzing, scoring, or working on this goal. Preserved for auditability, debugging, and model improvement. |

### Metadata & Sync

| Key | Type | Description |
|-----|------|-------------|
| {Q}weight{Q} | number | Weight within the workstream (0.0 to 1.0). All goal weights within a workstream should sum to approximately 1.0. Determines how much of the workstream's valuation is attributed to this goal. Data-driven using PitchBook comparable company data, recalculated weekly. |
| {Q}created_at{Q} | string | ISO 8601 timestamp of when this goal was created (e.g., "2026-03-15T08:30:00Z"). |
| {Q}updated_at{Q} | string | ISO 8601 timestamp of last modification. Updated automatically on any field change. |
| {Q}completed_at{Q} | string | ISO 8601 timestamp of when status changed to "completed". null if not yet completed. |
| {Q}started_at{Q} | string | ISO 8601 timestamp of when work actually began. May differ from startDate (planned vs actual). |
| {Q}executed_at{Q} | string | ISO 8601 timestamp of last execution by an agent or human. Tracks recency of activity on this goal. |
| {Q}iterationCount{Q} | integer | Number of times this goal has been revised or iterated. Tracks goal maturity and stability. Higher counts may indicate unclear requirements. |
| {Q}_meta{Q} | object | Internal system metadata. Contains pipeline version, last processing timestamp, and processing flags. Not intended for human consumption — used by ClawOS orchestration. |
| {Q}clawos{Q} | object or boolean | ClawOS sync metadata. As object: contains sync status, last sync time, and source agent name. As boolean (true): simply indicates ClawOS has processed this goal at least once. |
| {Q}shareos_sync{Q} | object | ShareOS platform sync status. Tracks when this goal was last synced to external dashboards (agents.sharelabs.ai, Mission Control) and which data version was published. |
| {Q}data_sources{Q} | array of strings | Data sources used to create or update this goal. Examples: ["MongoDB deals_internal", "Looker Studio", "Fireflies transcript", "Shopify analytics"]. |
| {Q}external_references{Q} | array of strings | External URLs or document references. Links to research papers, product specs, competitor analysis, or third-party data supporting this goal. |
| {Q}tools_used{Q} | array of strings | Tools and platforms used in pursuing this goal. Examples: ["Vercel", "MongoDB", "SuperDesign", "Figma", "Perplexity"]. |
| {Q}stageGate{Q} | string | Stage gate status. Indicates whether this goal has passed its stage quality gate criteria per the Stage Quality Gates framework. |

### Children

| Key | Type | Description |
|-----|------|-------------|
| {Q}milestones{Q} | array of objects | Array of milestone objects nested under this goal. Each milestone follows the [[milestone-schema]]. Milestones are binary checkpoints that move the goal's KPI forward. A typical goal has 3-10 milestones. |
| {Q}workflow{Q} | array of objects | Workflow steps defining the execution sequence. See **Workflow Step Object** below. |

#### Workflow Step Object (inside {Q}workflow{Q} array)

| Key | Type | Description |
|-----|------|-------------|
| {Q}step{Q} | integer | Step number in the workflow sequence (1, 2, 3...). Defines execution order. Steps are processed sequentially by the orchestration layer. |
| {Q}action{Q} | string | Description of what needs to be done (e.g., "Review and understand the context: Analyze competitive landscape and identify positioning gaps"). Should be specific and actionable. |
| {Q}actor{Q} | string | Who performs this step: "human" (requires human execution), "ai_agent" (routed to an AI agent), or a specific agent name (e.g., "retention-churn-analyzer"). Determines routing in ClawOS. |
| {Q}approval_required{Q} | boolean | Whether human approval is needed before proceeding. true for high-stakes actions: deployments, external communications, financial transactions, or irreversible decisions. |
| {Q}owner{Q} | object | Owner of this specific workflow step. Same structure as Goal Owner Object: {{personId, name, role}}. May differ from the goal owner when steps are delegated to specialists. |
| {Q}tools_required{Q} | array of strings | Tools needed (e.g., ["MongoDB", "Vercel CLI", "Figma"]). Used for pre-execution resource checking and agent capability matching. |
| {Q}agent_output_deliverable{Q} | string | Expected deliverable from this step. Prefixed with a checkmark when complete. Example: "Context understood — decision or next action identified." |
| {Q}feedback{Q} | string | Guidance for the executor. Provides context on expectations, quality criteria, and common pitfalls. Example: "Clarify scope and expected outcome before proceeding." |
| {Q}ai_agent_name{Q} | string | Specific AI agent assigned to this step when actor is "ai_agent". Must match an agent name in the Agent Org Chart (clawos_cronjobs collection). |

## Goal vs Milestone

| | Goal | Milestone |
|-|------|-----------|
| Nature | Quantifiable KPI | Binary checkpoint |
| Example | "$500K MRR" | "Launch referral program" |
| Drives | performanceScore | executionScore |

## Goal Dependency Chain (Revenue)
{QQ}
1. Product exists (deployed)
2. Target customers identified (external ICP)
3. Outreach channel established
4. Interest signals captured
5. First paid transaction
6. Revenue goal (MRR/ARR)
{QQ}

**See also:** [[milestone-schema]], [[task-schema]], [[valuation-model]], [[evaluation-methodology]]"""


# ============================================================
# MILESTONE SCHEMA - EXPANDED
# ============================================================
MILESTONE_SCHEMA = f"""Milestones are binary checkpoints within a goal. Each moves the goal's KPI forward. They sit between goals and tasks in the hierarchy.

## Rules
1. Binary — done or not done. No partial milestones.
2. Moves parent goal's KPI forward measurably
3. Completable in 1-4 weeks
4. Must have a clear owner
5. Milestones drive **executionScore** (aggregate dollar valuation of milestones completed)

## MongoDB Location
{QQ}
deals_internal.{{company}}.os_share.workstreams[].goals[].milestones[]
{QQ}

## Complete Milestone Fields (99 keys)

### Identity & Naming

| Key | Type | Description |
|-----|------|-------------|
| {Q}id{Q} | string | 8-character hex unique identifier (e.g., "b2c3d4e5"). Auto-generated on creation. Referenced by tasks via parentMilestoneId. |
| {Q}name{Q} | string | Outcome-oriented checkpoint name. Should describe a verifiable outcome, not a process. Good: "Beta launched to 50 users". Bad: "Work on beta launch". 3-8 words typical. |
| {Q}milestone_description{Q} | string | Detailed paragraph (50+ words recommended) explaining what this milestone achieves, how it moves the parent goal's KPI forward, what "done" looks like, and any acceptance criteria. |
| {Q}description{Q} | string | Alternate description field. Contains the same type of content as milestone_description. Some data pipelines write here instead. |
| {Q}milestone_name{Q} | string | Alternate name field used by some integrations. Contains the same outcome-oriented name. |
| {Q}milestone_id{Q} | string | Alternate ID field for cross-system reconciliation. Maps to the primary {Q}id{Q} field. |
| {Q}milestone_type{Q} | string | Type classification for categorizing milestones. Examples: "technical", "business", "regulatory", "research". Used for filtering in workstream reports. |

### Status & Progress

| Key | Type | Description |
|-----|------|-------------|
| {Q}status{Q} | string | Current status. Values: "pending" (not started), "in_progress" (work underway), "completed" (verified done), "blocked" (cannot proceed). Binary nature means "in_progress" = tasks are being worked but milestone isn't done yet. |
| {Q}current_milestone_metric_status{Q} | string or integer | Current KPI value or completion indicator. For milestones with measurable sub-targets: the current number. For binary milestones: narrative status. |
| {Q}current_metric{Q} | string | Alternate current metric field. Same measurement as current_milestone_metric_status. |
| {Q}target_milestone_metric{Q} | string or integer | Target metric for this milestone. For binary milestones this might be "1" (done) or a specific threshold that must be crossed. |
| {Q}target_metric{Q} | string | Alternate target metric. |
| {Q}completion_pct{Q} | integer | 0-100 completion percentage. While milestones are binary (done/not done), this tracks task-level progress within the milestone. 100 = all tasks complete = milestone done. |
| {Q}completionPercentage{Q} | number | Alternate completion percentage field. Same semantics as completion_pct. |
| {Q}progress{Q} | number | Progress percentage. Another alternate for completion tracking, used by some dashboard components. |

### Rationale & Reasoning

| Key | Type | Description |
|-----|------|-------------|
| {Q}rational_milestone_reasoning{Q} | string | Detailed rationale (50+ words) for why this milestone exists and how it moves the parent goal forward. Should reference the goal's KPI and explain the causal link between completing this milestone and improving that KPI. |

### Valuation & Scoring

| Key | Type | Description |
|-----|------|-------------|
| {Q}targetValuation{Q} | integer | Dollar value (USD) this milestone contributes to the parent goal's valuation when completed. Inherited top-down from the goal's targetValuation, distributed across milestones by importance. |
| {Q}targetValuation_reasoning{Q} | string (50+ words) | Step-by-step calculation of how this milestone's valuation was derived from the parent goal. Must show the math: goal value x milestone share = milestone value, with justification for the share percentage. |
| {Q}currentValuation{Q} | integer | Current valuation contribution in USD. For binary milestones: 0 (not done) or targetValuation (done). For milestones with sub-metrics: proportional to completion. |
| {Q}valuationImpact{Q} | integer | Enterprise value impact in USD (Valuation Impact Track 1). Same as targetValuation for most milestones. |
| {Q}valuationImpactReasoning{Q} | string | Explanation of how this milestone specifically impacts enterprise value. References the parent goal's valuation model. |
| {Q}socialValuationImpact{Q} | integer | Societal value impact in USD (Social Valuation Impact Track 2). The dollar value of health, wellbeing, or societal benefit this milestone enables. |
| {Q}socialValuationImpactReasoning{Q} | string | Explanation of societal impact. Example: "Deploying the screening tool to 500 clinics enables early detection for ~12,000 patients, avoiding ~$3.6M in emergency treatment costs." |
| {Q}performanceScore{Q} | integer | 0-100. Weighted task completion score reflecting how well the milestone's sub-tasks are performing against their targets. |
| {Q}executionScore{Q} | integer | 0-100. Formula: 50% on-time delivery + 25% time efficiency + 25% budget adherence. Measures execution quality for this milestone. |
| {Q}roi{Q} | integer | ROI as a multiple. Calculated as targetValuation / estimated_cost for this milestone specifically. |
| {Q}roi_reasoning{Q} | string (50+ words) | Boardroom-grade justification with specific numbers, comparable benchmarks, and financial assumptions behind the ROI calculation. |
| {Q}roiPercentage{Q} | number | ROI expressed as a percentage. |

### Ranking & Ordering

| Key | Type | Description |
|-----|------|-------------|
| {Q}ranking{Q} | integer | 1-10 ranking within the parent goal based on valuation contribution and strategic sequence. 1 = most critical milestone. |
| {Q}ranking_justification{Q} | string | What this milestone unlocks and why it ranks where it does. References dependency chains and value creation sequence. |
| {Q}overall_ranking{Q} | string | Global ranking label across the entire venture. Example: "Top 20". Used for cross-workstream prioritization. |
| {Q}position{Q} | integer | Display position in the UI. Controls visual ordering. May differ from ranking when milestones are manually resequenced. |

### Ownership

| Key | Type | Description |
|-----|------|-------------|
| {Q}owner{Q} | object | Person responsible for this milestone. See **Owner Object** below. Every milestone MUST have an owner, assigned based on team expertise and workload. |
| {Q}owner_role{Q} | string | Shorthand role of the owner (e.g., "Product", "Engineering"). Used when the full owner object is not available. |

#### Owner Object (inside {Q}owner{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}personId{Q} | string | UUID of the owner. Links to team directory for contact info and cross-milestone workload tracking. |
| {Q}name{Q} | string | Full name (e.g., "Yuvaraj Tankala"). Displayed in milestone cards, reports, and notification routing. |
| {Q}role{Q} | string | Role title (e.g., "AI Engineering Lead"). Used for role-based assignment validation — milestones should match the owner's domain expertise. |

### Timeline & Cost

| Key | Type | Description |
|-----|------|-------------|
| {Q}estimated_deadline{Q} | string | Target completion date in MM/DD/YYYY format. Should be within 1-4 weeks of the milestone start. Used for schedule adherence in executionScore. |
| {Q}deadline{Q} | string | Alternate deadline field. Same format as estimated_deadline. |
| {Q}startDate{Q} | string | Planned or actual start date. ISO format or MM/DD/YYYY. |
| {Q}endDate{Q} | string | Planned or actual end date. ISO format or MM/DD/YYYY. |
| {Q}due_date{Q} | string | Alternate due date field. |
| {Q}estimated_time{Q} | string | Hours estimate as string (e.g., "40 hours"). Represents total effort for all tasks under this milestone. |
| {Q}estimated_hours{Q} | number | Hours estimate as numeric value. Used for resource planning calculations. |
| {Q}estimated_cost{Q} | integer | Total cost estimate in USD for completing this milestone. Sum of all task costs. |
| {Q}costEstimate{Q} | integer | Alternate cost estimate field in USD. |
| {Q}actual_cost{Q} | integer | Actual cost incurred to date in USD. Updated as tasks complete. Compared against estimate for budget adherence scoring. |
| {Q}budgetAllocated{Q} | integer | Budget allocated in USD. May be adjusted from initial estimate. |
| {Q}budgetSpent{Q} | integer | Budget spent to date in USD. Triggers alerts when approaching or exceeding budgetAllocated. |
| {Q}sprint{Q} | string | Sprint assignment (e.g., "Sprint 14", "2026-W15"). Used for agile planning and sprint-level tracking. |

### Source & Type

| Key | Type | Description |
|-----|------|-------------|
| {Q}type{Q} | string | "suggested" (AI-proposed) or "existing" (confirmed). Suggested milestones are pending review; existing milestones are active. |
| {Q}source{Q} | string | Origin of this milestone (e.g., "planning-intelligence", "human", "gap-analysis", "meeting-transcript"). |
| {Q}source_description{Q} | string | Additional details about the source. Provides context for how and when this milestone was created. |

### Quality Audit

| Key | Type | Description |
|-----|------|-------------|
| {Q}syntax_warning{Q} | object | Automated QA warnings. See **Syntax Warning Object** below. |
| {Q}feedback_summary{Q} | string | Consolidated evaluation with recommendations. Summarizes quality issues and suggested improvements. |
| {Q}feedback{Q} | string or array | Individual feedback entries from reviewers or QA agents. |

#### Syntax Warning Object (inside {Q}syntax_warning{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}suggestion{Q} | string | Human-readable suggestion explaining the naming or ordering issue detected. |
| {Q}nameChange{Q} | boolean | true if the milestone name should be revised to follow outcome-oriented naming conventions. |
| {Q}new_suggestion{Q} | string | Suggested replacement name if nameChange is true. |
| {Q}reorder_change{Q} | boolean | true if this milestone should be reordered within the goal based on dependency sequence or valuation. |
| {Q}reorder_reasoning{Q} | string | Explanation of why reordering is recommended with specific valuation or sequencing rationale. |

### Deliverables & Content

| Key | Type | Description |
|-----|------|-------------|
| {Q}deliverable{Q} | string | Primary deliverable description. What artifact or outcome this milestone produces. |
| {Q}deliverables{Q} | array | Multiple deliverable items. Can be strings or structured objects with evidence fields. |
| {Q}agent_output_deliverable{Q} | string | Specific deliverable produced by an AI agent for this milestone. Marked with checkmark when delivered. |
| {Q}key_outcomes{Q} | array | Key outcomes expected from this milestone. Each item describes one specific measurable or verifiable outcome. |
| {Q}links{Q} | array | URLs to relevant resources, documents, or tools needed for this milestone. |
| {Q}pending_items{Q} | array | Items still pending completion within this milestone. Used for tracking remaining work. |
| {Q}notes{Q} | string | Free-form notes for additional context that doesn't fit other fields. |
| {Q}thinking{Q} | string | AI reasoning trace. Chain-of-thought used by agents when analyzing or working on this milestone. |

### AI Tools

| Key | Type | Description |
|-----|------|-------------|
| {Q}aiTools{Q} | array | AI tools used for this milestone. Each item: {{name: string, type: "automation"/"analysis"/"documentation"/"generation"}}. |
| {Q}added_agent{Q} | string | Name of the AI agent that created or last modified this milestone. For audit trail tracking. |

### Dependencies

| Key | Type | Description |
|-----|------|-------------|
| {Q}dependencies{Q} | array | Prerequisite milestones or goals that must complete first. Can be ID strings or structured objects with {{id, name, type, status}}. |
| {Q}workstream{Q} | string | Parent workstream name. Inherited from the parent goal but stored here for direct queries without parent traversal. |
| {Q}workstreams{Q} | array | Multi-workstream references if this milestone spans multiple workstreams. Rare but used for cross-functional milestones. |

### Metadata & Sync

| Key | Type | Description |
|-----|------|-------------|
| {Q}created_at{Q} | string | ISO 8601 creation timestamp. |
| {Q}updated_at{Q} | string | ISO 8601 last modification timestamp. |
| {Q}completed_at{Q} | string | ISO 8601 completion timestamp. null if not yet completed. |
| {Q}activity{Q} | array | Activity log entries tracking changes, status transitions, and agent interactions. Each entry has timestamp, actor, and description. |
| {Q}_meta{Q} | object | Internal system metadata. Pipeline version, processing timestamps, and flags. Not for human consumption. |
| {Q}clawos{Q} | object or boolean | ClawOS sync metadata. Object with sync details or boolean true indicating processing. |
| {Q}shareos_sync{Q} | object | ShareOS platform sync status. Tracks dashboard publication timestamps and versions. |

### Children

| Key | Type | Description |
|-----|------|-------------|
| {Q}tasks{Q} | array of objects | Array of task objects nested under this milestone. Each task follows the [[task-schema]]. Tasks are atomic units of work. A typical milestone has 2-8 tasks. |

**See also:** [[goal-schema]], [[task-schema]], [[owner-schema]], [[valuation-model]]"""


# ============================================================
# TASK SCHEMA - EXPANDED
# ============================================================
TASK_SCHEMA = f"""Tasks are the smallest executable units of work in ShareOS. One person, one deliverable. They sit under milestones in the hierarchy.

## Rules
- Smallest executable unit of work — cannot be broken down further
- Has: owner, deadline, status, estimated hours
- One person can complete one task
- Active verb + specific deliverable naming (3-7 words)
- Examples: "Build referral landing page", "Set up analytics tracking", "Draft investor email template"

## MongoDB Location
{QQ}
deals_internal.{{company}}.os_share.workstreams[].goals[].milestones[].tasks[]
{QQ}

## Complete Task Fields (109 keys)

### Identity & Naming

| Key | Type | Description |
|-----|------|-------------|
| {Q}id{Q} | string | 8-character hex unique identifier (e.g., "c3d4e5f6"). Auto-generated on creation. Referenced by dependency arrays and workflow steps. |
| {Q}name{Q} | string | Task name following "Active verb + specific deliverable" format, 3-7 words. Must start with an action verb. Good: "Build referral landing page", "Configure Stripe webhooks". Bad: "Landing page", "Stripe stuff". |
| {Q}task_description{Q} | string | Detailed description of how this task fulfills the parent milestone. Explains the specific work to be done, acceptance criteria, and how completion is verified. Should be detailed enough for any team member to pick up and execute. |
| {Q}description{Q} | string | Alternate description field. Same content type as task_description. Used by some data pipelines. |
| {Q}task_name{Q} | string | Alternate name field. Contains the same action-oriented task name. |
| {Q}task_id{Q} | string | Alternate ID for cross-system reconciliation. |

### Status & Progress

| Key | Type | Description |
|-----|------|-------------|
| {Q}status{Q} | string | Current task status. Values: "pending" (queued, not started), "in_progress" (actively being worked on), "completed" (done and verified), "blocked" (cannot proceed due to dependency, missing resource, or external blocker). |
| {Q}blocked{Q} | boolean | Explicit blocked flag. true when the task cannot proceed. Supplements the "blocked" status value and may include tasks that are in_progress but partially blocked. |
| {Q}current_task_metric_status{Q} | string | Current completion status or progress metric. For binary tasks: status narrative. For measurable tasks: current value. |
| {Q}current_metric{Q} | string | Alternate current metric field. |
| {Q}target_task_metric{Q} | string | Target metric that defines task completion. For most tasks this is binary (done/not done), but some have measurable targets. |
| {Q}target_metric{Q} | string | Alternate target metric. |

### Time & Effort

| Key | Type | Description |
|-----|------|-------------|
| {Q}estimated_hours{Q} | number | Realistic hours estimate for task completion (typically 2-40 hours). Used for resource planning, cost calculation (hours x rate), and schedule adherence scoring. Should reflect actual effort, not calendar time. |
| {Q}estimated_time{Q} | string | Hours estimate as string format (e.g., "8 hours", "2 days"). Used when estimates come from text-based sources. |
| {Q}estimated_effort{Q} | string | Effort classification (e.g., "low", "medium", "high", or "S/M/L/XL" t-shirt sizing). Higher-level estimate when precise hours aren't available. |
| {Q}effort{Q} | string | Alternate effort classification field. |
| {Q}actual_hours{Q} | number | Actual hours spent on this task. Updated on completion. Compared against estimated_hours for estimation accuracy tracking and future estimate calibration. |
| {Q}estimated_deadline{Q} | string | Target completion date in MM/DD/YYYY format. Should be realistic given the estimated_hours and the assignee's workload. |
| {Q}deadline{Q} | string | Alternate deadline field. Same format. |
| {Q}due_date{Q} | string | Alternate due date field. |
| {Q}startDate{Q} | string | Date when work on this task began or is planned to begin. ISO format or MM/DD/YYYY. |
| {Q}endDate{Q} | string | Actual or planned end date. ISO format or MM/DD/YYYY. |
| {Q}sprint{Q} | string | Sprint assignment (e.g., "Sprint 14", "2026-W15"). Links the task to a specific sprint cycle for agile tracking. |
| {Q}sprint_goal{Q} | string | Sprint-level goal this task contributes to. Provides context for how this task fits into the broader sprint objective. |

### Cost & Budget

| Key | Type | Description |
|-----|------|-------------|
| {Q}estimated_cost{Q} | integer | Estimated cost in USD. Typically estimated_hours x hourly rate. For AI tasks: compute cost estimate. |
| {Q}cost_estimate{Q} | integer | Alternate cost estimate field in USD. |
| {Q}cost{Q} | integer | Simple cost value in USD. Used when only a single cost number is needed. |
| {Q}cost_breakdown{Q} | object | Detailed cost breakdown with subcategories. Structure: {{labor: int, compute: int, tools: int, ...}} amounts in USD. Varies by task type. |
| {Q}costEstimate{Q} | integer | Another alternate cost estimate. Multiple cost fields exist for compatibility with different data sources. |
| {Q}actual_cost{Q} | integer | Actual cost incurred in USD. Updated on completion. Used for budget variance analysis. |
| {Q}budgetAllocated{Q} | integer | Budget allocated to this specific task in USD. |
| {Q}budgetSpent{Q} | integer | Budget spent to date in USD. Should not exceed budgetAllocated. |

### Ownership & Assignment

| Key | Type | Description |
|-----|------|-------------|
| {Q}owner{Q} | object | Person or agent responsible for executing this task. See **Owner Object** below. Every task MUST have an owner. For AI-executed tasks, this may be the supervising human. |
| {Q}assignee{Q} | string | Alternate assignee as a simple name string (e.g., "Yuvaraj Tankala"). Used by integrations without full owner object support. |

#### Owner Object (inside {Q}owner{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}personId{Q} | string | UUID of the task owner. Links to team directory. Used for workload tracking across all tasks assigned to this person. |
| {Q}name{Q} | string | Full name of the task owner (e.g., "Yuvaraj Tankala"). Displayed on task cards and in assignment notifications. |
| {Q}role{Q} | string | Role title (e.g., "AI Engineering Lead", "Designer"). Used to validate that the task is assigned to someone with appropriate skills for the work. |

### Parent References

| Key | Type | Description |
|-----|------|-------------|
| {Q}parentGoalId{Q} | string | 8-char hex ID of the parent goal. Enables direct goal lookup without traversing the full milestone path. |
| {Q}parentMilestoneId{Q} | string | 8-char hex ID of the parent milestone. The primary upward reference — completing this task moves the parent milestone toward completion. |
| {Q}workstream{Q} | string | Parent workstream name. Stored directly on the task for efficient querying without parent traversal. |

### Valuation & Scoring

| Key | Type | Description |
|-----|------|-------------|
| {Q}targetValuation{Q} | integer | Dollar value (USD) this task contributes when completed. Inherited from parent milestone's targetValuation, distributed across tasks by importance and effort. |
| {Q}targetValuation_reasoning{Q} | string (50+ words) | How the task's valuation was derived from the parent milestone. Must show the calculation chain: milestone value x task share = task value, with justification. |
| {Q}currentValuation{Q} | integer | Current valuation in USD. For binary tasks: 0 (not done) or targetValuation (done). |
| {Q}valuationImpact{Q} | integer | Enterprise value impact in USD (Track 1). |
| {Q}valuationImpactReasoning{Q} | string | Explanation of enterprise value contribution for this specific task. |
| {Q}socialValuationImpact{Q} | integer | Societal value impact in USD (Track 2). The societal benefit enabled by completing this task. |
| {Q}socialValuationImpactReasoning{Q} | string | Explanation of societal impact in dollar terms. |
| {Q}performanceScore{Q} | integer | 0-100. Task-level performance score based on output quality and target achievement. |
| {Q}executionScore{Q} | integer | 0-100. Formula: 40% time adherence + 30% defect rate + 30% collaboration quality. Measures how well the task was executed. |
| {Q}roi{Q} | integer | ROI as a multiple for this task. targetValuation / estimated_cost. |
| {Q}roi_reasoning{Q} | string (50+ words) | Financial justification for the task's ROI with specific numbers and assumptions. |
| {Q}roiPercentage{Q} | number | ROI as percentage. |

### Ranking

| Key | Type | Description |
|-----|------|-------------|
| {Q}ranking{Q} | integer | 1-10 ranking within the parent milestone. 1 = most critical task. Based on dependency position and value creation sequence. |
| {Q}ranking_justification{Q} | string | Why this task ranks where it does. References what it unblocks, its value contribution, and execution priority. |
| {Q}overall_ranking{Q} | string | Global ranking label across the venture. |
| {Q}priority{Q} | string | Priority override: "high", "medium", "low". Human override of computed priority. |

### Workflow & Execution

| Key | Type | Description |
|-----|------|-------------|
| {Q}workflow{Q} | array of objects | Execution workflow steps for this task. See **Workflow Step Object** below. Defines the step-by-step process for completing the task, including human and AI agent steps. |

#### Workflow Step Object (inside {Q}workflow{Q} array)

| Key | Type | Description |
|-----|------|-------------|
| {Q}step{Q} | integer | Step number in sequence (1, 2, 3...). Execution order within the task. |
| {Q}action{Q} | string | What needs to be done in this step. Specific and actionable description of the work. |
| {Q}actor{Q} | string | Who performs this step: "human", "ai_agent", or a specific agent name. Determines routing in ClawOS orchestration. |
| {Q}approval_required{Q} | boolean | Whether human approval is needed before the next step. true for deployments, external sends, financial actions. |
| {Q}owner{Q} | object | Step owner: {{personId: string, name: string, role: string}}. May differ from the task owner for specialized sub-steps. |
| {Q}tools_required{Q} | array of strings | Tools needed (e.g., ["GitHub", "Vercel", "Figma"]). Pre-execution resource check. |
| {Q}agent_output_deliverable{Q} | string | Expected output from this step. Prefixed with checkmark when complete. |
| {Q}feedback{Q} | string | Guidance for the executor: expectations, quality criteria, and common mistakes to avoid. |
| {Q}ai_agent_name{Q} | string | Specific AI agent for this step if actor is "ai_agent". Maps to agent_org_chart_v2. |

### Deliverables & Output

| Key | Type | Description |
|-----|------|-------------|
| {Q}deliverable{Q} | string | Primary deliverable description. What artifact this task produces. |
| {Q}deliverables{Q} | array | Multiple deliverable items. Can be strings or structured objects with evidence fields showing WHO, WHAT, HOW, RESPONSE, and OUTCOME. |
| {Q}result{Q} | string | Result description after task completion. Documents what was actually delivered vs what was planned. |
| {Q}ref{Q} | string | Reference link to the deliverable (URL, document ID, or file path). Provides verifiable evidence of completion. |
| {Q}github_ticket{Q} | string | GitHub issue or PR reference (e.g., "org/repo#123"). Links the task to code changes for engineering tasks. |

### Dependencies

| Key | Type | Description |
|-----|------|-------------|
| {Q}dependencies{Q} | array | Prerequisite tasks or milestones that must complete first. Can be ID strings or structured objects with full context. |

### Quality & Feedback

| Key | Type | Description |
|-----|------|-------------|
| {Q}syntax_warning{Q} | object | Automated QA warnings about naming and ordering. See **Syntax Warning Object** below. |
| {Q}feedback_summary{Q} | string | Consolidated evaluation from reviewers or QA agents. Summarizes quality issues, suggested improvements, and compliance status. |
| {Q}feedback{Q} | string or array | Individual feedback entries. String for simple feedback, array for structured feedback trail. |

#### Syntax Warning Object (inside {Q}syntax_warning{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}suggestion{Q} | string | Human-readable suggestion text explaining the detected issue. |
| {Q}nameChange{Q} | boolean | true if the task name should be revised to follow "Active verb + specific deliverable" convention. |
| {Q}new_suggestion{Q} | string | Suggested replacement name if nameChange is true. Ready to apply. |
| {Q}reorder_change{Q} | boolean | true if this task should be reordered within the milestone. |
| {Q}reorder_reasoning{Q} | string | Why reordering is recommended, referencing dependency sequence or priority logic. |

### AI & Automation

| Key | Type | Description |
|-----|------|-------------|
| {Q}aiTools{Q} | array | AI tools used. Each item: {{name: string, type: "automation"/"analysis"/"documentation"/"generation"}}. |
| {Q}added_agent{Q} | string | AI agent that created or last modified this task. |
| {Q}executed_by{Q} | string | Agent or person who actually executed this task. May differ from owner if delegated. |

### Source & Type

| Key | Type | Description |
|-----|------|-------------|
| {Q}type{Q} | string | "suggested" (AI-proposed, pending review) or "existing" (confirmed, active). |
| {Q}source{Q} | string | Origin: "planning-intelligence", "human", "clawos-sync", "meeting-transcript", etc. |
| {Q}source_description{Q} | string | Additional source context with creation details. |
| {Q}remapped_from{Q} | string | Original location if this task was moved from another milestone or goal. Tracks reorganization history. |

### Metadata & Sync

| Key | Type | Description |
|-----|------|-------------|
| {Q}created_at{Q} | string | ISO 8601 creation timestamp. |
| {Q}updated_at{Q} | string | ISO 8601 last modification timestamp. Auto-updated on any field change. |
| {Q}completed_at{Q} | string | ISO 8601 completion timestamp. null if pending or in_progress. |
| {Q}completedAt{Q} | string | Alternate completion timestamp field. Same format. |
| {Q}executed_at{Q} | string | ISO 8601 timestamp of last execution activity. Tracks recency of work. |
| {Q}started_at{Q} | string | ISO 8601 timestamp of when work actually began. |
| {Q}activity{Q} | array | Activity log entries tracking status changes, agent interactions, and human updates. Each entry: {{timestamp, actor, action, details}}. |
| {Q}notes{Q} | string | Free-form notes for additional context. |
| {Q}thinking{Q} | string | AI reasoning trace. Chain-of-thought from agent analysis or execution. Preserved for auditability. |
| {Q}_meta{Q} | object | Internal system metadata (pipeline version, processing flags). Not for human consumption. |
| {Q}clawos{Q} | object or boolean | ClawOS sync metadata or boolean processing flag. |
| {Q}shareos_sync{Q} | object | ShareOS platform sync status with dashboard publication timestamps. |

**See also:** [[goal-schema]], [[milestone-schema]], [[owner-schema]], [[valuation-model]]"""


# ============================================================
# Update pages
# ============================================================
for i, p in enumerate(pages):
    if p['id'] == 'goal-schema':
        pages[i]['content'] = GOAL_SCHEMA
        pages[i]['title'] = 'Goal Schema (Complete Reference)'
        print(f"Updated goal-schema: {len(GOAL_SCHEMA)} chars")
    elif p['id'] == 'milestone-schema':
        pages[i]['content'] = MILESTONE_SCHEMA
        pages[i]['title'] = 'Milestone Schema (Complete Reference)'
        print(f"Updated milestone-schema: {len(MILESTONE_SCHEMA)} chars")
    elif p['id'] == 'task-schema':
        pages[i]['content'] = TASK_SCHEMA
        pages[i]['title'] = 'Task Schema (Complete Reference)'
        print(f"Updated task-schema: {len(TASK_SCHEMA)} chars")

# Write back
pages_json = json.dumps(pages, ensure_ascii=False)
new_line = f'const PAGES = {pages_json};'

# Find and replace the PAGES line
lines = html.split('\n')
for i, line in enumerate(lines):
    if line.strip().startswith('const PAGES'):
        lines[i] = new_line
        break

# Update version
import time
version_tag = f'<!-- v{int(time.time()*1000)} -->'
new_html = '\n'.join(lines)
new_html = re.sub(r'<!-- v\d+ -->', version_tag, new_html)

open('index.html', 'w').write(new_html)
print(f"\nTotal HTML size: {len(new_html)} chars")
print("Done!")
PYSCRIPT