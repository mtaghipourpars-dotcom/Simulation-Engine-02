**MAPNA PARS  
Dynamic Production Control Tower**

SIMULATION & DECISION ENGINE — IMPLEMENTATION SPECIFICATION V1.1

Software / Database / API / UI / Simulation / Scenario / Decision / Test Specification

Date: 24 September 2026 | Status: Implementation Baseline V1.1 | UI/UX & Features/Functions Update

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

0.3 ثبت تغییرات V1.1: معماری UI/UX صفحه Run Simulation، لایه‌بندی اطلاعات، Priority-First/Progressive Disclosure، کاتالوگ Features & Functions، قراردادهای تعامل، API Mapping، رفتارهای Responsive، معیارهای پذیرش UI و Layout Pseudocode به سند اضافه شد. این تغییر، منطق Engine را تغییر نمی‌دهد و صرفاً تجربه کاربری و قرارداد ارائه/تعامل آن را کامل می‌کند.

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

وضعیت این بخش: UI/UX Implementation Baseline V1.1. این بخش مرجع مستقیم تیم Frontend برای ساخت صفحه‌ها، تعاملات، حالت‌ها، Featureها و معیارهای پذیرش است.

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

## 18.1 فلسفه طراحی رابط کاربری (Design Philosophy)

صفحه «اجرای شبیه‌سازی» (Run Simulation / Scenario Workbench) صفحه قلب سیستم است. این صفحه نباید به یک داشبورد KPI یا فرم ورود اطلاعات تقلیل یابد؛ باید در یک نگاه نشان دهد «اکنون چه وضعیتی داریم»، «اگر هیچ کاری نکنیم چه خواهد شد»، «اگر این اقدام را انجام دهیم چه تغییری رخ می‌دهد» و «کدام تصمیم انسانی باید گرفته شود».

- اولویت نمایش: بحران > هشدار > عادی > تاریخی. رنگ، اندازه، موقعیت و وزن تایپوگرافی باید این اولویت را به‌صورت هم‌زمان منتقل کنند.
- اصل Progressive Disclosure: در لایه صفر فقط اطلاعات لازم برای تشخیص وضعیت و تصمیم فوری نمایش داده شود؛ جزئیات در یک کلیک و داده خام در لایه عمیق‌تر قرار گیرد.
- اصل Priority-First Display: نخستین ناحیه قابل مشاهده باید ریسک تعهد، انسداد تولید، کمبود ماده، شکاف نقدینگی، کمبود ظرفیت و تصمیم‌های معوق را نشان دهد.
- Actual، Baseline، Scenario و Forecast باید از نظر بصری و داده‌ای کاملاً متمایز باشند. گذشته هرگز در UI به‌عنوان آینده یا سناریو نمایش داده نشود.
- هیچ Action حساس بدون نمایش دامنه اثر، پیش‌شرط، زمان اثرگذاری و پیامد احتمالی قابل ثبت نباشد.
- Engine محاسبه می‌کند و UI نتیجه را توضیح می‌دهد؛ UI حق ندارد منطق شبیه‌سازی را بازتعریف یا نتیجه را حدس بزند.

## 18.2 معماری اطلاعات و لایه‌های نمایش (Information Architecture)

| **لایه**                  | **هدف**                 | **محتوا**                                                                                                     | **تعامل**                                            |
| ------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| لایه صفر — یک نگاه        | تشخیص سریع وضعیت        | هشدارهای بحرانی، وضعیت موتور، ۶ KPI اصلی، وضعیت Baseline/Scenario، دکمه اجرای شبیه‌سازی                       | بدون باز کردن صفحه جدید؛ فقط مشاهده و ورود به جزئیات |
| لایه اول — یک کلیک        | فهم علت و دامنه اثر     | جزئیات Alert، Production Flow، Resource Impact، Material Risk، Cash Requirement، Commitment Impact            | Drawer / Panel / Expand                              |
| لایه دوم — تحلیل          | تحلیل زمانی و مقایسه‌ای | Timeline روزانه، نمودارها، Resource Allocation Change، Opportunity Cost، Event Timeline، Baseline vs Scenario | فیلتر، Zoom، Drill-down، مقایسه                      |
| لایه عمیق — کنترل و ممیزی | داده خام و کنترل فنی    | Dependency Graph، Event Payload، Run Metadata، Engine Trace، Audit، Raw Data                                  | Modal / Inspector / JSON Viewer فقط برای نقش مجاز    |

