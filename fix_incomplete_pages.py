#!/usr/bin/env python3
"""Fix all incomplete/inconsistent wiki pages with full end-to-end documentation."""

import json, re, time

html = open('index.html').read()
for line in html.split('\n'):
    if line.strip().startswith('const PAGES'):
        data = line.strip()[len('const PAGES = '):]
        if data.endswith(';'):
            data = data[:-1]
        pages = json.loads(data)
        break

Q = '\u2018'  # Unicode left single quote used as code fence in wiki
QQ = Q * 3

updates = {}

# ============================================================
# 1. OWNER SCHEMA - Expanded
# ============================================================
updates['owner-schema'] = {
    'title': 'Owner Object Schema',
    'content': f"""The {Q}owner{Q} object is a shared structure that appears at every level of the ShareOS hierarchy: workstream, goal, milestone, task, and workflow step. It identifies the person responsible for that unit of work.

## Fields

| Key | Type | Description |
|-----|------|-------------|
| {Q}personId{Q} | string | UUID unique identifier for the person (e.g., "2b7496c1-xxxx-xxxx-xxxx-xxxxxxxxxxxx"). Links to the team directory for contact info, role details, and cross-entity workload tracking. Used for assignment audits and deduplication. |
| {Q}name{Q} | string | Full name of the person (e.g., "Yuvaraj Tankala", "Andreas Dierks", "Kenny Brown"). Displayed in dashboards, task cards, reports, and notification routing. Must be the person's real name, not an alias or role title. |
| {Q}role{Q} | string | Role title or workstream assignment (e.g., "AI Engineering Lead", "Head of Operations", "CEO", "Product", "Demand"). Used for role-based filtering, capability matching, workload balancing, and validating that assignments match the person's domain expertise. |

## Where It Appears

| Level | Field Path | Purpose |
|-------|-----------|---------|
| Workstream | {Q}os_share.workstreams[].owner{Q} | Workstream lead responsible for all goals within |
| Goal | {Q}os_share.workstreams[].goals[].owner{Q} | Person accountable for achieving the KPI target |
| Milestone | {Q}...goals[].milestones[].owner{Q} | Person responsible for completing the checkpoint |
| Task | {Q}...milestones[].tasks[].owner{Q} | Person executing the atomic work unit |
| Workflow Step | {Q}...tasks[].workflow[].owner{Q} | Person performing a specific step in the execution sequence |

## Rules

1. **Every goal, milestone, and task MUST have an owner.** No orphaned work items.
2. **Owners are assigned based on team roles and expertise.** Planning Intelligence validates that assignments match the person's domain (e.g., engineering tasks go to engineering leads).
3. **The owner is accountable, not necessarily the executor.** The owner ensures completion but may delegate sub-steps via workflow steps with different owners.
4. **Owner assignment audits** are stored in {Q}os_share.owner_assignment_audit{Q} with fields: goals_assigned, milestones_assigned, tasks_assigned, total_assigned, skipped_locked, already_assigned, team_size, updated_at.
5. **Locked items** ({Q}locked_by{Q} is not null) are skipped during automatic reassignment to prevent overriding human decisions.

## Example

{QQ}json
{{
  "personId": "2b7496c1-4d1e-45fd-861d-0debc35b4f31",
  "name": "Andreas Dierks",
  "role": "Head of Operations"
}}
{QQ}

## Current Team

| Name | Role | Typical Workstreams |
|------|------|-------------------|
| Hamet Watt | CEO, Share Ventures | Investors, Partnerships, Strategy |
| Yuvaraj Tankala | AI Engineering Lead | Product, Operations |
| Dean Carter | CEO, instill | Product (instill) |
| Andreas Dierks | Head of Operations | Operations |
| Kenny Brown | Demand | Demand, Partnerships |

## Assignment Validation

Planning Intelligence checks:
- Does the person have expertise in the task's domain?
- Is the person's workload balanced (not overloaded with 50+ open tasks)?
- Does the role match the workstream? (e.g., "Demand" role should own Demand workstream goals)
- Are locked assignments preserved?

**See also:** [[goal-schema]], [[milestone-schema]], [[task-schema]], [[team-overview]]"""
}


