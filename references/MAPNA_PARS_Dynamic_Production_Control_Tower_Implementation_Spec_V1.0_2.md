**MAPNA PARS  
Dynamic Production Control Tower**

**SIMULATION & DECISION ENGINE — IMPLEMENTATION SPECIFICATION V1.0**

Software / Database / API / UI / Simulation / Scenario / Decision / Test Specification

Date: 24 September 2026 | Status: Implementation Baseline

# 0\. هدف، مرز و Source of Truth

این سند مشخصات اجرایی V1 موتور Dynamic Production Control Tower است. هسته سیستم یک شبیه‌ساز زمان‌مند و تصمیم‌یار است، نه Dashboard. گذشته Fact و immutable است؛ آینده Plan/Forecast/Scenario و قابل بازبرنامه‌ریزی است. Cell کوچک‌ترین واحد قابل‌کنترل تولید است و هر Component یک Production Order متناظر دارد.

این سند بر اساس معماری و قواعد قبلی پروژه، فایل DEMO، گزارش Scenario Engine و تصمیم‌های صریح کاربر تدوین شده است. داده‌های فایل DEMO synthetic هستند و داده واقعی MAPNA محسوب نمی‌شوند. fileciteturn10file0

## 0.1 تصمیم‌های Freeze شده

| موضوع                  | Rule                                                                               |
| ---------------------- | ---------------------------------------------------------------------------------- |
| Resource Allocation    | Scenario-Based Policy؛ اولویت تخصیص در Scenario تعریف می‌شود، نه Rule ثابت Engine. |
| Commitment Priority    | Scenario-Based Policy.                                                             |
| Cash                   | فقط محاسبه Cash Requirement / Availability / Gap / Impact.                         |
| Cash Injection         | فقط Decision/Scenario Action؛ خرج خودکار ممنوع.                                    |
| Cash Spending Priority | Policy قابل تنظیم در Scenario.                                                     |
| Capacity V1            | Additional Shift فقط.                                                              |
| Machine Purchase       | خارج از V1.                                                                        |
| Pause / Cancel         | منابع مصرف‌نشده از روز مؤثر آزاد می‌شوند؛ Cancel قابل Resume نیست.                 |
| Resume                 | Re-queue در Allocation Engine؛ منابع قبلی restore نمی‌شوند.                        |

## 0.2 اصول غیرقابل مذاکره

- Actual history never mutates.
- Scenario فقط future overlay روی Baseline Snapshot است.
- Action و State دو مفهوم جدا هستند.
- Engine محاسبه/شبیه‌سازی می‌کند؛ انسان تصمیم می‌گیرد.
- هر blocker باید علت دقیق و قابل trace داشته باشد.
- برای ورودی یکسان، Run باید deterministic باشد.
- Cash Injection به‌تنهایی Material ایجاد نمی‌کند.
- Cell seriality داخل PO است؛ بین POها dependency-driven است.

# 1\. معماری کلان

```
COMMITMENT -> PRODUCT -> BOM/COMPONENT -> PRODUCTION ORDER -> OPERATIONS -> RESOURCE DEMAND -> DAILY SIMULATION -> FORECAST/RISK -> SCENARIO -> FEASIBILITY -> DECISION CASE -> HUMAN DECISION -> COMMITTED PLAN -> EXECUTION/ACTUAL -> LEARNING
```

| Layer         | Responsibility                                                                              |
| ------------- | ------------------------------------------------------------------------------------------- |
| UI            | Control Tower, Planning Workspace, Scenario Lab, Resource Board, Decision Workbench         |
| API           | REST/JSON commands and queries, validation, auth, audit                                     |
| Application   | Scenario, Planning, Decision, Master Data services                                          |
| Simulation    | Daily Engine, Dependency, Allocation, Material, Machine, Manpower, Cash, Capacity, Forecast |
| Domain        | Cell, PO, Operation, Resource, Commitment, Scenario, Action, Decision Case                  |
| Persistence   | PostgreSQL + snapshots + ledgers + audit                                                    |
| Integration   | SAP adapter; future MES/SCADA/OPC-UA adapters                                               |
| Observability | Logs, metrics, traces, run evidence                                                         |

سند معماری قبلی همین boundary را تثبیت می‌کند: SAP S/4HANA برای facts متعلق به SAP سیستم عملیاتی است و Control Tower لایه برنامه‌ریزی/impact-analysis/decision است. fileciteturn10file5