## 18.3 اسکلت صفحه اجرای شبیه‌سازی (Run Simulation Page)

صفحه دسکتاپ بر مبنای شبکه ۱۲ ستونه طراحی شود. Header ثابت است؛ ناحیه Alert و KPI در بالای صفحه قرار می‌گیرند؛ Workspace اصلی در مرکز و پنل تصمیم در سمت راست قرار دارد. اسکرول صفحه فقط برای لایه‌های تحلیلی مجاز است و کنترل‌های حیاتی نباید با اسکرول از دسترس خارج شوند.

| **ناحیه**                   | **ارتفاع/نسبت پیشنهادی** | **محتوا**                                                                                             | **اولویت** |
| --------------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------- | ---------- |
| Header                      | ۵۶–۶۴ px                 | نام سامانه، Scenario، تاریخ شبیه‌سازی، Baseline، آخرین محاسبه، کیفیت داده، کاربر                      | خیلی بالا  |
| Critical Alerts Zone        | ۴۸–۸۰ px                 | بحران‌ها، تعهدات در خطر، Blockerهای جدید، Cash/Material/Machine critical                              | بحرانی     |
| System Health Bar           | ۳۲–۴۰ px                 | Engine Status، Data Freshness، Last Successful Run، Queue/Latency                                     | خیلی بالا  |
| Primary KPI Strip           | ۹۶–۱۲۰ px                | At-Risk Commitments، Blocked Cells، Material Shortage، Capacity Gap، Cash Requirement، Decision Queue | خیلی بالا  |
| Scenario Control Workspace  | ۱۸۰–۲۴۰ px               | Scenario، Policy، Horizon، Actions، Preconditions، Run/Cancel                                         | بالا       |
| Simulation/Impact Workspace | حداقل ۴۸۰ px             | Production Flow، Timeline، Constraint Impact، Resource Reallocation                                   | بالا       |
| Analysis/Decision Zone      | ۳۰۰–۴۵۰ px               | Baseline vs Scenario، Opportunity Cost، Decision Alternatives، Event Log                              | متوسط/بالا |

## 18.4 Zero Layer — Critical Alerts Zone

- Alertها به چهار سطح Critical، Warning، Normal و Historical تقسیم شوند؛ Historical نباید در کنار Critical فضای بصری هم‌وزن داشته باشد.
- هر Alert باید حداقل شامل نوع Constraint، Entity، Effective Date، Impact، Source و Action پیشنهادی/قابل بررسی باشد.
- هر Alert قرمز/کهربایی باید Drill-to-Source داشته باشد: Commitment → Product/Project → Cell → PO → Operation → Resource/Constraint.
- Alertها باید Deduplicate شوند؛ یک علت واحد نباید به ده هشدار تکراری تبدیل شود.
- در حالت Crisis، ناحیه هشدار Sticky شود و تا Acknowledge یا رفع علت باقی بماند.

## 18.5 System Health Bar

| **شاخص**         | **مقدار نمونه**                      | **رفتار UI**                                         |
| ---------------- | ------------------------------------ | ---------------------------------------------------- |
| وضعیت موتور      | Ready / Running / Completed / Failed | سبز/آبی/قرمز؛ در Running درصد پیشرفت و زمان سپری‌شده |
| تازگی داده       | مثلاً ۲ دقیقه قبل                    | در صورت عبور از آستانه، Warning و Drill-down به منبع |
| آخرین اجرای موفق | Run ID + timestamp                   | کلیک برای باز کردن نتیجه و Trace                     |
| کیفیت داده       | Valid / Warning / Blocked            | کلیک برای Data Quality Detail                        |
| زمان پاسخ        | محاسبه / صف                          | در صورت عبور از SLA، هشدار عملکردی                   |

## 18.6 Primary KPI Cards