# ============================================================
# 2. VENTURE DOCUMENT SCHEMA - Expanded
# ============================================================
updates['venture-doc-schema'] = {
    'title': 'Venture Document Schema',
    'content': f"""Each venture is a document in {Q}shareos.deals_internal{Q}. This is the complete field reference covering all 208+ top-level fields and their nested structures.

## Location

| | |
|-|-|
| **Database** | shareos |
| **Collection** | deals_internal |
| **Documents** | 56+ |
| **Fields per document** | 208+ |

## Field Groups

### Identity & Basics

| Key | Type | Description |
|-----|------|-------------|
| {Q}_id{Q} | ObjectId | MongoDB unique document identifier. Auto-generated. |
| {Q}company_name{Q} | string | Official company name (e.g., "feno", "instill", "shareland"). Lowercase, used as primary key across all systems. |
| {Q}display_name{Q} | string | Human-friendly display name with proper capitalization (e.g., "Feno", "instill", "Shareland"). |
| {Q}cmny_id{Q} | string | Company ID used by external integrations and APIs. |
| {Q}description{Q} | string | Full company description explaining the venture's purpose, product, and market. |
| {Q}alt_description{Q} | string | Alternate description (shorter or for different audiences). |
| {Q}tagline{Q} | string | Short tagline or slogan. |
| {Q}blurb{Q} | string | Brief pitch blurb (1-3 sentences). |
| {Q}blurb_version_history{Q} | array | Historical versions of the blurb with timestamps. |
| {Q}info{Q} | string | Additional info field. |
| {Q}website{Q} | string | Primary website URL. |
| {Q}company_url{Q} | string | Alternate URL field. |
| {Q}company_logo{Q} | string | URL to company logo image. |
| {Q}company_location{Q} | string | Geographic location (e.g., "Los Angeles, CA"). |
| {Q}company_size{Q} | string | Team size description. |
| {Q}founded{Q} | string | Year or date founded. |
| {Q}vertical{Q} | string | Primary performance vertical (Physical, Cognitive, Emotional, Social, Biological, Organizational, Financial). |
| {Q}venture_type{Q} | string | "foundry" (built by Share Labs) or "fund" (external investment). |
| {Q}entity_type{Q} | string | Entity classification. |
| {Q}display{Q} | string | Display mode setting. |
| {Q}date_id{Q} | string | Date-based identifier. |
| {Q}id{Q} | string | Internal string ID. |

### Stage & Status

| Key | Type | Description |
|-----|------|-------------|
| {Q}current_stage{Q} | string | Current lifecycle stage: Explore, Generate, Validate, Pilot, Launch, Scale, or Exit. Determines which KPIs, agent groups, and evaluation criteria apply. |
| {Q}stage{Q} | string | Alternate stage field. |

### Valuation & Finance

| Key | Type | Description |
|-----|------|-------------|
| {Q}currentValuation{Q} | integer | Current enterprise valuation in USD. Calculated from workstream performance and market comparables. |
| {Q}current_valuation{Q} | integer | Alternate current valuation field. |
| {Q}current_valuation_reasoning{Q} | string | Detailed reasoning for current valuation. |
| {Q}targetValuation{Q} | integer | Target valuation to achieve. |
| {Q}benchmark_valuation{Q} | integer | Benchmark valuation from comparable companies. |
| {Q}computed_valuation_breakdown{Q} | object | Detailed valuation breakdown with per-workstream allocations. Contains: valuation methodology, workstream contributions, market multiple applied, comparable companies referenced. |
| {Q}ROI{Q} | string | Overall ROI for the venture. |
| {Q}ROI_reasoning{Q} | string | Justification for the ROI figure. |
| {Q}total_spent{Q} | integer | Total USD spent to date across all workstreams. |
| {Q}cost_to_date{Q} | integer | Total cost to date. |
| {Q}burn{Q} | string | Monthly burn rate. |
| {Q}raised_amount{Q} | string | Total funding raised. |
| {Q}current_arr{Q} | string | Current annual recurring revenue. |
| {Q}invested{Q} | string | Amount invested by Share Ventures. |
| {Q}investment_date{Q} | string | Date of investment. |
| {Q}investmentRequiredRelativeToValuationPotential{Q} | float | Investment efficiency ratio. |
| {Q}finance_data{Q} | object | Financial data container. |

### Scores & Assessment

| Key | Type | Description |
|-----|------|-------------|
| {Q}executionScore{Q} | integer | 0-100 execution score across all workstreams. 50% milestone completion + 25% budget + 25% schedule. |
| {Q}execution_score{Q} | integer | Alternate execution score field. |
| {Q}performanceScore{Q} | integer | 0-100 performance score. Aggregate of goal KPI achievement weighted by valuation. |
| {Q}performance_score{Q} | integer | Alternate performance score. |
| {Q}health_score{Q} | integer | Overall venture health score. |
| {Q}company_score_breakdown{Q} | object | Detailed score breakdown per dimension. |
| {Q}product_assessment{Q} | string | Product workstream assessment narrative. |
| {Q}team_assessment{Q} | string | Team workstream assessment. |
| {Q}partnerships_assessment{Q} | string | Partnerships assessment. |
| {Q}investors_assessment{Q} | string | Investors assessment. |
| {Q}overall_assessment{Q} | string | Holistic venture assessment. |
| {Q}final_recommendations{Q} | object | Final recommendations with reasoning. |
| {Q}ai_insights{Q} | string | AI-generated insights about the venture. |

### Workstream Updates (per workstream)

| Key | Type | Description |
|-----|------|-------------|
| {Q}product_updates{Q} | array/object | Recent product workstream updates with timestamps and content. |
| {Q}demand_updates{Q} | array/object | Recent demand workstream updates. |
| {Q}demand{Q} | object | Demand metrics and data. |
| {Q}operations_updates{Q} | array/object | Recent operations updates. |
| {Q}partnerships_updates{Q} | array/object | Recent partnerships updates. |
| {Q}synergy_updates{Q} | array/object | Recent synergy updates. |
| {Q}investor_updates{Q} | array/object | Recent investor updates. |
| {Q}team_updates{Q} | array/object | Recent team updates. |

### People & Team

| Key | Type | Description |
|-----|------|-------------|
| {Q}founders{Q} | array of objects | Founder information. Each: {{name, role, bio, linkedin, image}}. |
| {Q}founder_data{Q} | array of objects | Extended founder data from research. |
| {Q}founder_shareos_ids{Q} | array | ShareOS IDs for founders. |
| {Q}employees{Q} | array of objects | Employee directory with roles and details. |
| {Q}average_salaries{Q} | array | Salary benchmarks for the team. |
| {Q}diversity{Q} | array | Diversity metrics. |

### Metrics & Analytics

| Key | Type | Description |
|-----|------|-------------|
| {Q}company_metrics{Q} | object | Key company metrics (9 keys). Revenue, users, growth rate, engagement, etc. |
| {Q}additional_metrics{Q} | object | Extended metrics (8 keys). Supplementary KPIs beyond core metrics. |
| {Q}community_metrics{Q} | object | Community engagement metrics (19 keys). Social media followers, engagement rates, content performance. |
| {Q}followers{Q} | string | Social media follower count. |
| {Q}company_highlights{Q} | array of strings | Key highlights and achievements. |
| {Q}icons{Q} | object | UI icon configuration (8 keys). |

### Goals & Milestones (Legacy)

| Key | Type | Description |
|-----|------|-------------|
| {Q}goals_milestones{Q} | object | Legacy goals/milestones summary (7 keys). Pre-os_share structure, kept for backward compatibility. |
| {Q}goal_table_id{Q} | string | External goal table reference. |
| {Q}expected_deadline{Q} | string | Overall venture deadline. |

### Competitive & Market

| Key | Type | Description |
|-----|------|-------------|
| {Q}competitive_analysis{Q} | array of objects | Competitive analysis entries with competitor details. |
| {Q}domain{Q} | object | Domain classification (10 keys). Vertical, subdomain, market info. |
| {Q}impact{Q} | string | Narrative description of societal impact (NOT a monetary metric). |
| {Q}impact_version_history{Q} | array | Historical versions of impact narrative. |
| {Q}customer_base{Q} | string | Target customer base description. |

### Funding & Investment

| Key | Type | Description |
|-----|------|-------------|
| {Q}funding_info{Q} | object | Funding details (10 keys). Rounds, amounts, investors, terms. |

### External Data

| Key | Type | Description |
|-----|------|-------------|
| {Q}email_ids_msgs{Q} | array of strings | Email thread IDs associated with this venture. |
| {Q}fireflies_meeting_titles{Q} | array of strings | Meeting titles from Fireflies transcripts. |
| {Q}deck_data{Q} | string | Pitch deck data/reference. |

### ClawOS Integration

| Key | Type | Description |
|-----|------|-------------|
| {Q}clawos{Q} | object/boolean | ClawOS sync metadata. |
| {Q}clawos_updates{Q} | object | Updates synced from WhatsApp via ClawOS daily sync (7 keys). Per-workstream update arrays. |
| {Q}clawos_updates_synced_at{Q} | string | Last sync timestamp. |
| {Q}clawos_updates_audited_at{Q} | string | Last audit timestamp. |
| {Q}clawos_updates_cleaned_at{Q} | string | Last cleanup timestamp. |

### Agent & Automation

| Key | Type | Description |
|-----|------|-------------|
| {Q}agent_hours_saved{Q} | integer | Estimated human hours saved by AI agent automation. |

## The {Q}os_share{Q} Object (Core ShareOS Hierarchy)

The {Q}os_share{Q} object is the heart of every venture document. It contains the full goal/milestone/task hierarchy, valuation data, and all Planning Intelligence outputs.

### Top-Level {Q}os_share{Q} Fields

| Key | Type | Description |
|-----|------|-------------|
| {Q}workstreams{Q} | array of objects | The 7 workstream objects, each containing goals, milestones, and tasks. See [[goal-schema]], [[milestone-schema]], [[task-schema]] for nested structure. |
| {Q}workstream_rankings{Q} | array | Ranked list of workstreams by performance and valuation contribution. |
| {Q}targetValuation{Q} | integer | Company-level target valuation in USD. This is the top of the valuation cascade: company -> workstreams -> goals -> milestones -> tasks. |
| {Q}currentValuation{Q} | integer | Company-level current valuation based on aggregate goal performance. |
| {Q}stage{Q} | string | Current lifecycle stage. Determines applicable KPIs and evaluation criteria. |

### Planning Intelligence Outputs (inside {Q}os_share{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}ground_truth{Q} | object | Ground truth verification from Step 1 of Planning Intelligence. Contains: confidence_score (0-100), confidence_rubric, verified_metrics (confirmed data points), flagged_metrics (uncertain or contradictory), contradictions (conflicts found between sources), real_metrics (from Shopify/Looker/meetings), truth_document (consolidated narrative), key_decisions, stated_priorities. |
| {Q}business_blueprint{Q} | object | CEO-level business blueprint from Step 2. Contains: business_model, business_type, customer (ICP definition), building_blocks (key capabilities needed), sequence (build order), team_input_assessment, key_insight, updated_at. |
| {Q}coherence_audit{Q} | object | Goal coherence check from Step 3. Contains: coherence_score (0-100), understanding (system's interpretation of goals), reasoning (why changes were made), removed (goals removed as duplicates/irrelevant), created (new goals added), fixed (goals modified), fixes_applied (count), fix_details (per-fix explanation), updated_at. |
| {Q}gap_analysis{Q} | object | Missing goal identification from Step 4. Contains: gaps (identified missing areas), suggested_goals (new goals proposed), goals_created (count of goals added), note, updated_at. |
| {Q}weight_recalculation{Q} | object | Workstream weight adjustment from Step 11. Contains: old_weights (previous weights), new_weights (recalculated), methodology (how weights were derived), per_workstream (detailed per-workstream breakdown), significant_shifts (weights that changed >5%), updated_at. |
| {Q}valuation_agent_analysis{Q} | object | Valuation sanity check. Contains: comparables (comparable companies used), failed_companies (cautionary comparisons), valuation_range (min/max/likely), sanity_flags (warnings about unrealistic valuations), updated_at. |
| {Q}pipeline_health{Q} | object | Agent pipeline health check. Contains: overall_score, breakdown (per-agent health), agent_summary, stale_agents (not run recently), never_run_agents, premature_deactivated, qa_agents, issues, updated_at. |
| {Q}owner_assignment_audit{Q} | object | Owner assignment results. Contains: goals_assigned (count), milestones_assigned, tasks_assigned, total_assigned, skipped_locked (preserved human overrides), already_assigned (unchanged), team_size, updated_at. |

**See also:** [[goal-schema]], [[milestone-schema]], [[task-schema]], [[valuation-model]], [[planning-intelligence]]"""
}