# 2\. Domain Model

## 2.1 Aggregate Roots

| Aggregate        | Owns                             | Relations                     |
| ---------------- | -------------------------------- | ----------------------------- |
| Project          | state, actions, commitments      | Project 1:N Product           |
| Product          | definition and rollup            | Product 1:N Component         |
| Cell/Component   | controllable manufacturing unit  | Cell 1:1 PO                   |
| Production Order | operations and future allocation | PO 1:N Operation              |
| Operation        | execution/resource demand        | Operation N:1 Resource        |
| Resource         | capacity/calendar/allocation     | Resource 1:N Allocation       |
| Material         | stock/reservation/receipt        | Material 1:N Ledger           |
| Commitment       | due/priority/criticality         | Commitment -> Project/Product |
| Scenario         | snapshot/policies/actions/runs   | Scenario 1:N Action           |
| Decision Case    | problem/alternatives/approval    | Case 1:N Alternative          |
| Simulation Run   | inputs/outputs/evidence          | Run 1:N Daily Snapshot        |

## 2.2 Canonical Cell

```
Cell
├ identity
├ product
├ component
├ productionOrder
├ routing
├ operations[]
├ machineAssignment[]
├ materialRequirements[]
├ manpowerRequirements[]
├ plannedState
├ actualState
├ simulationState
├ costState
├ qualityState (future)
├ maintenanceContext (future)
└ deviationModel (future)
```

- Cell مستقل از Siemens/GE/SAP/SCADA است. ISA-95 reference boundary است، نه تعریف vendor-specific Cell.
- هر Component یک PO دارد.
- هر PO چند Operation دارد؛ Operationها sequential هستند.
- POها از BOM/precedence dependency می‌گیرند و globally serial نیستند.

## 2.3 Common Metadata

```
id, source_system, source_object, source_id, version, status, created_at, updated_at, valid_from, valid_to, snapshot_id, confidence, quality_status
```

# 3\. State Machine

```
DRAFT -> PLANNED -> READY -> RUNNING -> COMPLETED
READY/BLOCKED/RUNNING -> PAUSED -> READY/BLOCKED
PAUSED -> CANCELLED
BLOCKED reasons = MATERIAL | MACHINE | MANPOWER | DEPENDENCY | CASH | MULTI_CONSTRAINT
PROJECT: CREATED -> RUNNING -> PAUSED -> RUNNING; PAUSED -> CANCELLED; RUNNING -> COMPLETED
```

- COMPLETED و CANCELLED terminal هستند.
- RUNNING بدون current operation معتبر ممنوع است.
- BLOCKED حداقل یک blocker code دارد.
- هر transition یک event و audit record تولید می‌کند.

# 4\. Database Design

## 4.1 Technology Baseline

- PostgreSQL 16+ recommended.
- UUID technical IDs + business IDs as unique keys.
- UTC timestamps; planning_date in plant timezone.
- NUMERIC/Decimal for money; never float.
- JSONB only for extensible policy/metadata; core business fields relational.
- Foreign keys enforced.
- Immutable facts are append-only/versioned, not soft-deleted.

## 4.2 Physical Schema

| Table                 | Core columns / purpose                                            |
| --------------------- | ----------------------------------------------------------------- |
| organization          | company, business_unit, plant, department                         |
| project               | project, status, priority, planned/forecast completion            |
| product               | product, group, project_id                                        |
| component             | cell/component, product_id, BOM node                              |
| bom_precedence        | predecessor_component_id, successor_component_id, rule            |
| production_order      | po_no, component_id, status, dates                                |
| operation             | po_id, sequence_no, work_center_id, duration, status, progress    |
| operation_material    | operation_id, material_id, qty_required, qty_consumed             |
| operation_manpower    | operation_id, skill_id, qty_required                              |
| resource              | resource_id, type, status                                         |
| machine               | resource_id, capability, calendar_id                              |
| operator              | resource_id, skills                                               |
| material              | material_id, unit, valuation, planning_policy                     |
| material_stock        | material_id, date, free_qty, reserved_qty, in_transit_qty         |
| material_ledger       | material_id, event_type, qty, source, effective_date              |
| resource_calendar     | resource_id, date, available_hours, shift_code                    |
| resource_allocation   | resource_id, operation_id, start/end, status                      |
| commitment            | type, due_date, priority, criticality, penalty, status            |
| scenario              | scenario_id, baseline_snapshot_id, horizon                        |
| scenario_policy       | scenario_id, policy_type, mode, parameters_json                   |
| scenario_action       | scenario_id, action_type, target, effective_date, parameters_json |
| simulation_run        | run_id, scenario_id, seed, engine_version, status                 |
| daily_snapshot        | run_id, date, entity_type/id, state_json                          |
| constraint            | run_id, date, entity, type, severity, details_json                |
| forecast              | run_id, entity, forecast_date, confidence, basis                  |
| resource_release      | run_id/action, resource, qty, effective_date                      |
| resource_reallocation | resource, previous/new consumer, dates, idle_days                 |
| opportunity_cost      | run, action, beneficiary, displaced entity, impact                |
| decision_case         | case, problem, status, owner                                      |
| decision_alternative  | case, type, parameters, run, feasibility                          |
| decision_approval     | case, alternative, decision, actor, timestamp                     |
| cash_account          | account, currency, opening_balance                                |
| cash_flow             | account, date, type, amount, source                               |
| cash_requirement      | run, date, source, amount, reason                                 |
| purchase_plan         | material, qty, cost, order/receipt dates                          |
| capacity_action       | scenario/action, shift, scope, added_hours, cost                  |
| audit_event           | event, actor, timestamp, entity, before/after                     |