| **KPI**                                   | **تعریف**                                                             | **نمایش اصلی**                                        | **Drill-down**     |
| ----------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------- | ------------------ |
| تعهدات در معرض ریسک (At-Risk Commitments) | تعداد/مقدار تعهداتی که Baseline یا Scenario در معرض تأخیر قرار می‌دهد | عدد بزرگ + Delta + سطح ریسک                           | Commitment Trace   |
| سلول‌های مسدود (Blocked Cells)            | Cellهایی که حداقل یک Constraint فعال دارند                            | عدد + تفکیک Material/Machine/Manpower/Cash/Dependency | Constraint List    |
| کمبود مواد (Material Shortage)            | ماده/مقدار/تاریخ اولین کمبود                                          | عدد + نزدیک‌ترین تاریخ کمبود                          | Material Forecast  |
| شکاف ظرفیت (Capacity Gap)                 | ظرفیت موردنیاز منهای ظرفیت در دسترس در بازه زمانی                     | ساعت/شیفت + تاریخ اوج                                 | Capacity Board     |
| نیاز نقدینگی (Cash Requirement)           | نیاز زمانی نقدینگی ناشی از Scenario؛ بدون خرج خودکار                  | مبلغ + تاریخ/بازه                                     | Cash Timeline      |
| صف تصمیم (Decision Queue)                 | تصمیم‌های باز با Impact و Deadline                                    | عدد + Critical Count                                  | Decision Workbench |

- KPI فقط عدد نباشد؛ هر KPI باید وضعیت، تغییر نسبت به Baseline و زمان/افق مربوطه را نشان دهد.
- KPIهای بحرانی باید در بالاترین و چپ/مرکز میدان دید قرار گیرند؛ KPIهای تاریخی به لایه دوم منتقل شوند.

## 18.7 Scenario Definition & Policy Panel

این پنل محل تعریف سناریو است و باید بین «Policy» و «Action» تفکیک بصری و داده‌ای داشته باشد. Policy رفتار موتور را در سناریو تعیین می‌کند؛ Action یک تغییر مشخص در آینده سناریو است.

| **Feature / Function**     | **ورودی**                             | **اعتبارسنجی**                       | **خروجی**                 |
| -------------------------- | ------------------------------------- | ------------------------------------ | ------------------------- |
| Scenario Selector          | Scenario ID/Name                      | Scenario قابل دسترسی و نسخه معتبر    | Scenario Snapshot         |
| Baseline Selector          | Baseline Snapshot ID                  | Snapshot immutable و معتبر           | Baseline Reference        |
| Simulation Horizon         | Start/End یا تعداد روز                | تاریخ‌ها معتبر و Start≤End           | Horizon                   |
| Resource Allocation Policy | اولویت‌های تخصیص                      | فقط Policyهای فعال/مجاز              | Allocation Policy Version |
| Commitment Priority Policy | سطح تعهد و اولویت                     | ترتیب معتبر و بدون ابهام             | Commitment Policy Version |
| Cash Policy                | محاسبه Requirement/Gap و قواعد اولویت | No Automatic Spending                | Cash Policy               |
| Capacity Policy            | Additional Shift در V1                | شیفت و ظرفیت معتبر                   | Capacity Policy           |
| Scenario Description       | هدف و فرضیات                          | حداقل توضیح برای Scenario قابل ذخیره | Audit/Trace Context       |

## 18.8 Scenario Actions — Action Builder

Action Builder باید یک Command Builder کنترل‌شده باشد. هر Action قبل از ثبت باید Target، Effective Date، Preconditions، Expected Impact و Audit Context داشته باشد.

| **Action**                    | **Target**                     | **رفتار**                                                                | **محدودیت**                                           |
| ----------------------------- | ------------------------------ | ------------------------------------------------------------------------ | ----------------------------------------------------- |
| Pause                         | Project / Cell / PO            | از تاریخ مؤثر، اجرای جدید متوقف و منابع مصرف‌نشده آزاد می‌شوند           | منابع مصرف‌شده برنمی‌گردند؛ Pause قابل Resume است     |
| Resume                        | Project / Cell / PO            | موجودیت مجدداً وارد Allocation Engine می‌شود                             | منابع قبلی Restore نمی‌شوند؛ Re-queue انجام می‌شود    |
| Cancel                        | Project / Cell / PO            | اجرای آتی متوقف و منابع مصرف‌نشده آزاد می‌شوند                           | Resume مجاز نیست؛ مصرف گذشته باقی می‌ماند             |
| Cash Injection                | Cash Pool / Scenario           | فقط به‌عنوان تصمیم/Action ثبت و در Simulation اثر نقدینگی محاسبه می‌شود  | Engine مجاز به خرج خودکار نیست                        |
| Additional Shift              | Line/Work Center/Capacity Pool | ظرفیت زمانی جدید با هزینه مرتبط اضافه می‌شود                             | V1 فقط Additional Shift؛ خرید ماشین خارج از V1        |
| Future Material/Supply Action | Material / Supply Event        | در صورت فعال شدن نسخه بعدی، زمان رسیدن و مقدار را وارد Simulation می‌کند | در V1 فقط قرارداد API/Domain برای توسعه آتی تعریف شود |