# ============================================================
# 3. VENTURE SIMULATION SCHEMA - Full expansion
# ============================================================
updates['venture-simulation-schema'] = {
    'title': 'Venture Simulation Schema',
    'content': f"""Venture simulations project a venture's trajectory across all 7 lifecycle stages. Each simulation is an end-to-end model of how a venture progresses from signal detection through exit, including agent costs, human touchpoints, valuations, and deliverables at each stage.

## Location

| | |
|-|-|
| **Database** | shareos |
| **Collection** | venture_simulations |
| **Documents** | 37+ |

## Top-Level Fields

| Key | Type | Description |
|-----|------|-------------|
| {Q}cmny_id{Q} | string | Company identifier matching deals_internal (e.g., "share_insights", "feno"). Primary key for cross-referencing. |
| {Q}name{Q} | string | Human-readable venture name (e.g., "Share Insights", "Feno"). |
| {Q}vertical{Q} | string | Performance vertical: Physical, Cognitive, Emotional, Social, Biological, Organizational, or Financial. |
| {Q}generated_at{Q} | string | ISO 8601 timestamp of when this simulation was generated or last updated. |
| {Q}simulation_metadata{Q} | object | Simulation configuration and context. See **Simulation Metadata** below. |
| {Q}executive_summary{Q} | object | High-level summary of simulation results. See **Executive Summary** below. |
| {Q}signal_origin{Q} | object | How the venture opportunity was first detected. See **Signal Origin** below. |
| {Q}founding_team{Q} | array of objects | Team members involved. See **Team Member** below. |
| {Q}products{Q} | array of objects | Products/offerings being built. See **Product** below. |
| {Q}stages{Q} | array of objects | Per-stage simulation data (the core of the simulation). See **Stage** below. |
| {Q}analysis{Q} | object | Cross-stage analysis and comparisons. See **Analysis** below. |

## Simulation Metadata Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}venture_name{Q} | string | Full venture name. |
| {Q}version{Q} | string | Simulation version (e.g., "V1", "V2"). Tracks iterations as the venture evolves. |
| {Q}generated_date{Q} | string | Date the simulation was generated (YYYY-MM-DD format). |
| {Q}vertical{Q} | string | Performance vertical this venture targets. |
| {Q}subdomain{Q} | string | Specific subdomain within the vertical (e.g., "AI-Powered Market Research" under Cognitive). |
| {Q}tam{Q} | integer | Total Addressable Market in USD (e.g., 15000000000 for $15B). |
| {Q}tam_formatted{Q} | string | Human-readable TAM (e.g., "$15B"). |
| {Q}simulation_purpose{Q} | string | Purpose statement (e.g., "ShareOS Autonomous Venture Creation Simulation"). |

## Executive Summary Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}current_valuation{Q} | float | Current simulated valuation in USD. |
| {Q}target_valuation{Q} | float | Target valuation for the current stage. |
| {Q}total_agent_cost{Q} | integer | Total AI agent compute cost in USD across all stages. |
| {Q}agent_cost_pct{Q} | string | Agent cost as percentage of valuation (e.g., "0.02%"). Demonstrates capital efficiency. |
| {Q}avg_agent_work_share{Q} | string | Average percentage of work done by AI agents vs humans (e.g., "88%"). |
| {Q}timeline{Q} | string | Current status and stage (e.g., "Active — Generate Stage"). |
| {Q}total_goals{Q} | integer | Total number of goals across all stages. |
| {Q}goals_achieved{Q} | integer or null | Number of goals completed. null if in progress. |
| {Q}key_takeaways{Q} | array of strings | Top 3-5 strategic insights from the simulation. |

## Signal Origin Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}signal_strength_score{Q} | float | 0.0-1.0 score indicating how strong the opportunity signal is. Threshold for action is typically 0.75. |
| {Q}threshold{Q} | float | Minimum signal strength to trigger venture creation (default 0.75). |
| {Q}action_triggered{Q} | string | What action was taken when signal exceeded threshold (e.g., "Venture Agent spawned, Stage 1 EXPLORE begins"). |
| {Q}vertical{Q} | string | Which vertical the signal maps to. |
| {Q}subdomain{Q} | string | Specific subdomain identified. |
| {Q}tam{Q} | string | TAM estimate for the opportunity. |
| {Q}signals{Q} | array of objects | Individual signals that contributed to the score. Each: {{signal: string, strength: string}}. |
| {Q}domain_context{Q} | string | Context about what's known at the Explore stage. |
| {Q}core_scientific_thesis{Q} | string | The core thesis underlying the venture's technology approach. |

### Signal Object (inside {Q}signals{Q} array)

| Key | Type | Description |
|-----|------|-------------|
| {Q}signal{Q} | string | Description of the signal detected (e.g., '"AI market research" search volume'). |
| {Q}strength{Q} | string | Signal strength measurement (e.g., "+340% / 24mo" for search trend growth). |

## Team Member Object (inside {Q}founding_team{Q} array)

| Key | Type | Description |
|-----|------|-------------|
| {Q}name{Q} | string | Team member's full name. |
| {Q}role{Q} | string | Role in the venture (e.g., "CEO & Founder", "CTO"). |
| {Q}hourly_rate{Q} | integer | Hourly cost rate in USD for cost modeling. |
| {Q}description{Q} | string | Description of their contribution and expertise. |
| {Q}expertise_tags{Q} | array of strings | Skills and domain tags (e.g., ["strategy", "investor-relations", "network-capital"]). |

## Product Object (inside {Q}products{Q} array)

| Key | Type | Description |
|-----|------|-------------|
| {Q}name{Q} | string | Product name (e.g., "Digital Twin Research Platform"). |
| {Q}category{Q} | string | Product category (e.g., "Enterprise SaaS — Market Research"). |
| {Q}outcome{Q} | string | What the product achieves for customers. |
| {Q}mechanism{Q} | string | How the product works technically. |
| {Q}key_differentiator{Q} | string | What makes this product unique vs competitors. |
| {Q}evidence_score{Q} | string | Evidence supporting the product's effectiveness. |
| {Q}pricing{Q} | string | Pricing model and ranges. |

## Stage Object (inside {Q}stages{Q} array)

Each stage object represents one lifecycle stage with full simulation data.

| Key | Type | Description |
|-----|------|-------------|
| {Q}stage_number{Q} | integer | Stage sequence number (1=Explore through 7=Exit). |
| {Q}stage_name{Q} | string | Stage name: Explore, Generate, Validate, Pilot, Launch, Scale, or Exit. |
| {Q}headline{Q} | string | One-line description of this stage's focus. |
| {Q}description{Q} | string | Detailed description of what happens in this stage and its goals. |
| {Q}duration{Q} | string | Estimated duration (e.g., "6 days", "4 weeks"). |
| {Q}target_valuation{Q} | integer | Target valuation at the end of this stage in USD. |
| {Q}goals_count{Q} | string | Number of active goals (e.g., "7 workstreams active"). |
| {Q}agent_cost{Q} | integer | Total AI agent cost for this stage in USD. |
| {Q}human_time{Q} | string | Total human time required (e.g., "5 min", "2 hours"). |
| {Q}human_cost{Q} | integer | Human labor cost for this stage in USD. |
| {Q}total_cost{Q} | integer | Total cost (agent + human) in USD. |
| {Q}agent_work_pct{Q} | float | Percentage of work done by AI agents (e.g., 97.8). |
| {Q}human_work_pct{Q} | float | Percentage of work done by humans. |
| {Q}workstream_weights{Q} | array of objects | Per-workstream valuation weights. See **Workstream Weight** below. |
| {Q}workstreams{Q} | array of objects | Detailed per-workstream simulation. See **Workstream Simulation** below. |
| {Q}agent_iterations{Q} | array of objects | Agent error/recovery cycles. See **Agent Iteration** below. |
| {Q}human_touchpoints{Q} | array of objects | Points where human intervention occurred. See **Human Touchpoint** below. |
| {Q}stage_scorecard{Q} | array of objects | Stage gate evaluation criteria. See **Scorecard Entry** below. |
| {Q}stage_summary{Q} | object | Summary metrics for the stage. See **Stage Summary** below. |
| {Q}simulated_deliverables{Q} | array of strings | List of deliverables produced in this stage. |

### Workstream Weight (inside {Q}workstream_weights{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}workstream{Q} | string | Workstream identifier (e.g., "1. Product (Technical)"). |
| {Q}weight_pct{Q} | integer | Weight as percentage (all 7 sum to 100). |
| {Q}valuation_allocation{Q} | integer | Dollar amount allocated to this workstream (target_valuation x weight). |

### Workstream Simulation (inside {Q}workstreams{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}workstream_name{Q} | string | Workstream name (e.g., "WS 1 — Product"). |
| {Q}headline{Q} | string | Focus area for this workstream in this stage. |
| {Q}key_metric_label{Q} | string | North star metric name (e.g., "Technical Readiness Score"). |
| {Q}key_metric_value{Q} | string | Current value of the metric. |
| {Q}key_metric_target{Q} | string | Target value (e.g., ">0.80"). |
| {Q}valuation{Q} | integer | Valuation contribution of this workstream in USD. |
| {Q}goals{Q} | array of objects | Goals within this workstream for this stage. See **Simulation Goal** below. |

### Simulation Goal (inside workstream {Q}goals{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}id{Q} | string | Goal identifier (e.g., "P-E1" for Product-Explore-Goal1). |
| {Q}name{Q} | string | Goal KPI name. |
| {Q}status{Q} | string | Status: "IN-PROGRESS", "COMPLETE", "NOT-STARTED". |
| {Q}result{Q} | string | Current result or outcome description. |
| {Q}target{Q} | string | Target metric value. |
| {Q}target_valuation{Q} | integer | Dollar value if achieved. |
| {Q}contribution{Q} | integer | Current contribution in USD based on progress. |
| {Q}performance_score{Q} | integer | 0-100 performance score. |
| {Q}weight_in_stage{Q} | string | Weight within the stage's workstream (e.g., "30%"). |

### Agent Iteration (inside {Q}agent_iterations{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}iteration_number{Q} | integer | Sequence number of the error/fix cycle. |
| {Q}agent_name{Q} | string | Name of the agent that encountered the issue. |
| {Q}agent_role{Q} | string | Role description (e.g., "TAM Sizing Agent"). |
| {Q}failure_description{Q} | string | What went wrong (e.g., "Initial TAM returned $220B — correct data, wrong scope"). |
| {Q}fix_description{Q} | string | How the agent corrected the error. |
| {Q}before_state{Q} | string | State before the fix. |
| {Q}after_state{Q} | string | State after the fix. |
| {Q}human_required{Q} | boolean or null | Whether human intervention was needed. null = agent self-corrected. |
| {Q}valuation_at_risk{Q} | string | Dollar value that was at risk due to the error. |
| {Q}value_recovered{Q} | string | Dollar value recovered by the fix. |

### Human Touchpoint (inside {Q}human_touchpoints{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}touchpoint_number{Q} | integer | Sequence number. |
| {Q}person{Q} | string | Name of the human (e.g., "Hamet Watt"). |
| {Q}time_spent{Q} | string | Time the human spent (e.g., "5 min"). |
| {Q}cost{Q} | integer | Cost of this human touchpoint in USD. |
| {Q}description{Q} | string | What the human did. |
| {Q}decision_made{Q} | string | The decision and its rationale. |
| {Q}agent_preparation{Q} | string | What the agents prepared for the human to review. |

### Scorecard Entry (inside {Q}stage_scorecard{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}criterion{Q} | string | Evaluation criterion name (e.g., "LLM Simulation Viability"). |
| {Q}result{Q} | string | Achieved result (e.g., "4.1/5.0 Evidence Score"). |
| {Q}target{Q} | string | Required target to pass (e.g., ">4.0"). |
| {Q}status{Q} | string | "PASS" or "FAIL". |
| {Q}valuation_impact{Q} | string | Dollar value impact of this criterion (e.g., "$360.0K / $360.0K"). |

### Stage Summary (inside {Q}stage_summary{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}performance_score{Q} | integer | 0-100 overall performance score for the stage. |
| {Q}execution_score{Q} | integer | 0-100 execution score for the stage. |
| {Q}agent_iwa{Q} | string | Intelligent Work Automation percentage (e.g., "97.8%"). How much work was done by agents. |
| {Q}agent_cost{Q} | integer | Total agent cost for the stage in USD. |
| {Q}human_cost{Q} | integer | Total human cost for the stage in USD. |

## Analysis Object

Cross-stage analysis providing the big-picture view.

| Key | Type | Description |
|-----|------|-------------|
| {Q}human_pct_trajectory{Q} | array of objects | How human vs agent work split changes across stages. Each: {{stage, human_pct, agent_pct, human_cost, agent_cost}}. Human % should plateau/recover at Scale as team grows alongside agent coverage. |
| {Q}agent_value_creation{Q} | array of objects | Value created by different agent capabilities. Each: {{value_driver: string, amount: string}}. |
| {Q}shareos_vs_traditional{Q} | object | Side-by-side comparison. Contains: {Q}traditional{Q} (description of traditional approach) and {Q}shareos{Q} (description of ShareOS approach). |
| {Q}proofs{Q} | array of objects | Evidence that the simulation model works. Each: {{proof_number, title, description}}. |
| {Q}master_stage_summary{Q} | array of objects | Summary table across all stages. Each: {{stage, duration, goals, agent_cost, human_time, human_cost, total_cost, iwa}}. |

**See also:** [[stages]], [[valuation-model]], [[venture-doc-schema]], [[acc-engine]]"""
}