## 4.3 Indexes

- production_order(component_id,status)
- operation(po_id,sequence_no)
- operation(status,planned_start_date)
- bom_precedence(predecessor_component_id,successor_component_id)
- resource_allocation(resource_id,start_date,end_date)
- material_stock(material_id,stock_date)
- material_ledger(material_id,effective_date)
- scenario_action(scenario_id,effective_date)
- daily_snapshot(run_id,planning_date,entity_type,entity_id)
- constraint(run_id,planning_date,severity)
- commitment(due_date,priority,status)

# 5\. Resource Allocation Engine

```
Candidates -> Dependency Gate -> Material Gate -> Machine Gate -> Manpower Gate -> Cash Gate -> Policy Ranking -> Allocation -> Reservation/Lock -> Explainability
```

| Mode          | Definition                                        |
| ------------- | ------------------------------------------------- |
| LEXICOGRAPHIC | Criterion 1 dominates; ties go to next criterion. |
| WEIGHTED      | Normalized criteria × configurable weights.       |
| RULESET       | Explicit if/then rules.                           |
| HYBRID        | Hard gates then lexicographic/weighted ranking.   |

- Configurable criteria: Hard Commitment, Critical Path/Constraint Impact, Required Delivery Date, Project Priority, Operation Readiness, Resource Efficiency, FIFO.
- The exact order/weights are scenario policy, not permanent engine logic.
- Allocation result must explain why a candidate won and which candidates were displaced.

# 6\. Scenario / Policy Model

```
SCENARIO
├ Baseline Snapshot
├ Policy Set
│ ├ Resource Allocation Policy
│ ├ Commitment Priority Policy
│ ├ Cash Priority Policy
│ └ Capacity Policy
├ Actions
│ ├ PAUSE
│ ├ RESUME
│ ├ CANCEL
│ ├ CASH_INJECTION
│ └ ADD_SHIFT
└ Simulation Runs
```

- Policy answers how competing feasible choices are ranked.
- Action changes future state.
- Scenario lifecycle: DRAFT -> READY -> RUNNING -> CALCULATED -> COMPARED -> APPROVED/DISCARDED.
- Scenario never mutates actual/baseline; it stores future overlays/deltas.

# 7\. Material Engine

```
PO START -> reserve ALL PO materials -> free decreases / reserved increases
OPERATION EXECUTION -> consume OperationMaterials -> reserved decreases / consumed ledger increases
PAUSE/CANCEL -> release ONLY unconsumed reservations from effective day
```

- Consumption is never returned by Pause/Cancel.
- Shortage creates MATERIAL blocker with first shortage date, required, available and affected demand lines.
- Cash -> Procurement -> Supplier Lead Time -> Goods Receipt -> Free Stock -> Reservation -> Consumption.
- No instant material creation from cash.

# 8\. Machine Engine

```
AVAILABLE -> ALLOCATED/LOCKED -> RELEASED
                 -> FAILED / MAINTENANCE
```

- Machine is locked only for current operation, not whole PO.
- Capability compatibility is a hard gate unless substitution is configured.
- Downtime/maintenance overlays future capacity.
- Every release/reallocation records previous/new consumer and idle days.