- قبل از Add Action، UI باید نشان دهد این Action روی چند Project/Cell/Commitment اثر خواهد گذاشت؛ مقدار دقیق اثر پس از Run توسط Engine محاسبه می‌شود.

## 18.9 Pre-Run Validation

| **کنترل**     | **شرط**                       | **پیام خطا/هشدار**                                                                   |
| ------------- | ----------------------------- | ------------------------------------------------------------------------------------ |
| Scenario      | Scenario و Baseline معتبر     | سناریو یا Snapshot نامعتبر است                                                       |
| Horizon       | بازه زمانی معتبر              | افق شبیه‌سازی نامعتبر است                                                            |
| Action        | Target و Effective Date معتبر | Action قابل اجرا نیست                                                                |
| Policy        | Policy Version معتبر          | Policy ناقص یا ناسازگار است                                                          |
| Data Quality  | داده‌های حیاتی موجود و تازه   | Simulation با کیفیت داده ناکافی قابل اجرا نیست یا با Warning اجرا می‌شود، طبق Policy |
| Concurrency   | Snapshot/Version unchanged    | Baseline تغییر کرده است؛ Refresh لازم است                                            |
| Authorization | کاربر مجاز                    | مجوز اجرای Action/Scenario کافی نیست                                                 |

- Validation باید قبل از شروع محاسبه انجام شود و خطاها را به‌صورت قابل اصلاح نمایش دهد؛ خطای مبهم مانند «Run Failed» کافی نیست.

## 18.10 Simulation Execution Experience

پس از Run، صفحه باید از «فرم تنظیمات» به «حالت مانیتورینگ اجرای موتور» تغییر کند. کاربر باید بداند موتور در کدام مرحله است و نتیجه موقت یا نهایی کدام است.

| **مرحله**          | **نمایش UI**     | **رفتار**                                                       |
| ------------------ | ---------------- | --------------------------------------------------------------- |
| Queued             | در صف            | شماره صف/زمان انتظار در صورت وجود                               |
| Validating         | اعتبارسنجی       | نمایش کنترل‌های در حال بررسی                                    |
| Running            | در حال شبیه‌سازی | Progress، Simulation Date، تعداد Entity پردازش‌شده، آخرین Event |
| Calculating Impact | محاسبه اثر       | نمایش حوزه‌های Production/Resource/Cash/Commitment              |
| Comparing          | مقایسه           | Baseline vs Scenario در حال آماده‌سازی                          |
| Completed          | کامل             | نمایش Result Summary و امکان باز کردن Decision Case             |
| Failed             | ناموفق           | علت دقیق، Run ID، Retry و لینک Trace                            |

## 18.11 Production Lines / Cells View

این View باید تولید را به‌صورت ساختار قابل فهم از Product/Project تا Cell/PO و Operation نمایش دهد. هدف آن تشخیص سریع محل اثر Scenario است، نه نمایش همه جزئیات در صفحه اصلی.

- سطح اول: Product/Project با وضعیت کلی، Commitment Risk و Completion Forecast.
- سطح دوم: Cell/PO با وضعیت READY/RUNNING/BLOCKED/COMPLETED/PAUSED/CANCELLED.
- سطح سوم: Operation Timeline با Machine، Manpower، Material و Duration.
- Cellهای متاثر از Scenario با Highlight و Delta نمایش داده شوند؛ Cellهای بدون اثر در حالت کم‌کنتراست قرار گیرند.
- برای هر Blocked Cell علت دقیق Constraint و زنجیره Dependency قابل مشاهده باشد.

## 18.12 Live Charts & Analysis