# ============================================================
# 4. POLSIA SCHEMA - Expanded with field descriptions
# ============================================================
updates['polsia-schema'] = {
    'title': 'Polsia Intelligence Schema',
    'content': f"""Polsia is the autonomous company intelligence system in ShareOS. When a new venture is created or analyzed, Polsia automatically scrapes the company's website, generates brand DNA, audits SEO, maps competitors, checks AI search visibility, and searches for relevant patents and grants. It populates 6 MongoDB collections per venture.

## Collections Overview

| Collection | Documents | Purpose |
|------------|-----------|---------|
| {Q}polsia_okara_brand_dna{Q} | 39+ | Mission, vision, values, brand voice, target personas, visual identity, positioning |
| {Q}polsia_okara_seo{Q} | 39+ | SEO audit: meta tags, headings, page speed, content quality, link analysis |
| {Q}polsia_okara_competitors{Q} | 39+ | Direct/indirect competitors, market positioning, feature comparison |
| {Q}polsia_okara_geo{Q} | 39+ | AI search engine visibility across ChatGPT, Gemini, Perplexity, Claude |
| {Q}polsia_okara_grants{Q} | 47+ | Matching government/foundation grants with eligibility and deadlines |
| {Q}polsia_okara_patents{Q} | 46+ | Related patent landscape, IP risks, white space opportunities |

---

## polsia_okara_brand_dna

Comprehensive brand identity analysis generated from website scraping and AI analysis.

| Key | Type | Description |
|-----|------|-------------|
| {Q}domain{Q} | string | Company domain (e.g., "feno.co"). Primary key linking to other Polsia collections. |
| {Q}generated_at{Q} | datetime | When this brand DNA was generated. |
| {Q}source{Q} | string | Data source used (e.g., "firecrawl_live_scrape"). |
| {Q}links_discovered{Q} | integer | Number of links found during scraping. |
| {Q}pages_scraped{Q} | integer | Number of pages successfully scraped and analyzed. |
| {Q}scraped_urls{Q} | array of strings | URLs that were scraped. |
| {Q}raw{Q} | string | Raw JSON output from the AI analysis before parsing into structured fields. |
| {Q}brand_voice{Q} | object | Brand voice definition. See **Brand Voice** below. |
| {Q}messaging{Q} | object | Core messaging framework. See **Messaging** below. |
| {Q}target_personas{Q} | array of objects | Target customer personas. See **Persona** below. |
| {Q}visual_identity{Q} | object | Visual brand guidelines. See **Visual Identity** below. |
| {Q}brand_archetypes{Q} | object | Brand archetype classification. See **Archetypes** below. |
| {Q}competitive_positioning{Q} | object | Market positioning strategy. See **Competitive Positioning** below. |
| {Q}brand_positioning{Q} | object | Brand positioning framework. See **Brand Positioning** below. |
| {Q}brand_story{Q} | object | Brand narrative and values. See **Brand Story** below. |
| {Q}content_themes{Q} | array of objects | Content strategy themes. See **Content Theme** below. |
| {Q}products{Q} | array of objects | Products identified on the website. See **Product** below. |
| {Q}social_proof{Q} | object | Trust and credibility signals. See **Social Proof** below. |

### Brand Voice Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}tone{Q} | string | Brand tone description (e.g., "Confident, science-driven, approachable"). |
| {Q}personality_traits{Q} | array of strings | Brand personality traits. |
| {Q}language_style{Q} | string | Writing style guidelines. |
| {Q}communication_principles{Q} | array of strings | Core communication rules. |
| {Q}sample_phrases{Q} | array of strings | Example phrases that embody the brand voice. |

### Messaging Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}tagline{Q} | string | Primary tagline. |
| {Q}value_proposition{Q} | string | Core value proposition statement. |
| {Q}key_messages{Q} | array of strings | Top messaging pillars. |
| {Q}objection_handling{Q} | object or array | Common objections and responses. |
| {Q}content_pillars{Q} | array of strings | Content strategy pillars. |

### Persona Object (inside {Q}target_personas{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}name{Q} | string | Persona name/archetype (e.g., "Health-Conscious Professional"). |
| {Q}age_range{Q} | string | Target age range (e.g., "30-50"). |
| {Q}description{Q} | string | Detailed persona description. |
| {Q}motivations{Q} | array of strings | What drives this persona. |
| {Q}pain_points{Q} | array of strings | Problems this persona faces. |

### Visual Identity Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}color_palette{Q} | array or object | Brand colors with hex codes and usage rules. |
| {Q}color_psychology{Q} | string | Reasoning behind color choices. |
| {Q}typography{Q} | object | Font families, weights, and usage. |
| {Q}imagery_style{Q} | string | Photography/illustration style guidelines. |
| {Q}design_principles{Q} | array of strings | Core design rules. |

### Archetypes Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}primary{Q} | string | Primary brand archetype (e.g., "The Sage", "The Creator"). |
| {Q}secondary{Q} | string | Secondary archetype for nuance. |
| {Q}rationale{Q} | string | Why these archetypes were chosen. |

### Competitive Positioning Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}category{Q} | string | Market category definition. |
| {Q}position_statement{Q} | string | Formal positioning statement. |
| {Q}differentiators{Q} | array of strings | Key competitive differentiators. |
| {Q}competitive_landscape{Q} | string or object | Overview of the competitive field. |
| {Q}price_positioning{Q} | string | Price positioning strategy (premium, mid-market, etc.). |

### Brand Positioning Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}category{Q} | string | Category the brand competes in. |
| {Q}market_position{Q} | string | Current market position. |
| {Q}competitive_frame{Q} | string | Frame of reference vs competitors. |
| {Q}brand_promise{Q} | string | Core brand promise to customers. |
| {Q}emotional_territory{Q} | string | Emotional space the brand owns. |

### Brand Story Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}origin_narrative{Q} | string | How and why the brand was created. |
| {Q}mission{Q} | string | Brand mission statement. |
| {Q}vision{Q} | string | Brand vision for the future. |
| {Q}brand_values{Q} | array of strings | Core values. |
| {Q}brand_archetype{Q} | string | Archetype reference. |

### Content Theme Object (inside {Q}content_themes{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}theme{Q} | string | Theme name (e.g., "Science of Oral Health"). |
| {Q}description{Q} | string | What content falls under this theme. |
| {Q}content_types{Q} | array of strings | Types of content (blog, video, infographic, etc.). |

### Product Object (inside {Q}products{Q})

| Key | Type | Description |
|-----|------|-------------|
| {Q}name{Q} | string | Product name. |
| {Q}price{Q} | string | Product price or pricing range. |
| {Q}description{Q} | string | Product description. |
| {Q}key_features{Q} | array of strings | Main product features. |

### Social Proof Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}media_features{Q} | array of strings | Media publications that featured the brand. |
| {Q}credibility_signals{Q} | array of strings | Trust signals (certifications, partnerships, awards). |
| {Q}trust_builders{Q} | array of strings | Elements that build customer trust. |

---

## polsia_okara_seo

SEO audit results including on-page analysis, technical health, content quality, and link profile.

| Key | Type | Description |
|-----|------|-------------|
| {Q}domain{Q} | string | Company domain audited. |
| {Q}url{Q} | string | Specific URL audited (usually homepage). |
| {Q}audited_at{Q} | datetime | Audit timestamp. |
| {Q}source{Q} | string | Tools used (e.g., "google_pagespeed_insights + firecrawl_content"). |
| {Q}overall_score{Q} | integer | 0-100 overall SEO score. |
| {Q}on_page_score{Q} | integer | 0-100 on-page optimization score. |
| {Q}content_score{Q} | integer | 0-100 content quality score. |
| {Q}technical_score{Q} | integer | 0-100 technical SEO score. |
| {Q}mobile_score{Q} | integer or null | Mobile optimization score. null if not tested. |
| {Q}performance_score{Q} | integer or null | Page performance score. |
| {Q}title{Q} | string | Page title as found. |
| {Q}title_tag{Q} | object | Title tag analysis: {{score, current, issues, suggested}}. |
| {Q}meta_description{Q} | string or null | Meta description as found. null if missing. |
| {Q}headings{Q} | object | Heading structure analysis: {{score, structure, issues}}. |
| {Q}keywords{Q} | array of strings | Keywords detected on the page. |
| {Q}content_quality{Q} | object | Content assessment: {{score, word_count_estimate, issues, strengths}}. |
| {Q}links{Q} | object | Link analysis: {{score, internal_links, external_links, issues}}. |
| {Q}technical{Q} | object | Technical SEO: {{score, issues, strengths}}. |
| {Q}issues{Q} | array of objects | All SEO issues found with severity and recommendations. |
| {Q}recommendations{Q} | array of strings | Prioritized actionable recommendations. |
| {Q}competitive_gap_analysis{Q} | object | SEO gaps vs competitors: {{note, gaps}}. |
| {Q}page_speed{Q} | integer or null | Page speed score. |
| {Q}pagespeed_raw{Q} | object | Raw PageSpeed Insights data. |
| {Q}link_velocity{Q} | integer | Rate of new backlinks acquired. |
| {Q}referring_domains{Q} | integer | Number of unique referring domains. |
| {Q}top_referring_domains{Q} | array of objects | Top backlink sources with domain authority. |

---

## polsia_okara_competitors

Competitive landscape analysis identifying direct and indirect competitors.

| Key | Type | Description |
|-----|------|-------------|
| {Q}domain{Q} | string | Company domain analyzed. |
| {Q}analyzed_at{Q} | datetime | Analysis timestamp. |
| {Q}total{Q} | integer | Total competitors identified. |
| {Q}new_found{Q} | integer | New competitors found in this scan vs previous. |
| {Q}sources{Q} | array of strings | Data sources used (e.g., ["openai_web_search", "fundraising_scrapes"]). |
| {Q}competitive_advantages{Q} | array of strings | The venture's advantages over competitors. |
| {Q}market_overview{Q} | object | Market context: {{market_size, growth_rate, key_trends, market_drivers}}. |
| {Q}competitors{Q} | array of objects | Individual competitor profiles. See **Competitor** below. |

### Competitor Object

| Key | Type | Description |
|-----|------|-------------|
| {Q}name{Q} | string | Competitor company name. |
| {Q}website{Q} | string | Competitor website URL. |
| {Q}features{Q} | array of strings | Key product features. |
| {Q}platform{Q} | string | Platform type (e.g., "SaaS", "Hardware", "Marketplace"). |
| {Q}category{Q} | string | "direct" or "indirect" competitor. |
| {Q}focus{Q} | string | Primary market focus area. |

---

## polsia_okara_geo

AI search engine optimization (GEO) visibility analysis across major AI platforms.

| Key | Type | Description |
|-----|------|-------------|
| {Q}domain{Q} | string | Company domain checked. |
| {Q}checked_at{Q} | datetime | Check timestamp. |
| {Q}source{Q} | string | Analysis methodology used. |
| {Q}query_used{Q} | string | Search query used for testing visibility. |
| {Q}overall_geo_score{Q} | integer | 0-100 overall AI search visibility score. |
| {Q}overall_score{Q} | integer | Alternate overall score. |
| {Q}visibility_level{Q} | string | Visibility classification (e.g., "moderate", "high", "low"). |
| {Q}total_mentions{Q} | integer | Total brand mentions across all AI platforms. |
| {Q}brand_mentions_estimate{Q} | integer | Estimated mentions in AI responses. |
| {Q}avg_position{Q} | float | Average position when mentioned in AI responses. |
| {Q}platforms_queried{Q} | integer | Number of AI platforms tested. |
| {Q}platforms_responded{Q} | integer | Number that included the brand in responses. |
| {Q}platforms{Q} | object | Per-platform results summary. |
| {Q}chatgpt{Q} | object | ChatGPT-specific visibility data. |
| {Q}claude{Q} | object | Claude-specific visibility data. |
| {Q}google_ai{Q} | object | Google AI Overview visibility data. |
| {Q}perplexity{Q} | object | Perplexity-specific visibility data. |
| {Q}platform_raw_responses{Q} | object | Raw responses from each AI platform. |
| {Q}sentiment{Q} | string | Overall sentiment of AI mentions (positive, neutral, negative). |
| {Q}content_signals{Q} | object | Content optimization signals for improving AI visibility. |
| {Q}keywords_analyzed{Q} | integer | Number of keywords tested. |
| {Q}recommendations{Q} | array of strings | Actionable recommendations to improve GEO. |

---

## polsia_okara_grants

Government and foundation grant opportunities matched to the venture.

| Key | Type | Description |
|-----|------|-------------|
| {Q}domain{Q} | string | Company domain. |
| {Q}searched_at{Q} | datetime | Search timestamp. |
| {Q}source{Q} | string | Search methodology. |
| {Q}query{Q} | string | Search query used to find grants. |
| {Q}total_found{Q} | integer | Number of matching grants found. |
| {Q}recommendations{Q} | array of strings | Which grants to prioritize and why. |
| {Q}grants{Q} | array of objects | Individual grant opportunities. Each typically contains: name, organization, amount, deadline, eligibility, relevance_score, description, url. |

---

## polsia_okara_patents

Patent landscape analysis identifying IP risks, opportunities, and white spaces.

| Key | Type | Description |
|-----|------|-------------|
| {Q}domain{Q} | string | Company domain. |
| {Q}searched_at{Q} | datetime | Search timestamp. |
| {Q}query{Q} | string | Patent search query used. |
| {Q}total_found{Q} | integer | Number of relevant patents found. |
| {Q}technology_landscape{Q} | object | Overview of the technology patent landscape: density, key players, filing trends. |
| {Q}white_spaces{Q} | array of strings | Identified patent white spaces (unpatented areas the venture could claim). |
| {Q}patents{Q} | array of objects | Individual patent records. Each typically contains: title, patent_number, assignee, filing_date, abstract, relevance_score, risk_level. |

**See also:** [[polsia-intelligence]], [[venture-doc-schema]], [[venture-creation-pipeline]]"""
}