# 9\. Manpower Engine

- Canonical manpower is operation-level.
- Skill and quantity are hard gates unless substitution rule exists.
- Manpower locks for current operation and releases at completion.
- Absence is an effective-date capacity reduction.
- Demo may infer operators, but production model supports explicit OperationManpower.

# 10\. Cash Engine

```
Projected Cash(t) = Opening Cash + Expected Inflows(t) - Expected Outflows(t) + Approved Scenario Injections(t)
```

- Engine calculates Cash Requirement, Cash Availability, Cash Gap, timing and impact.
- Engine cannot spend cash or approve procurement.
- CASH_INJECTION is only a Decision/Scenario Action.
- Cash priority is scenario policy.
- A cheaper alternative does not automatically win if it creates an unacceptable cash exposure; the exposure must be shown to the decision maker.

# 11\. Capacity / Additional Shift Engine

- V1 Capacity Expansion = Additional Shift.
- Machine purchase is out of scope.
- Additional shift adds time-phased hours and requires manpower/skill feasibility.
- Incremental overtime/energy/variable costs become Cash Requirement.
- ADD_SHIFT is scenario-only until approved.

```
ADD_SHIFT -> Added Capacity -> Manpower Gate -> Cost -> Cash Requirement -> Re-schedule -> Commitment Impact
```

# 12\. Action / Event Engine

```
{ actionId, actionType, targetType, targetId, effectiveDate, source, scenarioId, parameters }
```

| Action         | Semantics                                                                |
| -------------- | ------------------------------------------------------------------------ |
| PAUSE          | Release unconsumed resources from effective day; future execution stops. |
| RESUME         | Requeue into allocation engine; no automatic restore.                    |
| CANCEL         | Same resource release as Pause; terminal.                                |
| CASH_INJECTION | Increase modeled liquidity from effective date only.                     |
| ADD_SHIFT      | Add configured capacity with constraints/cost.                           |

```
Action/Event -> State Transition -> Resource Recalculation -> Dependency Propagation -> Forecast -> Impact
```

# 13\. Daily Simulation Algorithm

```
FOR each day D:
1 Load immutable actual + baseline future state
2 Apply scenario actions effective on D
3 Rebuild resource/material/cash availability
4 Find runnable operations from dependency graph
5 Apply hard gates
6 Rank using scenario policy
7 Reserve PO materials at PO start
8 Allocate/lock machine + manpower
9 Advance one day
10 Consume operation materials
11 Complete finished operations
12 Release resources
13 Propagate downstream readiness
14 Recalculate forecast/commitment impact
15 Persist snapshot/ledger/events
16 Close D
```

برای مقیاس فعلی (~1,800 PO و ~13,000 Operation) از row-by-row dataframe simulation در production استفاده نشود؛ graph adjacency، indexed queries، in-memory run state و batch persistence استفاده شود.

# 14\. Forecast Engine

| Output              | Definition                                                     |
| ------------------- | -------------------------------------------------------------- |
| Forecast Completion | Expected completion date under state/policy.                   |
| First Shortage      | First date demand exceeds supply.                              |
| Resource Conflict   | First critical capacity conflict.                              |
| Commitment Status   | ON TRACK if forecast <= due date; otherwise AT RISK.           |
| Delay               | max(0, forecast completion - commitment due date).             |
| Confidence          | Data/forecast confidence; not a probability unless calibrated. |

- FACT/LIVE/PLAN/ASSUMPTION/DEMO tags must remain explicit.
- Missing data must surface as data-quality blocker; never silently become zero.

# 15\. Opportunity Cost Engine

```
PAUSE A -> RESOURCE RELEASE -> ALLOCATION -> B ACCELERATES / C DISPLACED -> compare baseline vs scenario
```

- Record direct gain, direct loss, completion delta, commitment delta, cash delta, utilization delta, displaced consumers and net portfolio effect.
- Opportunity cost is first-class persisted data.

# 16\. Decision Case Engine

| Object        | Question                                                                  |
| ------------- | ------------------------------------------------------------------------- |
| Scenario      | What happens if we do X?                                                  |
| Decision Case | Which feasible alternatives should management compare and decide between? |

```
DECISION CASE
Problem / Baseline / Constraint / Horizon
Alternatives: PAUSE CELL | CASH INJECTION | ADD SHIFT | COMBINATION
```