| **نمودار**                      | **داده**                                | **هدف**                   | **تعامل**              |
| ------------------------------- | --------------------------------------- | ------------------------- | ---------------------- |
| Baseline vs Scenario Completion | تکمیل تجمعی/Forecast                    | اثر Scenario بر تولید     | Hover + Drill-down     |
| Commitment Timeline             | Commitment Date و Forecast Date         | تشخیص تأخیر               | Click commitment       |
| Resource Load                   | Machine/Manpower/Material/Cash by day   | تشخیص Constraint          | Filter resource/date   |
| Material Forecast               | Available/Reserved/Consumed/Projected   | پیش‌بینی کمبود            | Select material        |
| Cash Requirement Timeline       | Opening/Requirement/Gap/Injection Event | زمان و مقدار نیاز نقدی    | Select date            |
| Opportunity Cost                | Gain/Loss/Displacement                  | اثر آزادسازی و تخصیص مجدد | Click affected product |
| Event Timeline                  | Action/Event/Constraint/State Change    | Traceability              | Open event detail      |

- تمام نمودارها باید Legend صریح برای Actual، Baseline، Scenario و Forecast داشته باشند.
- Tooltip باید مقدار، واحد، تاریخ و منبع را نشان دهد؛ Tooltip صرفاً تزئینی نباشد.

## 18.13 Decision & Impact Panel

پس از محاسبه، پنل تصمیم باید به‌جای نمایش یک «نتیجه خوب/بد»، مجموعه اثرات قابل مقایسه را ارائه کند. Engine انتخاب نهایی را انجام نمی‌دهد.

| **بخش**               | **محتوا**                                                  | **عملکرد**                |
| --------------------- | ---------------------------------------------------------- | ------------------------- |
| Scenario Result       | تاریخ پایان/Forecast، تعهدات، Blockerها                    | خلاصه اثر                 |
| Impact Breakdown      | Production، Resource، Material، Machine، Manpower، Cash    | Drill-down                |
| Opportunity Cost      | برنده/بازنده منابع، محصول جابه‌جا شده، ظرفیت آزادشده       | Trace                     |
| Decision Alternatives | Alternativeهای Feasible/Not Feasible با معیارهای عددی      | Compare                   |
| Decision Action       | Approve / Reject / Modify                                  | ثبت تصمیم انسانی + Audit  |
| Commit Plan           | در صورت تأیید، تبدیل Alternative/Scenario به Plan متعهدشده | نیازمند مجوز و کنترل نسخه |

- هر Alternative باید run_id و محاسبه مبنای خود را داشته باشد و قابل بازپخش باشد.

## 18.14 Event Panel & Audit Trace

- Event Panel باید آخرین Eventها را با Timestamp، Type، Entity، Source، Impact و Correlation ID نشان دهد.
- کاربر باید بتواند از Alert به Event، از Event به Entity و از Entity به Simulation Run برگردد.
- برای عملیات حساس، Audit Trail شامل Who، What، When، Why/Context، Before، After و Run/Scenario ID باشد.
- Raw Payload فقط برای نقش‌های مجاز و در لایه عمیق نمایش داده شود.

## 18.15 Smart Navigation و Drill-down Chain

مسیر استاندارد Drill-down باید قابل پیش‌بینی و در تمام صفحات ثابت باشد:

Alert → Commitment → Product/Project → Cell → Production Order → Operation → Constraint → Resource → Event → Forecast → Scenario → Alternative → Decision

- هر کارت، جدول، نمودار و Alert در صورت داشتن Source ID باید به مرحله بعدی این زنجیره متصل شود.
- Back Navigation باید Context فیلترها، تاریخ، Scenario و Scroll Position را حفظ کند.

## 18.16 Features & Functions Catalog

