MAPNA PARS — Dynamic Production Control Tower

# MASTER IMPLEMENTATION CONTRACT & MACHINE EXECUTION SPECIFICATION V2.0

\*\*Date:\*\* 24 September 2026

\*\*Status:\*\* Authoritative Implementation Baseline

\*\*Purpose:\*\* Remove ambiguity from machine/agent implementation.

# 0\. Authority and Source Boundary

This document consolidates the frozen project rules from the V1 implementation specification, architecture baseline, menu/functionality specification, scenario-engine test evidence, and user-confirmed decisions. It supersedes V1 wherever this document is more specific.

- DEMO data is synthetic; never present it as real MAPNA data.
- Do not invent missing business rules.
- If a genuinely required rule is absent, create an \`IMPLEMENTATION_BLOCKER\` for the affected behavior; do not guess.
- Every capability must map to domain rule, database, service, API, UI where applicable, automated test, acceptance evidence, and documentation.
- Business rules never live only in UI.
- Simulation Engine is the authority for forecast, feasibility, allocation, resource impact, cash requirement and scenario results.
- Actual history is immutable. Scenario is a future overlay on an immutable baseline snapshot.
- Same inputs + engine version + policy version + snapshot + seed must be deterministic.
- Human decides; engine calculates. No autonomous managerial decisions.

# 1\. Product Definition

The product is a \*\*Dynamic Production Control Tower + Simulation Lab + Decision Workbench\*\*. It is not a static dashboard, not a conventional MES replacement, and not an autonomous controller.

Core loop:

\`REAL WORLD → CURRENT STATE → BASELINE FORECAST → SCENARIO → POLICY/ACTION → SIMULATION → IMPACT → DECISION CASE → HUMAN DECISION → COMMITTED PLAN → EXECUTION → ACTUAL → NEXT SIMULATION\`

V1 non-goals: autonomous PLC/SCADA control, automatic cash spending/procurement approval, machine-purchase optimization, minute-level APS scheduling, full mathematical optimization as a prerequisite, autonomous managerial decisions, replacement of SAP transaction processing, and full quality/maintenance implementation.

# 2\. Canonical Manufacturing Model

## 2.1 Cell

One Cell = one Component = one Production Order.

Cell contains identity, product, component, production order, routing, operations, machine assignments, material requirements, manpower requirements, planned state, actual state, simulation state, cost state, and future quality/maintenance/deviation extension points.

## 2.2 Seriality

- Operations inside a Production Order are strictly serial: \`OP1 → OP2 → … → OPN\`.
- Production Orders/Cells are \*\*not\*\* globally serial.
- Cross-PO execution is dependency-driven through BOM/precedence.

## 2.3 Machine

Machine is assigned at operation level and is locked only while the current operation is running. It is released at operation completion.

## 2.4 Manpower

Canonical manpower is operation-level. Skill and quantity are hard gates unless an explicit substitution rule exists. Manpower is locked only for the current operation.

## 2.5 Material

At PO start, all PO material requirements are reserved. During operation execution, only that operation's materials are consumed.

# 3\. State Machine

## Project

\`CREATED → RUNNING → PAUSED → RUNNING\`

\`RUNNING/PAUSED → CANCELLED\`

\`RUNNING → COMPLETED\`

COMPLETED and CANCELLED are terminal.

## Cell

\`DRAFT → PLANNED → READY → RUNNING → COMPLETED\`

\`READY/BLOCKED/RUNNING → PAUSED → READY/BLOCKED\`

\`PAUSED → CANCELLED\`

## Blockers

\`MATERIAL | MACHINE | MANPOWER | DEPENDENCY | CASH | MULTI_CONSTRAINT\`

## Scenario

\`DRAFT → READY → RUNNING → CALCULATED → COMPARED → APPROVED/DISCARDED\`

\*\*Action ≠ State.\*\* Every state transition produces an auditable event.

# 4\. Pause / Cancel / Resume

- \*\*PAUSE:\*\* from effective day, future execution stops for the target scope and all unconsumed resources are released.
- \*\*CANCEL:\*\* same resource-release semantics as Pause, but terminal; cannot Resume.
- \*\*RESUME:\*\* requeues into the allocation engine. It does \*\*not\*\* restore previous resources.
- Consumed material is never returned by Pause/Cancel.
- Cell Pause stops that Cell and dependent downstream work; unrelated branches continue.
- Project Pause stops new execution in the project scope; unrelated projects continue.
- Every release/reallocation records previous consumer, new consumer, release date, allocation date and idle days.

# 5\. Material Engine

\`PO START → reserve ALL PO materials → FREE decreases / RESERVED increases\`

\`OPERATION EXECUTION → consume OperationMaterials → RESERVED decreases / consumption ledger increases\`

\`PAUSE/CANCEL → release ONLY unconsumed reservations from effective day\`

Shortage must produce a MATERIAL blocker with first shortage date, required quantity, available quantity, reserved quantity, and affected demand lines.

Cash chain is mandatory:

\`CASH INJECTION → PURCHASE PLAN/ORDER → SUPPLIER LEAD TIME → GOODS RECEIPT → FREE STOCK → RESERVATION → CONSUMPTION\`

Cash injection never creates material instantly.

# 6\. Resource Allocation Engine

Pipeline:

\`CANDIDATES → DEPENDENCY GATE → MATERIAL GATE → MACHINE GATE → MANPOWER GATE → CASH GATE → POLICY RANKING → ALLOCATION → LOCK/RESERVATION → EXPLANATION\`

Allocation is \*\*Scenario-Based\*\*. The exact priority order/weights are policy data, not permanent engine logic.

Supported ranking modes:

- \`LEXICOGRAPHIC\`
- \`WEIGHTED\`
- \`RULESET\`
- \`HYBRID\`

Configurable criteria include Hard Commitment, Critical Path/Constraint Impact, Required Delivery Date, Project Priority, Operation Readiness, Resource Efficiency and FIFO.

Every allocation result must explain feasibility, selected candidate, and displaced feasible candidates.

# 7\. Commitment Priority

Scenario-based commitment types:

1\. Hard Contractual

2\. Customer Delivery

3\. Project Milestone

4\. Strategic

5\. Internal

No commitment type may bypass a hard gate automatically. Exceptions must be explicit, scenario-based, and auditable.

# 8\. Cash Engine

\`Projected Cash(t) = Opening Cash + Expected Inflows(t) - Expected Outflows(t) + Approved Scenario Injections(t)\`

Engine calculates Cash Requirement, Availability, Gap, timing and impact. Engine cannot spend cash or approve procurement. Every Cash Injection is a Decision/Scenario Action. Cash priority is scenario policy.

# 9\. Capacity Engine

V1 capacity expansion = \*\*Additional Shift only\*\*.

Additional Shift must check calendar, manpower and skill feasibility and create incremental overtime/energy/variable cost as Cash Requirement. \`ADD_SHIFT\` is scenario-only until approved. Machine acquisition is outside V1.

# 10\. Daily Simulation Algorithm

For each simulation day D:

1\. Load immutable actual state + immutable baseline snapshot.

2\. Apply scenario actions effective on D.

3\. Rebuild resource/material/cash availability.

4\. Identify runnable operations from dependency graph.

5\. Apply dependency/material/machine/manpower/cash hard gates.

6\. Rank feasible candidates using active scenario policy.

7\. Reserve all PO materials when a PO starts.

8\. Allocate/lock machine and manpower for the current operation.

9\. Advance one working simulation day.

10\. Consume operation materials.

11\. Complete operations whose required progress/duration is reached.

12\. Release machine/manpower at operation completion.

13\. Propagate downstream readiness.

14\. Recalculate forecast, shortages, conflicts and commitment impact.

15\. Persist snapshots, ledgers, allocations, constraints and audit events.

16\. Close day.

Production implementation must not use row-by-row pandas loops. Use graph adjacency, indexed queries, in-memory run state, batch persistence and checkpoints.

# 11\. Forecast / Constraint Contract

- Forecast Completion = expected completion date under current state/policy.
- First Shortage = first date demand exceeds available supply.
- Resource Conflict = first blocking/delaying capacity conflict.
- Commitment Status = ON TRACK if forecast <= due date, otherwise AT RISK.
- Delay = \`max(0, forecast - due_date)\`.
- Confidence is forecast/data confidence, not probability unless calibrated.
- Multiple blockers are retained; never overwrite one with another.
- Missing master data becomes \`DATA_QUALITY_BLOCK\`, never silent zero/null.

Data tags: \`FACT, LIVE, PLAN, DEMO, ASSUMPTION, STALE, QUARANTINED\`.

# 12\. Opportunity Cost

\`PAUSE/RELEASE → RESOURCE POOL → REALLOCATION → BENEFICIARY ACCELERATES / DISPLACED CONSUMER DELAYS\`

Persist direct gain, direct loss, completion delta, commitment delta, cash delta, utilization delta, displaced consumers and net portfolio effect.

# 13\. Scenario / Decision Case

Scenario answers: \*\*What happens if we do X?\*\*

Decision Case answers: \*\*Which feasible alternatives should management compare and decide between?\*\*

Scenario contains baseline snapshot, policy set, actions and simulation runs.

V1 actions: \`PAUSE, RESUME, CANCEL, CASH_INJECTION, ADD_SHIFT\` and explicit combinations.

Every alternative references a simulation run. Compare feasibility, completion, commitment, cash, cost, resource impact, opportunity cost, blockers and portfolio impact.

Human approval is mandatory. The engine must not autonomously select or execute cash/shift/managerial decisions.

# 14\. Database Contract

Technology baseline: PostgreSQL 16+ recommended; UUID technical IDs; unique business IDs; UTC timestamps; planning date in plant timezone; NUMERIC/Decimal for money; JSONB only for extensible policy/metadata; relational core fields; foreign keys enforced; immutable facts append-only/versioned.

Mandatory tables:

\`organization, project, product, component, bom_precedence, production_order, operation, operation_material, operation_manpower, resource, machine, operator, material, material_stock, material_ledger, resource_calendar, resource_allocation, commitment, scenario, scenario_policy, scenario_action, simulation_run, daily_snapshot, constraint, forecast, resource_release, resource_reallocation, opportunity_cost, decision_case, decision_alternative, decision_approval, cash_account, cash_flow, cash_requirement, purchase_plan, capacity_action, audit_event\`

Required indexes include production_order(component_id,status), operation(po_id,sequence_no), operation(status,planned_start_date), BOM predecessor/successor, resource allocation by resource/date, material stock/ledger by material/date, scenario actions by scenario/effective date, snapshots by run/date/entity, constraints by run/date/severity, commitments by due/priority/status.

# 15\. API Contract

Base path: \`/api/v1\`.

- \`GET /projects\`
- \`POST /projects/{id}/actions\`
- \`GET /cells/{id}\`
- \`GET /production-orders/{id}\`
- \`POST /simulation-runs\`
- \`GET /simulation-runs/{id}\`
- \`GET/POST /scenarios\`
- \`POST /scenarios/{id}/actions\`
- \`POST /scenarios/{id}/calculate\`
- \`POST /scenarios/{id}/compare\`
- \`GET /resources\`
- \`GET /materials/{id}/forecast\`
- \`GET /commitments\`
- \`GET/POST /decision-cases\`
- \`POST /decision-cases/{id}/approve\`
- \`GET /cash/requirements\`
- \`GET /audit-events\`

Commands require Idempotency-Key. Mutations use optimistic concurrency/versioning. Errors use RFC-7807-like problem details. Collection endpoints paginate. Every mutation returns command/audit identity.

# 16\. UX Master Contract

Phase 1 Experience Classes are exactly:

1\. \*\*Executive\*\*

2\. \*\*Planning & Commitment\*\*

3\. \*\*Specialist\*\*

Production/Supply/Finance are domains inside Specialist, not separate UX roles.

Principle: \*\*Role = Security; Experience = UX; Domain = Specialization; Authority = Action Rights.\*\*

## Four mandatory UX principles

1\. Progressive Disclosure

2\. Priority First

3\. Graphics First

4\. Click-to-Reveal

Layer model:

- L0 Signal
- L1 Context
- L2 Cause/Impact
- L3 Detail/Action

Actual/Baseline/Scenario must always be distinct. Every amber/red KPI must drill to source. Scenario Simulator must preserve source context. Charts are interaction surfaces. UI never recalculates authoritative results. Persian UI is RTL; technical IDs are LTR.

# 17\. Complete UI Map

## EXECUTIVE

Executive Dashboard, Portfolio, Commitments, Risks, Scenario Results, Decision Visibility.

## PLANNING

Planning Console, Production Timeline, Production Orders, Resource Allocation, Commitments, Scenario Simulator, Decision Workbench.

## SPECIALIST

My Workspace, Production, Supply, Finance, Validation, Alerts.

## ANALYSIS

Resource Board, Material Risk, Commitment Trace, Risk Center, Reports & Analytics, Forecast.

## EXECUTION

Actuals, Confirmations, Consumption, Day Close, Reconciliation.

## GOVERNANCE

Decision Cases, Approvals, Actions, Audit Trail, Lessons Learned.

## INTEGRATION

SAP / Integration Monitor.

## ADMIN

Master Data, Rules, Thresholds, Calendars, Users & Roles, Configuration, System Health.

# 18\. Page-by-Page Layer Contract

## Executive Dashboard

L0: enterprise status, at-risk commitments, blocked cells, material shortages, machine conflicts, cash gap, decisions.

L1: commitment/production/resource/material/cash context.

L2: root cause and impact.

L3: Product→Cell→PO→Operation→Machine→Material→Manpower→Dependency→Forecast→Scenario.

## Product Portfolio

L0: portfolio health. L1: family→product. L2: product→commitment→progress→constraint. L3: full production/resource/dependency trace. What-If opens contextual Scenario.

## Commitment Center

L0: health/exposure. L1: customer/product/due/forecast/variance. L2: critical path/root cause. L3: commitment→product→PO→operation→resource→constraint→scenario.

## Planning Console

L0: overloaded resources, blocked cells, late commitments, material risk, unallocated/runnable work.

L1: timeline/resource/product/commitment.

L2: resource→operations→affected products→delivery impact.

L3: inspect, governed replan/reallocate, What-If and Scenario.

Mandatory planning surfaces: Planning Day, Horizon, Gantt/Timeline, Runnable Queue, Blocked Queue with all blockers, Dependency Graph, PO/Operation sequence, Machine/Material/Manpower availability, Allocation/Reallocation, Opportunity Cost, Forecast, Commitment Impact, What-If, Scenario Simulator.

## Production Workspace

L0 production status. L1 current operations. L2 operation status/progress/resources/dependencies. L3 actual confirmation, consumption, validation and event.

## Supply Workspace

L0 supply health. L1 critical materials. L2 required/reserved/consumed/free/in-transit/expected. L3 affected demand chain and What-If.

## Finance Workspace

L0 cash position/requirement/exposure. L1 requirement by project/material/date. L2 procurement lead-time chain. L3 cash-injection scenario and production/commitment impact. No direct spending action.

## Resource Board

Machine/material/manpower by day; current consumer; future consumer; release/reallocation; idle days; opportunity cost.

## Risk Center

Machine/material/manpower/dependency/cash/commitment risks. Every risk exposes cause, impact, source and scenario path.

## Decision Workbench

Problem, baseline, alternatives, feasibility, completion, commitment, cash, cost, resource impact, opportunity cost, portfolio impact and approval. Do not label an engine-selected "best" option.

## Scenario Simulator

Scenario = baseline snapshot + policy + actions. Actions: PAUSE, RESUME, CANCEL, CASH_INJECTION, ADD_SHIFT. Show Baseline/Scenario/Delta; blockers; feasibility; forecast; commitment; cash; opportunity cost. Context is preserved from source page.

## Execution / Actuals

Actual confirmations, consumption, reconciliation and Day Close. Past facts locked; corrections are compensating events.

## Integration Monitor

Source feed health, message status, stale feeds, rejected/quarantined records, retries and reconciliation.

## Governance / Audit

Decision cases, approvals, action history, audit events, lessons learned and immutable evidence.

# 19\. Global Interaction Pattern

\`SIGNAL → CONTEXT → CAUSE → IMPACT → WHAT-IF → SIMULATION → COMPARE → DECISION\`

Every command must display target, scope and effective date before submission and return command/audit identity. Every blocker shows type, source, first blocking date and downstream impact. Every reallocation shows previous consumer, new consumer, release date, allocation date and idle days.

# 20\. SAP / Integration Contract

SAP S/4HANA is source of truth for SAP-owned operational facts. Use released APIs/contracts where available. Normalize inbound data to canonical model. Each inbound message requires source_id, message_id, timestamp, version, status and reconciliation key. Retries are idempotent. Rejected/ambiguous records go to quarantine. SCADA/OPC-UA adapters do not redefine Cell.

Canonical ownership:

- Production Order / Operation / Routing → SAP PP
- Material / Stock / Goods Movement → SAP MM
- Cost → SAP CO
- Project / WBS → SAP PS
- Machine availability → PM/MES/SCADA adapter
- Actual confirmation → SAP/MES source
- Scenario / Decision → Control Tower

# 21\. Security / Audit

Server-side authorization. Least privilege. Approval separated from scenario author where required. Secrets outside code. Append-only business audit. No sensitive financial/employee data in ordinary logs. Test expired token, wrong role, cross-plant access, injection payloads, audit immutability and secret rotation.

# 22\. Acceptance Tests T01–T22

```
| ID | Acceptance |
|---|---|
| T01 | Allowed state transitions pass; illegal transitions reject. |
| T02 | OPn+1 cannot run before OPn completes. |
| T03 | Downstream Cell waits for predecessor condition. |
| T04 | No overlapping machine allocation; lock only current operation. |
| T05 | Manpower skill and quantity gates enforced. |
| T06 | PO start reserves all PO materials from free stock. |
| T07 | Operation consumes only operation-level materials. |
| T08 | Material shortage creates traceable MATERIAL blocker. |
| T09 | Pause releases unconsumed resources from effective day and stops future flow. |
| T10 | Cancel has same release semantics and cannot Resume. |
| T11 | Resume requeues and does not restore old resources. |
| T12 | Reallocation persists previous/new consumer, dates and idle days. |
| T13 | Opportunity cost persists gain/loss/displacement/net portfolio impact. |
| T14 | Cash injection changes modeled liquidity only from effective date and never stock directly. |
| T15 | Procurement availability follows supplier lead time. |
| T16 | Receipt increases free stock on receipt date. |
| T17 | Additional Shift is constrained by manpower/cost/calendar. |
| T18 | Scenario branching leaves baseline and actual unchanged. |
| T19 | Same inputs reproduce same result. |
| T20 | Forecast vs due date produces commitment status/delay. |
| T21 | All active blockers remain visible and persisted. |
| T22 | Alternatives are calculated/compared; approval remains separate. |
```

# 23\. Golden Scenarios

- GS-01 Pause Shared Resource.
- GS-02 Material Shortage + Cash Injection.
- GS-03 Additional Shift.
- GS-04 Pause→Resume Requeue.
- GS-05 Multi-Constraint.
- GS-06 Portfolio Opportunity Cost.

# 24\. Data Quality

Tags: FACT, LIVE, PLAN, DEMO, ASSUMPTION, STALE, QUARANTINED. Missing required master data becomes a data-quality blocker. Manual overrides require actor, reason, timestamp and scope.

# 25\. Performance / Scale

Support current demo scale (~1,800 POs, ~13,000 operations, ~47,000 operation-material rows), 1,000+ Cells and horizontally scalable simulation workers. Use indexed queries, graph adjacency, in-memory run state, batch persistence and checkpoints. Persist seed, engine version, policy version and snapshot ID.

# 26\. Machine/Agent Development Workflow

1\. Read the full specification and repository before editing.

2\. Build requirement manifest and traceability matrix.

3\. Implement domain/state machine.

4\. Implement schema/migrations/invariants.

5\. Implement deterministic simulation.

6\. Implement resource/material/machine/manpower/cash gates.

7\. Implement scenario/policy/actions.

8\. Implement allocation/reallocation/opportunity cost.

9\. Implement procurement/lead time/receipt.

10\. Implement Additional Shift.

11\. Implement Decision Cases/approval boundary.

12\. Implement API/auth/audit.

13\. Implement UI information architecture.

14\. Implement integration/reconciliation.

15\. Run all tests and golden scenarios.

16\. Generate acceptance evidence.

17\. Update traceability and docs.

18\. Only then evaluate release gates.

# 27\. Definition of Done

A requirement is complete only when: domain rule implemented; DB constraints present; server-side rule implemented; API tested; UI implemented if applicable; automated tests pass; golden scenario/evidence exists where applicable; audit verified; documentation and traceability updated; no unresolved blocker remains.

# 28\. Final Release Gate

\`BUILD=PASS\`

\`DATABASE=PASS\`

\`UNIT=PASS\`

\`INTEGRATION=PASS\`

\`E2E=PASS\`

\`SECURITY=PASS\`

\`PERFORMANCE=PASS\`

\`BILINGUAL=PASS\`

\`UI=PASS\`

\`GOLDEN=PASS\`

\`TRACEABILITY=PASS\`

\`DOCUMENTATION=PASS\`

\*\*FINAL STATUS = READY only when every gate is PASS and no implementation blocker remains.\*\*