# ============================================================
# 5. COLLECTION SCHEMAS - Add Description column
# ============================================================
# This one is too large to fully rewrite in this script. 
# Instead, we'll add a note pointing to the detailed schema pages
# and fix the table format to at least have a Description column header

current_cs = None
for p in pages:
    if p['id'] == 'collection-schemas':
        current_cs = p['content']
        break

if current_cs:
    # Add description column to all 2-column tables
    # Replace "| Field | Type |" with "| Field | Type | Description |"
    # and "| Field |" (single col) with "| Field | Type | Description |"
    
    lines = current_cs.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Fix single-column header: "| Field |"
        if line.strip() == '| Field |':
            new_lines.append('| Field | Type | Description |')
            i += 1
            # Skip separator if exists
            if i < len(lines) and lines[i].strip().startswith('|---'):
                new_lines.append('|-------|------|-------------|')
                i += 1
            continue
        
        # Fix two-column header: "| Field | Type |"
        if line.strip() == '| Field | Type |':
            new_lines.append('| Field | Type | Description |')
            i += 1
            if i < len(lines) and lines[i].strip().startswith('|---'):
                new_lines.append('|-------|------|-------------|')
                i += 1
            continue
        
        # Fix data rows - add empty description
        if line.strip().startswith('| ') and not line.strip().startswith('| Field') and not line.strip().startswith('|---'):
            cells = [x.strip() for x in line.split('|')]
            cells = [c for c in cells if c != '']
            if len(cells) == 1 and not cells[0].startswith('--'):
                # Single column row - add type and description
                new_lines.append(f'| {cells[0]} | — | — |')
                i += 1
                continue
            elif len(cells) == 2:
                # Two column row - add description
                new_lines.append(f'| {cells[0]} | {cells[1]} | — |')
                i += 1
                continue
        
        new_lines.append(line)
        i += 1
    
    # Add intro note about detailed schema pages
    intro_addition = """

> **For detailed field-by-field documentation with full descriptions**, see the dedicated schema pages: [[goal-schema]], [[milestone-schema]], [[task-schema]], [[owner-schema]], [[venture-doc-schema]], [[polsia-schema]], [[venture-simulation-schema]].

"""
    
    new_content = '\n'.join(new_lines)
    # Insert after first line
    first_newline = new_content.index('\n')
    new_content = new_content[:first_newline] + '\n' + intro_addition + new_content[first_newline:]
    
    updates['collection-schemas'] = {
        'title': 'MongoDB Collection Schemas',
        'content': new_content
    }


