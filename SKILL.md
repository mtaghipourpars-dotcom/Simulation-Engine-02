---
name: mapna-pars-production-control-tower
description: Implements, reviews, tests, and evolves the MAPNA PARS Dynamic Production Control Tower, including deterministic production simulation, Cell/Production Order/Operation dependencies, material reservation and consumption, machine and manpower allocation, cash constraints, scenario policies, resource reallocation, opportunity cost, commitment forecasting, decision cases, SAP integration, auditability, and RTL industrial-control UX. Use when building or modifying any part of this project.
license: Proprietary
compatibility: Repository-based implementation. Requires filesystem access, source control, a supported backend/database/frontend toolchain, and the ability to run the project's automated tests. Network access is not required for core simulation execution.
metadata:
  author: MAPNA PARS project
  version: "3.0.0"
  standard: "agentskills.io"
  specification_baseline: "MASTER_SPEC_V2.0"
  project: "Dynamic Production Control Tower"
  language: "fa-IR"
---

# MAPNA PARS Dynamic Production Control Tower

## Mission
Build the system exactly from the project references. Treat the Master Specification as the authoritative implementation contract. Use the other references for detailed architecture, historical requirements, UI features, menu structure, and scenarios.

## Activation and source precedence
1. Read this file first.
2. For any implementation rule, read `references/MAPNA_PARS_Dynamic_Production_Control_Tower_MASTER_SPEC_V2.0.docx`.
3. For architecture, temporal model, domain boundaries, integration, security, and platform design, consult `references/MAPNA_PARS_Dynamic_Production_Planning_Architecture_v1.0_2.docx`.
4. For detailed engine/API/database requirements retained from the earlier baseline, consult `references/MAPNA_PARS_Dynamic_Production_Control_Tower_Implementation_Spec_V1.0_2.docx`.
5. For UI coverage and detailed screen/function behavior, consult `references/MAPNA_PARS_Dynamic_Production_Control_Tower_Implementation_Spec_V1.1_UI_Features.docx`, `references/MAPNA_PARS_Dynamic_Production_Planning_Architecture_v1.1_UI_Features.docx`, and `references/menu-functionality.md`.
6. For scenario examples and test cases, consult `references/scenarios.md`.
7. If sources conflict, use the most specific frozen rule in the Master Specification. Do not silently reconcile conflicting requirements.

## Non-negotiable implementation rules
- Do not guess a missing business rule. Create an `IMPLEMENTATION_BLOCKER` for genuinely missing required information and continue unaffected work.
- Every capability must map to domain rule, database, service/engine, API, UI where applicable, automated test, acceptance evidence, and documentation.
- Business rules never live only in the UI.
- The Simulation Engine is authoritative for forecast, feasibility, allocation, resource impact, cash requirement, and scenario results.
- Actual history is immutable. Corrections are compensating events.
- Scenarios branch from an immutable baseline snapshot and may not mutate actual history.
- Deterministic repeatability is mandatory for the same inputs, engine version, policy version, snapshot, and seed.
- Human decision/approval remains separate from calculation. Never autonomously spend cash, approve procurement, buy equipment, or make managerial decisions.
- Never mark a feature complete because a screen exists; completion requires engine/domain + persistence + API + UI where applicable + tests + evidence.

## Core manufacturing semantics
- One Cell = one Component = one Production Order.
- Operations inside a Production Order are strictly serial.
- Cells/Production Orders across a product are dependency-driven through BOM/precedence, not globally serial.
- Machine locking is operation-level and lasts only for the current running operation.
- Manpower is operation-level and locked only for the current operation.
- At Production Order start, reserve all required materials.
- During operation execution, consume only that operation's materials.
- Pause and Cancel release only unconsumed resources/reservations from the effective date; consumed material is never returned.
- Resume requeues into the allocation engine and does not restore previous resource ownership.

## Simulation execution
For each planning day:
1. Load immutable actual state and baseline snapshot.
2. Apply scenario actions effective on that date.
3. Rebuild resource, material, and cash availability.
4. Identify runnable operations from dependency graph.
5. Apply dependency, material, machine, manpower, and cash hard gates.
6. Rank feasible candidates using the active scenario policy.
7. Reserve all PO materials when the PO starts.
8. Allocate/lock machine and manpower for the current operation.
9. Advance one working simulation day.
10. Consume operation materials.
11. Complete operations that reach required progress/duration.
12. Release machine/manpower at operation completion.
13. Propagate downstream readiness.
14. Recalculate forecast, shortages, conflicts, and commitment impact.
15. Persist snapshots, ledgers, allocations, constraints, and audit events.
16. Close the day.

Do not implement the production simulator as row-by-row pandas loops. Use indexed reads, graph adjacency, in-memory run state, batch persistence, and checkpoints.

## Resource allocation
Allocation pipeline:
`CANDIDATES → DEPENDENCY GATE → MATERIAL GATE → MACHINE GATE → MANPOWER GATE → CASH GATE → POLICY RANKING → ALLOCATION → LOCK/RESERVATION → EXPLANATION`