| **شناسه** | **Feature / Function**       | **شرح اجرایی**                                  | **سطح**      | **Acceptance**                                    |
| --------- | ---------------------------- | ----------------------------------------------- | ------------ | ------------------------------------------------- |
| UI-F01    | Scenario Selection           | انتخاب Scenario و نمایش وضعیت، نسخه و هدف       | Zero/First   | Scenario صحیح در تمام پنل‌ها Context را تعیین کند |
| UI-F02    | Baseline Snapshot Selection  | انتخاب Baseline immutable                       | First        | Snapshot ID در Run ذخیره شود                      |
| UI-F03    | Horizon Control              | تنظیم بازه شبیه‌سازی                            | Zero/First   | Start/End معتبر                                   |
| UI-F04    | Policy Editor                | نمایش/تنظیم Policyهای Scenario                  | First        | Versioned و Audit شده                             |
| UI-F05    | Action Builder               | ساخت Pause/Resume/Cancel/Cash/Shift             | First        | Precondition و Audit اجباری                       |
| UI-F06    | Pre-Run Validation           | اعتبارسنجی کامل قبل از Run                      | First        | خطای قابل اصلاح و دقیق                            |
| UI-F07    | Run Simulation               | شروع Run و نمایش وضعیت اجرای Engine             | Zero/First   | run_id و state قابل مشاهده                        |
| UI-F08    | Critical Alert Center        | نمایش بحران‌ها و هشدارهای مؤثر                  | Zero         | Drill-to-Source                                   |
| UI-F09    | KPI Strip                    | شش KPI اصلی و Delta                             | Zero         | Baseline/Scenario واضح                            |
| UI-F10    | Production Flow              | نمایش Product/Cell/Operation و اثر Scenario     | First/Second | Impact highlighting                               |
| UI-F11    | Constraint Explorer          | تفکیک Material/Machine/Manpower/Cash/Dependency | First        | Blocker دقیق                                      |
| UI-F12    | Resource Board               | بار روزانه منابع و Allocation Change            | Second       | Previous/New owner                                |
| UI-F13    | Material Forecast            | Reserved/Consumed/Available/Projected           | Second       | اولین shortage قابل تشخیص                         |
| UI-F14    | Cash Timeline                | Requirement/Gap/Injection event                 | Second       | Amount + Timing                                   |
| UI-F15    | Commitment Trace             | Commitment تا Operation و Constraint            | First/Second | Traceable                                         |
| UI-F16    | Opportunity Cost View        | Gain/Loss/Displacement                          | Second       | Affected products قابل مشاهده                     |
| UI-F17    | Baseline vs Scenario Compare | مقایسه هم‌زمان نتایج                            | Zero/Second  | Delta بدون ابهام                                  |
| UI-F18    | Decision Case Builder        | ساخت Alternative و مقایسه                       | Second       | هر Alternative به Run متصل                        |
| UI-F19    | Decision Approval            | Approve/Reject/Modify با Audit                  | First/Second | مجوز نقش‌محور                                     |
| UI-F20    | Event Timeline               | رویدادهای State/Action/Constraint               | Second       | Correlation ID                                    |
| UI-F21    | Audit Inspector              | نمایش Before/After و Actor                      | Deep         | غیرقابل‌دستکاری                                   |
| UI-F22    | Engine Trace                 | نمایش مرحله و خطای محاسبه                       | Deep         | فقط نقش مجاز                                      |
| UI-F23    | Replay                       | باز کردن Run/Scenario قبلی                      | Second/Deep  | Reproducible                                      |
| UI-F24    | Saved View                   | ذخیره فیلتر/چیدمان کاربر                        | First        | Context قابل بازیابی                              |
| UI-F25    | Responsive Control Room      | نمایش مناسب Desktop/Tablet/Mobile               | All          | بدون از دست رفتن کنترل بحرانی                     |
| UI-F26    | Data Quality Monitor         | نمایش freshness/completeness/validity           | Zero/First   | Stale data واضح                                   |
| UI-F27    | Notification Center          | اعلان Alert/Decision/Run                        | Zero/First   | Severity-aware                                    |
| UI-F28    | Search & Global Navigation   | جستجوی Project/Cell/PO/Material/Run             | All          | نتیجه با context                                  |

## 18.17 وضعیت‌های تعاملی و رفتاری UI

| **State**               | **رفتار بصری**                                | **کنترل‌های مجاز**                                |
| ----------------------- | --------------------------------------------- | ------------------------------------------------- |
| Normal                  | رنگ خنثی + KPI سبز/آبی مطابق معنا             | تمام عملیات مجاز طبق Role/Policy                  |
| Warning                 | نوار هشدار کهربایی + Highlight                | مشاهده علت، اصلاح Scenario، Run                   |
| Crisis                  | Alert Sticky، KPI بحرانی، کاهش عناصر غیرضروری | Acknowledge، Drill-down، Action/Decision طبق مجوز |
| Running                 | Progress و کنترل‌های ویرایش محدود             | مشاهده، Cancel Run در صورت پشتیبانی               |
| Completed               | نتیجه نهایی و Compare فعال                    | Create Decision Case / Replay                     |
| Failed                  | خطای دقیق و Trace                             | Retry پس از رفع علت                               |
| Maintenance / Read-only | Banner واضح و حذف کنترل‌های mutation          | فقط مشاهده/تحلیل                                  |