- Every alternative references a simulation run.
- Compare feasibility, completion, commitment, cash, cost, resource impact, opportunity cost and blockers.
- Human approval is mandatory for execution of decision actions.
- Engine must never autonomously select or execute a cash/shift decision.

# 17\. API Architecture

- REST/JSON, /api/v1, HTTPS.
- Idempotency-Key for commands.
- ETag/version for optimistic concurrency.
- RFC-7807-like problem details.
- Pagination.
- Every mutation creates audit event.

| Endpoint                                 | Purpose             |
| ---------------------------------------- | ------------------- |
| GET /api/v1/projects                     | Project list        |
| POST /api/v1/projects/{id}/actions       | Project command     |
| GET /api/v1/cells/{id}                   | Cell detail         |
| GET /api/v1/production-orders/{id}       | PO detail           |
| POST /api/v1/simulation-runs             | Create run          |
| GET /api/v1/simulation-runs/{id}         | Run status/result   |
| GET/POST /api/v1/scenarios               | Scenario CRUD       |
| POST /api/v1/scenarios/{id}/actions      | Add scenario action |
| POST /api/v1/scenarios/{id}/calculate    | Calculate           |
| POST /api/v1/scenarios/{id}/compare      | Compare             |
| GET /api/v1/resources                    | Resource Board      |
| GET /api/v1/materials/{id}/forecast      | Material forecast   |
| GET /api/v1/commitments                  | Commitment trace    |
| GET/POST /api/v1/decision-cases          | Decision cases      |
| POST /api/v1/decision-cases/{id}/approve | Approval            |
| GET /api/v1/cash/requirements            | Cash requirements   |
| GET /api/v1/audit-events                 | Audit               |

```
{ commandId, status, effectiveDate, entity:{type,id}, simulationRequired, auditEventId }
```

# 18\. UI / UX

| Screen                  | Purpose                                                       |
| ----------------------- | ------------------------------------------------------------- |
| Executive Control Tower | At-risk commitments, crises, decisions, trends, drill-down    |
| Planning Workspace      | Daily timeline, products, POs, operations, resource load      |
| Scenario Lab            | Fork, policy, actions, calculate, compare                     |
| Resource Board          | Machine/material/manpower/cash by day                         |
| Material Risk           | Projected balance, shortage, affected orders                  |
| Commitment Trace        | Commitment -> product -> PO -> operation -> resource -> event |
| Decision Workbench      | Alternatives, feasibility, opportunity cost, approval         |
| Execution & Actuals     | Confirmations, consumption, reconciliation                    |
| Integration Monitor     | SAP messages, stale feeds, errors                             |

این information architecture با baseline قبلی هم‌راستا است. fileciteturn10file1

```
CONTROL TOWER
[Simulation Date] [Baseline] [Scenario] [Last Calc] [Data Quality]
KPI: At-Risk Commitments | Blocked Cells | Material Shortages | Machine Conflicts | Cash Gap | Decisions
MAIN: Commitment Risk | Production Timeline | Resource Heatmap | Material Risk | Scenario Delta | Decision Queue
```

- Every amber/red KPI must drill to source.
- Baseline vs Scenario delta always visible.
- Blocker details visible.
- Cash requirement shows timing and amount.
- RTL Persian UI; technical IDs LTR.

# 19\. Relationships & Traceability

```
Commitment -> Project/Product -> Cell -> PO -> Operation -> Resource Requirement -> Allocation -> Daily Snapshot -> Event/Constraint -> Forecast -> Scenario -> Alternative -> Decision -> Action -> Actual Outcome
```

- Every output has run_id.
- Every scenario has baseline_snapshot_id.
- Every action has action_id.
- Every alternative references calculation run.
- Source identifiers are preserved for integration traceability.

# 20\. SAP / External Integration

- SAP S/4HANA is operational source for SAP-owned facts.
- Use released APIs/contracts where available; avoid undocumented direct coupling.
- Adapter normalizes source data to canonical model.
- Inbound messages need source_id, message_id, timestamp, version, status, reconciliation key.
- Retries are idempotent.
- Rejected/ambiguous records go to quarantine.
- Future SCADA/OPC-UA integration is adapter-based and does not redefine Cell.