# ============================================================
# 6. CHANNELS - Expanded
# ============================================================
updates['channels'] = {
    'title': 'Communication Channels',
    'content': f"""ShareOS operates across multiple communication channels, each serving a specific purpose in the human-AI workflow. All channels are unified through the ClawOS orchestration layer, allowing agents and humans to communicate seamlessly across platforms.

## Supported Channels

| Channel | Integration | Primary Use | Message Direction |
|---------|------------|-------------|-------------------|
| **WhatsApp** | Baileys (WA Web) | Team communication, alerts, meeting summaries, daily digests. Primary channel for Hamet and core team. | Bidirectional |
| **Telegram** | Bot API | Bot interactions, automated notifications, external user communication. | Bidirectional |
| **Email** | Gmail API + Resend + SendGrid | Outreach, investor communications, newsletters, formal correspondence. Gmail for reading, Resend/SendGrid for sending. | Bidirectional |
| **Web Client** | Next.js (stack.shareos.ai) | Primary dashboard, portfolio views, goal management, agent monitoring. | Read |
| **Slack** | Slack API | Team collaboration (select integrations). | Bidirectional |
| **Phone** | Twilio + VAPI | AI voice calls (Celli agent), outbound calls, phone-based interactions. | Outbound |
| **SMS** | Twilio (A2P) | Share Insights surveys, alerts, quick notifications. A2P messaging service for compliance. | Bidirectional |
| **Discord** | Bot API | Community engagement, skill development discussions. | Bidirectional |

## WhatsApp Groups

| Group | JID | Purpose | Members |
|-------|-----|---------|---------|
| **ClawOS** (MAIN) | {Q}120363422144289252@g.us{Q} | Primary workflow group. ALL alerts, meeting summaries, agent outputs, and daily digests go here. | Hamet, Yuvaraj, Angelica, OS |
| **ShareOS Skills** | {Q}120363424346247888@g.us{Q} | Skill development updates, new agent announcements, capability discussions. | Team + OS instances |
| **Sharefund Agents** | {Q}120363424454803947@g.us{Q} | Fund-level agent activity: deal pipeline, investor outreach, portfolio updates. | Fund team + OS |
| **Instill Agents** | {Q}120363407234097371@g.us{Q} | instill venture-specific agent activity and updates. | instill team + OS |
| **Feno Agents** | {Q}120363425476656872@g.us{Q} | Feno venture agent routing with @workstream tags. | Feno team + OS |

## Email Configuration

| Service | Purpose | From Address |
|---------|---------|-------------|
| **Gmail API** | Reading Hamet's inbox, sending on behalf | hamet@share.vc |
| **Resend API** | Transactional emails, automated sends | os@share.vc |
| **SendGrid** | Bulk email, newsletters | various @share.vc |

## Voice & Phone

| Service | Purpose | Number |
|---------|---------|--------|
| **VAPI** | AI voice agent (Celli) for inbound/outbound calls | +1 (424) 401-0557 |
| **Twilio** | SMS surveys (Share Insights), notifications | A2P messaging service |

## Channel Routing Rules

1. **Urgent items** (meetings within 24h, deal responses): WhatsApp direct to Hamet
2. **Meeting summaries**: Both current chat AND ClawOS WhatsApp group
3. **Email digests**: 3x daily (8am, 12pm, 5pm PT) — never individual alerts
4. **Scheduling/logistics**: Route to Angelica via WhatsApp + Email, skip Hamet
5. **Agent outputs**: ClawOS WhatsApp group
6. **Investor communications**: Email via Resend (os@share.vc)

## Multi-Instance Channel Architecture

Each OpenClaw instance has its own channel connections:

| Instance | WhatsApp | Telegram | Email |
|----------|----------|----------|-------|
| ShareOS (Main) | Connected | Connected | Gmail + Resend |
| Feno | Connected | — | — |
| instill | Connected | — | — |
| Shareland | Connected | — | — |
| Share Health | Connected | — | — |
| Hamet ClawOS | — | Connected | — |
| ShareMind | — | Connected | — |
| Dexter | — | — | — |

**See also:** [[clawos]], [[instances]], [[message-routing]]"""
}


# ============================================================
# 7. PERSONAS - Expanded
# ============================================================
updates['personas'] = {
    'title': 'Five User Personas',
    'content': f"""ShareOS serves five distinct user personas, each with their own portal, data access level, and interaction patterns.

## Persona Overview

| Persona | Portal | Primary Needs | Data Access |
|---------|--------|--------------|-------------|
| **LP** (Foundry Investor) | [lp.share.vc/fund](https://lp.share.vc/fund) | Fund performance, distributions, reporting, quarterly updates | Read-only: fund metrics, portfolio summary, IRR, distributions |
| **Foundry** (Share Team) | [portfolio.shareos.ai](https://portfolio.shareos.ai) | Venture dashboards, agent management, goal tracking, cross-venture analytics | Full access: all ventures, agents, goals, metrics, MongoDB |
| **Venture** (Portfolio Company) | [goals.shareos.ai](https://goals.shareos.ai) | Goal tracking, milestone management, team assignments, workstream health | Scoped: own venture only, goals/milestones/tasks, team data |
| **Circle** (External Network) | [app.shareos.ai](https://app.shareos.ai) | Collaboration, knowledge sharing, crowd tasks, feedback participation | Limited: shared surveys, public metrics, contribution tracking |
| **Agents** (Autonomous System) | [agents.sharelabs.ai](https://agents.sharelabs.ai) | Task execution, data access, cross-venture analysis, reporting | Programmatic: MongoDB read/write, API access, tool execution |

## Detailed Persona Profiles

### LP (Limited Partner / Foundry Investor)

**Who:** Investors in Share Ventures I, LP (the fund) or Share Foundry I, LLC.

**What they see:**
- Fund-level performance metrics (IRR, TVPI, DPI)
- Portfolio company summaries (stage, valuation, key milestones)
- Quarterly reports and capital call schedules
- Distribution history and projections

**What they don't see:**
- Individual goal/milestone/task details
- Internal team communications
- Agent activity or costs
- Raw MongoDB data

**Interaction pattern:** Quarterly portal visits, PDF report downloads, occasional direct communication via email.

### Foundry (Share Ventures Team)

**Who:** Hamet, Yuvaraj, Angelica, Sashank, and core Share Ventures team members.

**What they see:**
- Everything. Full access to all ventures, agents, data, and tools.
- Cross-venture analytics and comparison dashboards
- Agent org chart with performance metrics
- Planning Intelligence outputs
- Real-time workstream health across all 56+ ventures

**Interaction pattern:** Daily via WhatsApp, Telegram, email. Direct agent commands. Dashboard monitoring. Meeting summaries and action items.

### Venture (Portfolio Company)

**Who:** CEOs and teams of portfolio companies (e.g., Dean Carter at instill, Feno team).

**What they see:**
- Their own venture's goals, milestones, and tasks
- Workstream progress and health scores
- Team assignments and workload
- Stage gate criteria and progress toward next stage

**What they don't see:**
- Other ventures' data
- Fund-level metrics
- Cross-venture comparisons (unless shared)
- Agent cost details

**Interaction pattern:** Weekly dashboard reviews, milestone updates, quarterly planning sessions.

### Circle (External Network / Community)

**Who:** External contributors, beta testers, survey participants, advisors, and community members in Share Circles.

**What they see:**
- Surveys and feedback requests (via Share Insights)
- Public venture information
- Their own contribution history and influence points
- Reward tiers and token balances

**Interaction pattern:** SMS surveys (Cher agent), web polls, occasional product testing, referral participation.

### Agents (Autonomous AI System)

**Who:** 214+ AI agents across 36 groups, operating on 10 OpenClaw instances.

**What they access:**
- MongoDB collections (read/write as needed)
- External APIs (42+ integrations)
- File system and workspace
- Communication channels (send messages, emails)
- Tool execution (browser, code, deploy)

**Interaction pattern:** Continuous autonomous operation via cron schedules. Human-in-the-loop for approvals. Agent handoff protocols for complex tasks.

**See also:** [[overview]], [[clawos]], [[agent-org-chart]]"""
}