## 18.18 Responsive و Control-Room Design

- Desktop Control Room: حداقل عرض طراحی ۱۲۸۰ px؛ چیدمان کامل ۱۲ ستونه.
- Tablet: از ۷۶۸ تا ۱۲۷۹ px؛ پنل Decision و Detail به Drawer تبدیل شوند؛ KPIها دو ردیفه شوند.
- Mobile: زیر ۷۶۸ px؛ ترتیب نمایش فقط Priority-First باشد: Critical Alerts → System Health → KPI → Scenario Status → Actions → Decision Summary → Details.
- کنترل‌های Pause/Cancel/Approve باید هدف لمسی حداقل ۴۴×۴۴ px داشته باشند و Actionهای مخرب نیازمند Confirmation باشند.
- در Control Room، تراکم اطلاعات بالا ولی کنتراست و فاصله‌گذاری ثابت باشد؛ از Animation غیرضروری برای کاهش خستگی شیفتی استفاده نشود.
- Red/Green تنها حامل وضعیت نباشند؛ از Icon، Label و Shape نیز استفاده شود.

## 18.19 Design System و قرارداد بصری

| **عنصر**               | **قاعده**                                                              |
| ---------------------- | ---------------------------------------------------------------------- |
| Critical               | قرمز معنایی + آیکون هشدار + متن صریح؛ فقط برای خطر واقعی               |
| Warning                | کهربایی/نارنجی معنایی + وضعیت «در معرض ریسک»                           |
| Normal/Healthy         | سبز فقط برای OK/Healthy؛ از سبز برای Scenario/Information استفاده نشود |
| Simulation/Information | آبی/سایر رنگ‌های خنثی برای داده محاسباتی و وضعیت Simulation            |
| Scenario Branch        | یک نشانگر ثابت و قابل تشخیص برای تفکیک Scenario از Baseline            |
| Actual                 | رنگ/الگوی ثابت و غیرقابل اشتباه با Scenario                            |
| Historical             | کنتراست پایین‌تر و انتقال به لایه تحلیلی                               |
| Typography             | اعداد KPI بزرگ؛ Label کوتاه؛ توضیح در لایه دوم                         |
| Tables                 | ردیف بحرانی در بالا؛ Sort پیش‌فرض بر Severity/Impact نه Alphabetical   |
| Icons                  | هر Icon باید Tooltip و Label متنی داشته باشد                           |

## 18.20 UI Data Contract و API Mapping

| **Component**     | **API / Data Source**                    | **کلید اصلی**            |
| ----------------- | ---------------------------------------- | ------------------------ |
| Scenario Header   | GET /api/v1/scenarios                    | scenario_id / version    |
| Scenario Actions  | POST /api/v1/scenarios/{id}/actions      | action_id                |
| Run Control       | POST /api/v1/simulation-runs             | run_id                   |
| Run Result        | GET /api/v1/simulation-runs/{id}         | run_id                   |
| Resource Board    | GET /api/v1/resources                    | resource_id/date         |
| Material Forecast | GET /api/v1/materials/{id}/forecast      | material_id/date         |
| Commitment Trace  | GET /api/v1/commitments/{id}             | commitment_id            |
| Decision Case     | GET/POST /api/v1/decision-cases          | decision_case_id         |
| Approval          | POST /api/v1/decision-cases/{id}/approve | decision_id              |
| Cash Requirement  | GET /api/v1/cash/requirements            | cash_requirement_id/date |
| Audit             | GET /api/v1/audit-events                 | event_id/correlation_id  |

- UI نباید به پایگاه داده مستقیم متصل شود؛ تمام mutationها از API/BFF عبور کنند و correlation_id، user_id، scenario_id و run_id را منتقل کنند.

## 18.21 Performance و رفتار Frontend

- Initial shell باید سریع render شود و داده‌های لایه صفر را جداگانه و اولویت‌دار دریافت کند.
- Historical/Deep data lazy-load شود و در بارگذاری اولیه صفحه دریافت نشود.
- Polling/Streaming برای Run Status و Alerts باید محدود و قابل تنظیم باشد؛ هر Widget نباید polling مستقل ایجاد کند.
- فیلترها و Sortهای سنگین باید server-side یا روی read model مناسب انجام شوند.
- Virtualized table برای لیست‌های بزرگ Cell/Operation/Events الزامی است.
- در صورت stale شدن داده، UI باید وضعیت Stale را نمایش دهد و آخرین Timestamp معتبر را حفظ کند.