| Canonical            | Source class         | Ownership     |
| -------------------- | -------------------- | ------------- |
| ProductionOrder      | SAP PP               | SAP           |
| Operation/Routing    | SAP PP               | SAP           |
| Material/Stock       | SAP MM               | SAP           |
| Goods Movement       | SAP MM               | SAP           |
| Cost                 | SAP CO               | SAP           |
| Project/WBS          | SAP PS               | SAP           |
| Machine availability | PM/MES/SCADA adapter | Source        |
| Actual confirmation  | PP/MES               | Source        |
| Scenario/Decision    | Control Tower        | Control Tower |

# 21\. Security / Audit / Observability

- RBAC: Viewer, Planner, OperationsManager, SupplyManager, FinanceViewer, DecisionApprover, Admin.
- Least privilege; server-side authorization.
- Approval separated from scenario author where required.
- Secrets outside code.
- Append-only audit for business events.
- Input validation and injection/SSRF/file controls as applicable.
- No sensitive financial/employee data in ordinary logs.

Baseline security tests include expired token, wrong role, cross-plant access, injection payloads, audit immutability and secret rotation. fileciteturn10file1

## 21.1 Metrics

- simulation_run_duration_seconds
- operations_started/completed
- blocked_operations_by_reason
- resource_utilization_by_type
- material_shortage_count
- cash_gap_total
- scenario_calculation_failures
- api_latency_p50/p95/p99
- integration_stale_feed_count

# 22\. Performance / Scalability

- Support current demo scale: ~1,800 Components/POs, ~13,000 Operations, ~47,000 OperationMaterials.
- Do not hard-code 100 Cells; 1,000+ Cells expected.
- Scenario Runs can scale horizontally.
- Use batch persistence/checkpoints.
- A run remains deterministic.
- Prior architecture baseline specifies benchmark of at least 100 events/s with p95 <1s ingestion acknowledgement. fileciteturn10file1

# 23\. Testing Strategy

| Layer       | Required                                       |
| ----------- | ---------------------------------------------- |
| Unit        | Domain states, gates, formulas, policy ranking |
| Property    | No negative stock; conservation; determinism   |
| Integration | DB, API, adapters, transactions                |
| Scenario    | Branching, compare, baseline integrity         |
| E2E         | Golden production scenarios                    |
| Performance | Current + stress scale                         |
| Security    | RBAC/injection/audit/secrets                   |
| UAT         | PARS business scenarios                        |

## 23.1 Acceptance Tests T01–T22

| ID  | Test                  | Acceptance                                                       |
| --- | --------------------- | ---------------------------------------------------------------- |
| T01 | State Transition      | Allowed transitions pass; illegal transitions reject.            |
| T02 | Operation Seriality   | OPn+1 cannot run before OPn completes.                           |
| T03 | BOM Dependency        | Downstream Cell waits for predecessor condition.                 |
| T04 | Machine Allocation    | No overlapping allocation; lock only current operation.          |
| T05 | Manpower Allocation   | Skill and quantity gates enforced.                               |
| T06 | Material Reservation  | PO start reserves all PO materials from free stock.              |
| T07 | Material Consumption  | Operation consumes only operation-level materials.               |
| T08 | Material Shortage     | MATERIAL blocker + traceable demand.                             |
| T09 | Pause                 | Unconsumed resources released from effective day; flow stops.    |
| T10 | Cancel                | Same release semantics; cannot Resume.                           |
| T11 | Resume                | Requeues; no old-resource restore.                               |
| T12 | Resource Reallocation | Previous/new consumer, dates and idle days persisted.            |
| T13 | Opportunity Cost      | Gain/loss/displacement/net portfolio impact persisted.           |
| T14 | Cash Injection        | Liquidity changes from effective date; no direct stock creation. |
| T15 | Procurement Lead Time | Availability follows supplier lead time.                         |
| T16 | Material Receipt      | Receipt increases free stock on receipt date.                    |
| T17 | Extra Shift           | Capacity gain constrained by manpower/cost/calendar.             |
| T18 | Scenario Branching    | Baseline and actual history unchanged.                           |
| T19 | Baseline Integrity    | Same inputs yield reproducible result.                           |
| T20 | Commitment Impact     | Forecast vs due date produces status/delay.                      |
| T21 | Multi-Constraint      | All active blockers retained/explained.                          |
| T22 | Decision Comparison   | Alternatives calculated/compared; approval separate.             |

# 24\. Golden Scenarios

## GS-01 Pause Shared Resource

```
PAUSE PO-A on D+1 -> release unconsumed material + machine + manpower -> unrelated branches continue -> reallocation -> opportunity cost -> baseline unchanged.
```

## GS-02 Material Shortage + Cash Injection