# ============================================================
# 8. Venture stubs - Expand with MongoDB data reference
# ============================================================
venture_expansions = {
    'venture-feno': {
        'title': 'Feno Venture',
        'content': f"""Feno is redefining oral health as the beginning of whole-body health. The fenome superintelligence engine is built for dental providers, while the consumer product is the Smartbrush.

## Quick Facts

| Field | Value |
|-------|-------|
| **Company** | Feno |
| **Vertical** | Biological |
| **Stage** | Launch |
| **Website** | [feno.co](https://feno.co/) |
| **Type** | Foundry + Fund (built by Share Labs, invested by Share Fund) |
| **OpenClaw Instance** | 34.239.121.19 |
| **ClawAPI** | fenoclawapi.shareos.ai |

## Key Distinctions

- **Provider-focused, NOT consumer-facing.** The "fenome" superintelligence engine serves dental providers and clinics. The Smartbrush is the consumer hardware product.
- **Feno is a product (Smartbrush), not a platform.** Never use "The World's First Connected Oral Health Platform."
- **Separate OpenClaw instance** with dedicated agents, ClawAPI, and WhatsApp group.

## Workstreams

All 7 workstreams are active with goals, milestones, and tasks tracked in {Q}deals_internal.feno.os_share.workstreams[]{Q}.

| Workstream | Focus |
|------------|-------|
| Product | Smartbrush hardware, fenome AI engine, provider dashboard |
| Demand | Dentist acquisition, provider onboarding, content marketing |
| Operations | Manufacturing, supply chain, quality control |
| Team | Clinical advisors, engineering team, dental partnerships |
| Partnerships | Dental schools, insurance providers, clinic networks |
| Investors | Series A fundraising, LP relations |
| Synergy | Cross-venture data sharing, ShareOS integration |

## Polsia Intelligence

Brand DNA, SEO audit, competitor analysis, GEO visibility, and patent/grant searches available in {Q}polsia_okara_*{Q} collections with domain "feno.co".

## Agent Groups

Feno-specific agents run on the Feno OpenClaw instance. The Feno Agents WhatsApp group ({Q}120363425476656872@g.us{Q}) supports @workstream tag routing.

**See also:** [[venture-list]], [[feno-brand]], [[instance-feno]], [[stages]]"""
    },
    'venture-1440': {
        'title': '1440 Venture',
        'content': f"""1440 is an AI-powered coaching platform that empowers individuals to unlock their full potential through personalized data insights, AI coaching conversations, and a reimagined approach to daily time management (1,440 minutes in a day).

## Quick Facts

| Field | Value |
|-------|-------|
| **Company** | 1440 |
| **Vertical** | Emotional |
| **Stage** | Validate |
| **Website** | [1440.ai](https://1440.ai/) |
| **Type** | Foundry (built by Share Labs) |

## Key Distinctions

- **"AI coaching" undersells 1440.** Always use differentiated, high-perceived-value language. 1440 is a comprehensive human performance platform, not just another chatbot.
- **ShareClaw is NOT 1440.** ShareClaw = consumer app, on-ramp to 1440. Completely different products. Never conflate them.
- **Celli = conversational sign-up system for 1440**, not a generic e-commerce agent.
- **1440 is NOT ShareHealth.** Different ventures. ShareHealth might license 1440 technology but they are separate entities.

## Product Components

| Component | Description |
|-----------|-------------|
| **1440 Core Platform** | AI coaching engine with personalized insights |
| **Celli** | Conversational sign-up agent using voice (VAPI + ElevenLabs) |
| **ShareClaw** | Consumer mobile app, on-ramp to 1440 platform |
| **Health Data Integration** | Junction API for wearable/health data ingestion |

## Technology Stack

- **Voice:** LiveKit + ElevenLabs for real-time AI coaching calls
- **Messaging:** Twilio SMS/WhatsApp for async coaching
- **Health Data:** Junction API for wearable integration
- **Payments:** Stripe for subscription management

**See also:** [[venture-list]], [[celli-agent]], [[1440-deep]], [[stages]]"""
    },
    'venture-instill': {
        'title': 'instill Venture',
        'content': f"""instill is a culture operating system that leverages AI to measure, build, and advance company culture. It provides real-time culture scoring, personalized insights, and actionable recommendations for leadership teams.

## Quick Facts

| Field | Value |
|-------|-------|
| **Company** | instill (always lowercase) |
| **Vertical** | Organizational |
| **Stage** | Launch |
| **Website** | [instill.ai](https://instill.ai) |
| **Type** | Foundry + Fund (built by Share Labs, invested by Share Fund) |
| **CEO** | Dean Carter (dean@instill.ai) |
| **OpenClaw Instance** | 44.203.114.96 |
| **ClawAPI** | instillclawapi.shareos.ai |

## Key Distinctions

- **Always lowercase "instill."** The brand is "instill" not "Instill". Always.
- **Dean Carter is CEO AND cofounder.** Dan Kasper is no longer with the company.
- **Nike is "powered by instill"** — never use "Nike plus Instill" as a section header.
- **Sensate is in the Share Fund portfolio, NOT the Foundry.** External investment only.
- **Separate OpenClaw instance** with dedicated agents and WhatsApp group ({Q}120363407234097371@g.us{Q}).

## Product

instill's platform provides:
- Real-time culture health scoring across teams and departments
- AI-driven insights for leadership on culture gaps and strengths
- Personalized action plans for improving organizational culture
- Integration with HR systems for continuous monitoring

## Enterprise Clients

Nike is a flagship deployment ("powered by instill") demonstrating culture measurement at scale within a Fortune 500 organization.

**See also:** [[venture-list]], [[instance-instill]], [[stages]]"""
    },
    'venture-shareland': {
        'title': 'Shareland Venture',
        'content': f"""Shareland is a real-time exchange for residential real estate tokens. It democratizes access to real estate investment through blockchain-based tokenization, allowing fractional ownership of properties.

## Quick Facts

| Field | Value |
|-------|-------|
| **Company** | Shareland |
| **Vertical** | Financial |
| **Stage** | Launch |
| **Website** | [share.land](https://share.land/) |
| **Type** | Foundry (built by Share Labs) |
| **OpenClaw Instance** | 98.81.222.36 |
| **ClawAPI** | sharelandclawapi.shareos.ai |

## Product

Shareland's platform enables:
- Fractional real estate ownership through tokenized securities
- Real-time trading of property tokens on a dedicated exchange
- Portfolio diversification with low minimum investment thresholds
- Transparent property valuation and performance tracking

## Technology

Built on blockchain/smart contract infrastructure from ShareOS's "Coordination & Exchange" horizontal. Uses the ledger and marketplace protocol layers.

**See also:** [[venture-list]], [[instance-shareland]], [[stages]]"""
    },
    'venture-spree': {
        'title': 'Spree Venture',
        'content': f"""Spree is an AI-enhanced video commerce platform curating health and wellness products for the longevity market. It combines shoppable video content with personalized product recommendations.

## Quick Facts

| Field | Value |
|-------|-------|
| **Company** | Spree |
| **Vertical** | Social |
| **Stage** | Launch |
| **Website** | [spree.shop](https://www.spree.shop) |
| **Type** | Foundry (built by Share Labs) |

## Product

Spree's platform features:
- Shoppable video content curated for health and wellness
- AI-powered product recommendations based on viewer behavior and health goals
- Creator tools for health and wellness influencers
- Integrated checkout within video experiences
- Longevity-focused product curation and marketplace

## Market Position

Targeting the intersection of the Social vertical (community, trust, content) with health/wellness commerce. Video-first shopping experience optimized for mobile.

**See also:** [[venture-list]], [[stages]]"""
    },
    'share-health-venture': {
        'title': 'Share Health Venture',
        'content': f"""Share Health operates at the intersection of healthcare and AI, focused on the Biological vertical. It has a dedicated OpenClaw instance for autonomous operations.

## Quick Facts

| Field | Value |
|-------|-------|
| **Company** | Share Health |
| **Vertical** | Biological |
| **Stage** | Launch |
| **Type** | Foundry (built by Share Labs) |
| **OpenClaw Instance** | 3.86.145.38 |
| **ClawAPI** | sharehealthclawapi.shareos.ai |

## Key Distinctions

- **Share Health is NOT 1440.** Different ventures. ShareHealth might be a licensee of 1440 technology but they are separate entities with separate operations.
- **Separate OpenClaw instance** with its own agents, ClawAPI, and WhatsApp integration.

## Technology

Leverages ShareOS's Data, Sensing & Detection horizontal for biometric capture and health data processing.

**See also:** [[venture-list]], [[instance-sharehealth]], [[stages]]"""
    },
    'share-mind-venture': {
        'title': 'Share Mind Venture',
        'content': f"""Share Mind is the human expertise + agent speed platform. It combines human intelligence with AI agent capabilities for tasks that require both depth of understanding and rapid execution.

## Quick Facts

| Field | Value |
|-------|-------|
| **Company** | Share Mind |
| **Vertical** | Cognitive |
| **Type** | Foundry (built by Share Labs) |
| **OpenClaw Instance** | 54.87.71.65 |
| **Telegram Group** | ShareMind - ShareOS Channel ({Q}-1003954220514{Q}) |

## Concept

Share Mind is the distribution layer for human tasks in the ShareOS ecosystem:
- AI agents handle volume work (synthetic testing, research, filtering)
- Humans provide truth (real reactions, gut checks, creative input)
- Contributors earn Influence Points tracked per person across all ventures
- Points convert to tokens representing royalty stream rights on venture success

## Connection to Share Circles

Share Mind's human task distribution mechanism IS the Share Circles reward system. When a crowd task needs human input (naming, design feedback, product testing), it routes through Share Mind and compensates via Share Circles points/tokens.

## Key Distinctions

- **ShareClaw and wearables are 2 completely separate threads.** Never combine them with Share Mind.
- Messages to the ShareMind Telegram group must start with: "📋 [ShareOS Manager]"

**See also:** [[venture-list]], [[share-circles]], [[stages]]"""
    },
    'sense01-venture': {
        'title': 'SENSE 01 Venture',
        'content': f"""SENSE 01 is a functional fragrance venture — the first company to be fully created by the ShareOS autonomous system. It uses neuroscience-backed scent compounds to enhance cognitive performance, emotional regulation, and social bonding.

## Quick Facts

| Field | Value |
|-------|-------|
| **Company** | SENSE 01 (sense01) |
| **Vertical** | Biological + Cognitive + Emotional |
| **Stage** | Validate |
| **Website** | [sense01.sharelabs.ai](https://sense01.sharelabs.ai) |
| **Type** | Foundry (built autonomously by ShareOS) |
| **MongoDB** | deals_internal.sense01 |
| **Project Dir** | projects/vial/ (kept for compatibility) |

## Key Distinctions

- **First venture fully created by ShareOS autonomous system.** Flagship for the ACC Engine.
- **Originally "VIAL"** — renamed to SENSE 01 after "vial" → "vile" phonetic risk identified.
- **Tagline:** "The first sense, reprogrammed."

## Science & Formulation

Active compounds backed by clinical research:
- **Beta-caryophyllene** — CB2 agonist for calm without sedation
- **Linalool** — Cortisol reduction and anxiolytic effects
- **1,8-Cineole** — Cognitive enhancement and memory improvement
- **Oxytocin fragments** — Social bonding facilitation

## Product Line

Three fragrance products targeting distinct use cases:
1. **Focus** — Cognitive enhancement blend
2. **Calm** — Stress reduction blend
3. **Connect** — Social bonding blend

## Naming Exercise

Comprehensive naming exercise completed (March 2026). 60+ candidates generated, synthetic focus groups run, domain and IP checks performed. SENSE 01 selected for all-domain availability (.com .ai .co .beauty .io) and lab/formula aesthetic.

## Detailed Documentation

Full playbook, workstream analysis, content library, financial model, and competitive analysis available in the dedicated SENSE 01 wiki section (40+ pages).

**See also:** [[sense01-analysis]], [[venture-list]], [[acc-engine]], [[stages]]"""
    }
}
updates.update(venture_expansions)