Allocation policy is scenario-based. Never hard-code one universal winner. Supported policy modes are `LEXICOGRAPHIC`, `WEIGHTED`, `RULESET`, and `HYBRID`. Policy criteria can include hard commitment, critical-path/constraint impact, required delivery date, project priority, operation readiness, resource efficiency, and FIFO.

Every allocation result must explain feasibility, selected candidate, and displaced feasible candidates. Persist reallocation and opportunity cost.

## Cash and supply
- Calculate cash requirement, timing, availability, gap, and production/commitment impact.
- Cash injection is a scenario/decision action.
- Cash does not instantly create material.
- Required chain: `CASH INJECTION → PURCHASE PLAN/ORDER → SUPPLIER LEAD TIME → GOODS RECEIPT → FREE STOCK → RESERVATION → CONSUMPTION`.
- V1 capacity expansion is Additional Shift only. Machine acquisition is outside V1.

## Scenario and decision governance
Scenario answers: “What happens if we do X?”
Decision Case answers: “Which feasible alternatives should management compare and decide between?”

V1 scenario actions: `PAUSE`, `RESUME`, `CANCEL`, `CASH_INJECTION`, `ADD_SHIFT`, plus explicit combinations. Every alternative references a simulation run. Compare feasibility, completion, commitment, cash, cost, resources, opportunity cost, blockers, and portfolio impact. Do not label an engine-selected alternative as “best.”

## UX contract
Experience classes:
1. Executive
2. Planning & Commitment
3. Specialist

Production, Supply, and Finance are Specialist domains, not separate UX roles.

Rules:
- Role = security; Experience = UX; Domain = specialization; Authority = action rights.
- Progressive Disclosure.
- Priority First.
- Graphics First.
- Click-to-Reveal.
- L0 Signal → L1 Context → L2 Cause/Impact → L3 Detail/Action.
- Actual/Baseline/Scenario must always be distinct.
- Every amber/red KPI drills to source.
- Scenario Simulator preserves context from the originating entity/page.
- Charts are interaction surfaces.
- UI does not calculate authoritative engine results.
- Persian UI is RTL; technical identifiers are LTR.

## Required UI areas
Executive: Dashboard, Portfolio, Commitments, Risks, Scenario Results, Decision Visibility.
Planning: Planning Console, Production Timeline, Production Orders, Resource Allocation, Commitments, Scenario Simulator, Decision Workbench.
Specialist: My Workspace, Production, Supply, Finance, Validation, Alerts.
Analysis: Resource Board, Material Risk, Commitment Trace, Risk Center, Reports & Analytics, Forecast.
Execution: Actuals, Confirmations, Consumption, Day Close, Reconciliation.
Governance: Decision Cases, Approvals, Actions, Audit Trail, Lessons Learned.
Integration: SAP / Integration Monitor.
Admin: Master Data, Rules, Thresholds, Calendars, Users & Roles, Configuration, System Health.

## Integration boundary
SAP S/4HANA remains the source of truth for SAP-owned operational facts. Use approved/released integration contracts. Normalize inbound data to the canonical model. Every inbound message requires source ID, message ID, timestamp, version, status, and reconciliation key. Retries are idempotent; rejected/ambiguous records go to quarantine. SCADA/OPC-UA adapters must not redefine the Cell domain model.

## Data quality and audit
Use explicit tags: `FACT`, `LIVE`, `PLAN`, `DEMO`, `ASSUMPTION`, `STALE`, `QUARANTINED`.
Missing required master data is a blocker, never an implicit zero/null.
Actual and audit records are append-only/versioned. Manual overrides require actor, reason, timestamp, and scope.

## Testing
Implement and pass T01–T22 and the golden scenarios GS-01 through GS-06 from the Master Specification. Also verify invariants including material conservation, no negative stock, no overlapping resource allocations, dependency correctness, legal state transitions, baseline immutability, scenario isolation, and deterministic repeatability.

## Traceability and completion
Maintain `REQ-ID → domain → DB → service → API → UI → test → evidence → status`.
A requirement is `PASS` only with implementation and evidence.

Final release gates:
`BUILD`, `DATABASE`, `UNIT`, `INTEGRATION`, `E2E`, `SECURITY`, `PERFORMANCE`, `BILINGUAL`, `UI`, `GOLDEN`, `TRACEABILITY`, `DOCUMENTATION` — all must be PASS, with no unresolved implementation blocker, before status `READY`.

## Common failure modes to prevent
- Treating Cells as globally serial.
- Locking a machine for an entire PO instead of its current operation.
- Returning consumed material on Pause/Cancel.
- Restoring old resource ownership on Resume.
- Creating material instantly after Cash Injection.
- Allowing UI-side calculations to diverge from the engine.
- Mutating actual history from a scenario.
- Hiding secondary blockers.
- Hard-coding a universal resource priority.
- Calling the deterministic heuristic scheduler a mathematical optimizer.
- Treating synthetic DEMO data as real MAPNA data.
- Declaring completion without test evidence and traceability.

## When changing the system
1. Update the authoritative rule/decision record.
2. Update schema/migrations if needed.
3. Update domain/service/engine.
4. Update API contract.
5. Update UI if applicable.
6. Update automated tests and golden scenarios.
7. Update traceability and documentation.
8. Run regression and release gates.

Never patch only one layer.