```
Without injection: blocked. With injection D+3: cash increases D+3 -> procurement lead time -> receipt -> stock -> reservation -> production. No instant material.
```

## GS-03 Additional Shift

```
ADD_SHIFT -> added hours -> manpower/skill gate -> incremental cost/cash requirement -> revised schedule -> commitment impact; no automatic approval.
```

# 25\. Data Quality / Governance

| Tag         | Meaning                           |
| ----------- | --------------------------------- |
| FACT        | Verified historical/closed actual |
| LIVE        | Current governed feed             |
| PLAN        | Approved/planned future           |
| DEMO        | Synthetic demo                    |
| ASSUMPTION  | Explicit scenario assumption      |
| STALE       | Older than freshness threshold    |
| QUARANTINED | Rejected/ambiguous source         |

- Missing required master data must become a data-quality blocker.
- Manual overrides require actor, reason, timestamp, scope.

# 26\. Configuration / Versioning

- scenario_policy_type
- priority_criterion
- commitment_type
- blocker_type
- resource_type
- shift_type
- skill_type
- calendar_rule
- material_planning_policy
- cash_priority_policy
- forecast_confidence_rule

Policy changes create new versions. A Simulation Run retains exact policy_version, engine_version, snapshot_id and seed.

# 27\. Deployment

```
Browser -> Reverse Proxy/API Gateway -> Web UI + REST API -> Domain Services + Simulation Workers -> PostgreSQL
                                               -> Integration Adapters -> SAP / MES / SCADA / Files
```

- On-prem/private-network first.
- Simulation workers separate from synchronous API threads.
- Separate dev/test/prod databases.
- Daily full backup + PITR where supported.
- No mandatory public internet dependency for core planning.

# 28\. Implementation WBS

| Phase | Deliverable                                     |
| ----- | ----------------------------------------------- |
| P0    | Freeze specification, rules, schema, API, tests |
| P1    | Database/domain/repositories/seed               |
| P2    | Daily simulation + dependency graph             |
| P3    | Material/machine/manpower/allocation            |
| P4    | Scenario/snapshot/policy/actions/compare        |
| P5    | Cash/procurement/lead time                      |
| P6    | Additional Shift                                |
| P7    | Decision Case/opportunity cost/approval         |
| P8    | UI                                              |
| P9    | SAP integration/reconciliation                  |
| P10   | Performance/security/E2E/UAT/release evidence   |

# 29\. Machine/Agent Development Rules

- Missing rule must not be guessed; mark TODO/ASSUMPTION and stop affected behavior.
- Domain change must update schema + service + API + UI + tests + docs.
- Every feature has acceptance evidence.
- Business rules never live only in UI.
- Money uses Decimal/Numeric.
- Historical data never mutates.
- Random scheduling requires persisted seed.
- Multiple blockers are not overwritten by one reason.
- Build -> Test -> Golden Scenario -> Inspect -> Fix -> Repeat.

# 30\. Traceability Matrix

| Capability  | DB                                 | API                     | UI                 | Tests           |
| ----------- | ---------------------------------- | ----------------------- | ------------------ | --------------- |
| Cell        | component                          | /cells/{id}             | Cell Detail        | T01,T09,T10,T11 |
| Operation   | operation                          | /production-orders/{id} | Timeline           | T02             |
| Dependency  | bom_precedence                     | /dependencies           | Flow Graph         | T03             |
| Material    | stock/ledger                       | /materials/...          | Material Risk      | T06-08,T15-16   |
| Machine     | machine/allocation                 | /resources              | Resource Board     | T04,T12         |
| Manpower    | operation_manpower                 | /resources              | Resource Board     | T05             |
| Scenario    | scenario/policy/action             | /scenarios              | Scenario Lab       | T18,T19         |
| Cash        | cash/flow/requirement              | /cash/requirements      | Cash Panel         | T14             |
| Capacity    | capacity_action                    | /scenarios/actions      | Scenario Lab       | T17             |
| Commitment  | commitment                         | /commitments            | Commitment Trace   | T20             |
| Decision    | decision_case/alternative/approval | /decision-cases         | Decision Workbench | T22             |
| Opportunity | opportunity_cost                   | /scenarios/compare      | Impact Panel       | T13             |

# 31\. Non-Goals V1