# ============================================================
# 9. CELLI AGENT - Expanded
# ============================================================
updates['celli-agent'] = {
    'title': 'Celli Conversational Agent',
    'content': f"""Celli is the conversational sign-up system for the 1440 platform. It uses AI voice and text to guide potential users through onboarding via natural conversation, rather than forms or web flows.

## Overview

| | |
|-|-|
| **Purpose** | Conversational sign-up and onboarding for 1440 |
| **Channels** | Voice (VAPI + ElevenLabs), SMS (Twilio), WhatsApp |
| **Phone Number** | +1 (424) 401-0557 |
| **Voice Model** | ElevenLabs (custom voice) |
| **AI Backend** | VAPI for call orchestration |

## How It Works

1. **Inbound/Outbound Call:** Celli initiates or receives a call via VAPI
2. **Conversational Onboarding:** Asks questions naturally (name, goals, health interests)
3. **Data Capture:** Responses stored in MongoDB during the conversation
4. **Profile Creation:** Automatically creates a 1440 user profile from conversation data
5. **Follow-up:** Sends confirmation via SMS/WhatsApp with next steps

## Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Call Orchestration | VAPI | Manages call flow, turn-taking, and AI responses |
| Voice Synthesis | ElevenLabs | Natural-sounding AI voice for conversations |
| Telephony | Twilio | Phone number management and call routing |
| Data Storage | MongoDB | Conversation transcripts and user profiles |
| Tunnel | loclx | Exposes local VAPI server to the internet |

## Key Distinctions

- **Celli is NOT a generic e-commerce agent.** It is specifically the conversational sign-up system for 1440.
- **Celli is NOT 1440 itself.** It is one component (the onboarding agent) within the 1440 ecosystem.

## Integration with ShareOS New Business Pipeline

Celli connects to the end-to-end new business onboarding flow:
1. Website form submission triggers VAPI outbound call
2. Celli conducts AI conversation
3. Data stored in MongoDB
4. Polsia intelligence runs on the new lead
5. Venture simulation generated
6. Results emailed/SMS'd to the prospect

**See also:** [[venture-1440]], [[1440-deep]], [[new-business-pipeline]]"""
}


# ============================================================
# 10. CRON SYSTEM - Expanded
# ============================================================
updates['cron-system'] = {
    'title': 'Agent Cron System',
    'content': f"""The Agent Cron System manages scheduled execution of all 214+ AI agents across the ShareOS platform. Agents are stored in {Q}clawos_cronjobs{Q} MongoDB collection and executed on their assigned OpenClaw instances.

## MongoDB Collection

| | |
|-|-|
| **Database** | shareos |
| **Collection** | clawos_cronjobs |
| **Documents** | 233 (129 active) |

## Cron Job Schema

| Key | Type | Description |
|-----|------|-------------|
| {Q}name{Q} | string | Unique agent name using kebab-case (e.g., "retention-churn-analyzer"). Must be unique across all instances. |
| {Q}purpose{Q} | string | What this agent does. Detailed description of its function. |
| {Q}schedule{Q} | string | Cron expression (e.g., "0 4 * * *" for daily at 4am UTC) or interval. |
| {Q}status{Q} | string | "active" (running on schedule), "paused", "disabled", or "error". |
| {Q}companies{Q} | array of strings | Ventures this agent operates on (e.g., ["feno", "instill"]). |
| {Q}workstream{Q} | string | Primary workstream: Product, Demand, Operations, Team, Partnerships, Investors, Synergy. |
| {Q}parent_group{Q} | string | Parent agent group from the Agent Org Chart (e.g., "User Engagement & Retention Agent"). |
| {Q}instance{Q} | string | OpenClaw instance this runs on (e.g., "shareos", "feno", "instill"). |
| {Q}model{Q} | string | AI model used (e.g., "anthropic/claude-sonnet-4-6", "openai/gpt-5.2"). |
| {Q}latest_output{Q} | array | Rolling last 5 outputs from recent runs. Each contains the agent's report and metrics. |
| {Q}run_history{Q} | array | Rolling last 50 run records with timestamps, duration, success/failure, and cost. |
| {Q}created_at{Q} | string | When the cron job was created. |
| {Q}updated_at{Q} | string | Last modification timestamp. |
| {Q}last_run{Q} | string | Timestamp of most recent execution. |
| {Q}next_run{Q} | string | Timestamp of next scheduled execution. |

## Agent Organization

- **36 parent groups** containing **83 sub-agents** tracking **508 KPIs**
- Organized across 7 workstreams (Product, Demand, Team, Operations, Partnerships, Investors, Synergy)
- Full org chart: {Q}agent_matrix.agent_org_chart_v2{Q} in MongoDB

## latest_output Standard (Mandatory)

Every cron job MUST write a detailed {Q}latest_output{Q} to MongoDB on every run. This is the single source of truth for agent health monitoring.

## Querying Agents

{QQ}python
# All active agents
agents = list(db.clawos_cronjobs.find({{"status": "active"}}))

# Agents for a specific company
feno_agents = list(db.clawos_cronjobs.find({{"companies": "feno"}}))

# Agents by workstream
product_agents = list(db.clawos_cronjobs.find({{"workstream": "Product"}}))
{QQ}

## Agent Dashboard

Live agent monitoring: [agents.sharelabs.ai](https://agents.sharelabs.ai)

**See also:** [[agents-overview]], [[agent-org-chart]], [[agent-roster-full]], [[planning-intelligence]]"""
}


# ============================================================
# 11. ONBOARDING - Expanded
# ============================================================
updates['onboarding'] = {
    'title': 'New Team Member Onboarding',
    'content': f"""Onboarding process for new team members joining Share Ventures or portfolio companies. Covers system access, tool setup, and orientation to the ShareOS platform.

## Day 1: System Access

| Step | Action | Tool |
|------|--------|------|
| 1 | Create ShareOS account | stack.shareos.ai |
| 2 | Add to WhatsApp ClawOS group | WhatsApp |
| 3 | Add to relevant venture WhatsApp groups | WhatsApp |
| 4 | Set up MongoDB read access | MongoDB Atlas |
| 5 | Add to Vercel team (if engineering) | Vercel |
| 6 | Configure OpenClaw instance access | SSH keys |

## Day 1: Orientation

| Step | Action | Resource |
|------|--------|----------|
| 1 | Read ShareOS Overview | [[overview]] |
| 2 | Understand the 7 verticals | [[verticals]] |
| 3 | Learn the 7 workstreams | [[workstreams]] |
| 4 | Review the valuation model | [[valuation-model]] |
| 5 | Explore the wiki | shareos-wiki.vercel.app |

## Week 1: Deep Dive

| Area | Resources |
|------|-----------|
| Goals system | [[shareos-goals-management]], [[goal-schema]] |
| Agent architecture | [[agent-org-chart]], [[agents-overview]] |
| Data schemas | [[venture-doc-schema]], [[mongodb-collections]] |
| Infrastructure | [[instances]], [[tech-stack]] |
| Daily operations | [[daily-operations]], [[heartbeat-system]] |

## Key Contacts

| Person | Role | Contact |
|--------|------|---------|
| Hamet Watt | CEO | +1 310-902-6350 |
| Yuvaraj Tankala | AI Engineering Lead | +91 8074 010 350 |
| Angelica | PA (scheduling, calendar) | +1 310-237-6170 |

## Naming Conventions to Know

1. **Share Ventures** = "venture lab and fund" (never "venture studio")
2. **Share Foundry** = the lab. **Share Fund** = the fund. Neither is a venture.
3. **instill** = always lowercase
4. **"Current valuation"** not "realized valuation"
5. **Goals = KPIs** — quantifiable, measurable, one per goal

## Tools You'll Use

| Tool | Purpose | Access |
|------|---------|--------|
| MongoDB Atlas | Data access | Read-only credentials |
| ShareOS Wiki | Documentation | shareos-wiki.vercel.app |
| OpenClaw | AI agent orchestration | Instance SSH access |
| Vercel | Deployments | Team invite |
| GitHub | Code repos | Org invite |
| WhatsApp | Team communication | Group adds |

**See also:** [[overview]], [[team-overview]], [[daily-operations]]"""
}


# ============================================================
# Apply all updates
# ============================================================
for i, p in enumerate(pages):
    if p['id'] in updates:
        pages[i]['title'] = updates[p['id']]['title']
        pages[i]['content'] = updates[p['id']]['content']
        print(f"Updated {p['id']}: {len(updates[p['id']]['content'])} chars")

# Write back
pages_json = json.dumps(pages, ensure_ascii=False)
new_line = f'const PAGES = {pages_json};'

lines = html.split('\n')
for i, line in enumerate(lines):
    if line.strip().startswith('const PAGES'):
        lines[i] = new_line
        break

version_tag = f'<!-- v{int(time.time()*1000)} -->'
new_html = '\n'.join(lines)
new_html = re.sub(r'<!-- v\d+ -->', version_tag, new_html)

open('index.html', 'w').write(new_html)
print(f"\nTotal HTML size: {len(new_html)} chars")
print(f"Pages updated: {len(updates)}")
print("Done!")