## 18.22 معیارهای پذیرش UI/UX

| **ID**  | **معیار پذیرش**                                                                                            |
| ------- | ---------------------------------------------------------------------------------------------------------- |
| UX-AC01 | کاربر در کمتر از چند ثانیه بتواند Critical Alert و وضعیت موتور را پیدا کند.                                |
| UX-AC02 | تمام KPIهای بحرانی دارای Drill-to-Source باشند.                                                            |
| UX-AC03 | Baseline و Scenario در تمام نمودارها و KPIها به‌صورت غیرقابل‌ابهام تفکیک شوند.                             |
| UX-AC04 | Run بدون Scenario/Baseline/Horizon معتبر قابل اجرا نباشد.                                                  |
| UX-AC05 | هر Action قبل از ثبت Target، Effective Date و Validation را داشته باشد.                                    |
| UX-AC06 | Pause و Cancel از نظر آزادسازی منابع مصرف‌نشده رفتار قابل مشاهده و قابل Trace داشته باشند.                 |
| UX-AC07 | Resume به‌عنوان Re-queue نمایش داده شود و UI ادعای Restore منابع قبلی نکند.                                |
| UX-AC08 | Cash Injection به‌عنوان Decision/Scenario Action نمایش داده شود و دکمه پرداخت/خرج خودکار وجود نداشته باشد. |
| UX-AC09 | پس از Run، اثر Scenario بر Commitment، Resource، Material، Cash و Opportunity Cost قابل مشاهده باشد.       |
| UX-AC10 | هر Alternative به run_id و محاسبه مربوط متصل باشد.                                                         |
| UX-AC11 | در حالت Failed، علت دقیق و Run ID و مسیر Trace نمایش داده شود.                                             |
| UX-AC12 | در Mobile فقط اطلاعات Priority-First نمایش داده شود و کنترل‌های بحرانی قابل دسترسی بمانند.                 |
| UX-AC13 | UI به‌تنهایی منطق Engine را تغییر ندهد و هیچ نتیجه‌ای را از روی داده ناقص حدس نزند.                        |
| UX-AC14 | Audit برای mutationهای حساس ثبت و قابل مشاهده برای نقش مجاز باشد.                                          |

## 18.23 Layout Pseudocode — Run Simulation

PAGE RunSimulation

HEADER { System; Scenario; Baseline; SimulationDate; LastCalc; DataQuality; User }

CRITICAL_ALERTS { Critical > Warning > Normal > Historical; DrillToSource }

SYSTEM_HEALTH { EngineStatus; DataFreshness; LastRun; Latency }

KPI_STRIP { AtRiskCommitments; BlockedCells; MaterialShortage; CapacityGap; CashRequirement; DecisionQueue }

SCENARIO_WORKSPACE { Scenario; Baseline; Horizon; Policies; Actions; Validation; RUN }

MAIN_WORKSPACE {

PRODUCTION_FLOW { Product/Project -> Cell/PO -> Operation; Dependency; Status }

CONSTRAINT_PANEL { Material; Machine; Manpower; Cash; Dependency }

RESOURCE_IMPACT { AllocationChange; Release; Reallocation; OpportunityCost }

}

ANALYSIS_ZONE { BaselineVsScenario; Timeline; MaterialForecast; CashTimeline; CommitmentImpact }

DECISION_ZONE { Alternatives; Feasibility; Impact; OpportunityCost; Approve/Reject/Modify }

EVENT_PANEL { Action; Event; StateChange; Audit; Trace }

DEEP_INSPECTOR { RawData; DependencyGraph; EngineTrace; RunMetadata }

## 18.24 خروجی مورد انتظار از صفحه

در پایان هر Run، صفحه باید بدون نیاز به باز کردن چند صفحه دیگر بتواند پاسخ چهار سؤال مدیریتی را ارائه کند: «چه چیزی در خطر است؟»، «چرا در خطر است؟»، «اگر این سناریو را اجرا کنیم چه تغییری رخ می‌دهد؟»، و «برای تصمیم انسانی چه گزینه‌های عددی و قابل ردیابی وجود دارد؟». هر جزئیات اضافی باید در لایه‌های Progressive Disclosure قرار گیرد و نباید میدان دید تصمیم را اشغال کند.

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