- Autonomous PLC/SCADA control.
- Automatic cash spending/procurement approval.
- Machine purchase optimization.
- Minute-level APS scheduling.
- Full mathematical optimizer as prerequisite.
- Autonomous managerial decision.
- Replacement of SAP transaction processing.
- Full quality/maintenance domain implementation.

# 32\. Risks / Mitigations

| Risk                     | Mitigation                                        |
| ------------------------ | ------------------------------------------------- |
| Inventory too high       | Inventory Stress/Crisis datasets + shortage tests |
| Hard-coded priority      | Scenario Policy versioning                        |
| Baseline mutation        | Immutable snapshot + overlays + T18/T19           |
| Instant cash-to-material | Procurement lead-time chain                       |
| Global Cell seriality    | Dependency graph + operation seriality            |
| Missing manpower         | Operation-level canonical model + quality blocker |
| Performance              | Batch/graph/indexed simulation                    |
| Over-automation          | Human approval boundary                           |

# 33\. Final Release Gate

```
BUILD=PASS
DATABASE=PASS
UNIT=PASS
INTEGRATION=PASS
E2E=PASS
SECURITY=PASS
PERFORMANCE=PASS
BILINGUAL=PASS
UI=PASS
GOLDEN=PASS
TRACEABILITY=PASS
DOCUMENTATION=PASS

FINAL STATUS = READY only when all blockers PASS
```

# Appendix A — Event Catalog

| Event                     | Meaning              |
| ------------------------- | -------------------- |
| PROJECT_CREATED           | Create project       |
| PROJECT_PAUSED            | Pause project        |
| PROJECT_RESUMED           | Resume project       |
| PROJECT_CANCELLED         | Cancel project       |
| CELL_PAUSED               | Pause cell           |
| CELL_RESUMED              | Resume cell          |
| CELL_CANCELLED            | Cancel cell          |
| PO_STARTED                | Start/release PO     |
| OPERATION_STARTED         | Start operation      |
| OPERATION_COMPLETED       | Complete operation   |
| MATERIAL_RESERVED         | Reserve              |
| MATERIAL_CONSUMED         | Consume              |
| MATERIAL_RELEASED         | Release unconsumed   |
| RESOURCE_ALLOCATED        | Allocate             |
| RESOURCE_RELEASED         | Release              |
| RESOURCE_REALLOCATED      | Change consumer      |
| MACHINE_FAILED            | Capacity loss        |
| MACHINE_RESUMED           | Capacity restored    |
| CASH_INJECTION            | Liquidity action     |
| MATERIAL_PURCHASE_PLANNED | Supply plan          |
| MATERIAL_RECEIVED         | Goods receipt        |
| SHIFT_ADDED               | Capacity action      |
| SCENARIO_CREATED          | Scenario created     |
| SCENARIO_CALCULATED       | Scenario calculated  |
| DECISION_APPROVED         | Alternative approved |

# Appendix B — Error Catalog

| Code                     | Meaning                              |
| ------------------------ | ------------------------------------ |
| VALIDATION_ERROR         | Schema/business validation failure   |
| INVALID_STATE_TRANSITION | Illegal state change                 |
| BASELINE_IMMUTABLE       | Attempt to mutate fact/baseline      |
| RESOURCE_CONFLICT        | Resource unavailable                 |
| MATERIAL_SHORTAGE        | Material gate failed                 |
| MANPOWER_SHORTAGE        | Manpower gate failed                 |
| DEPENDENCY_BLOCKED       | Predecessor unmet                    |
| CASH_CONSTRAINT          | Liquidity gate failed                |
| SCENARIO_NOT_READY       | Scenario cannot run                  |
| CONCURRENCY_CONFLICT     | Version mismatch                     |
| DATA_QUALITY_BLOCK       | Missing/stale/invalid data           |
| UNAUTHORIZED             | Authentication/authorization failure |

# Appendix C — Source Register

- Dynamic_Production_Control_Tower_DEMO_v1.xlsx — synthetic master/baseline data.
- MAPNA_PARS_Dynamic_Production_Planning_Architecture_v1.0.docx — architecture baseline, domain, temporal model, UI, security, SAP and UAT.
- MAPNA_20Product_Scenario_Engine_V1_Report.xlsx — frozen Cell/PO/material/scenario rules and tests.
- User-confirmed decisions — scenario-based allocation/commitment policy, cash boundary, cash injection as Decision/Scenario Action, Additional Shift.

Concrete table names, REST paths and PostgreSQL baseline in this document are implementation specifications proposed for V1; they are not claims about an existing production system.