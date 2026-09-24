**SOFTWARE ARCHITECTURE DOCUMENT**

**MAPNA Generator Engineering and Manufacturing Company (PARS)**

**Dynamic Production Planning & Resource Allocation Platform**

_Architecture Baseline v1.0 — Single Source of Truth_

21 September 2026

| **Item**                | **Value**                                                                                                                                           |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Document owner          | Enterprise Architecture / Digital Manufacturing                                                                                                     |
| Business reference      | MAPNA Generator Engineering and Manufacturing Co. (PARS)                                                                                            |
| Primary external source | <https://mapnagenerator.com/>                                                                                                                       |
| Architecture scope      | Dynamic daily production planning, resource allocation, what-if scenario planning, decision support, execution feedback and organizational learning |
| Integration baseline    | SAP S/4HANA on-premise; release-specific APIs selected from SAP Business Accelerator Hub                                                            |
| Deployment principle    | On-premise-first; no mandatory public-internet dependency for core planning or execution                                                            |
| Document status         | Baseline architecture; implementation-ready logical and physical specification                                                                      |

**IMPORTANT SOURCE BOUNDARY:** The public MAPNA Generator website is used only to establish externally verifiable business context, product families and stated capabilities. Internal SAP customizing, machine IDs, routings, production volumes, costs, stock levels, customer commitments and maintenance schedules are not treated as public facts. Where internal details are required, this document defines configuration points and canonical interfaces rather than inventing internal values.

# Table of Contents

0\. Executive Architecture Summary

1\. Purpose, Scope, Design Authority and Source Basis

2\. Business Context and Domain Boundaries

3\. Architecture Principles and Non-Negotiable Rules

4\. C4 Level 1 — System Context

5\. Macro Logical Architecture

6\. Physical / Deployment Architecture

7\. Technology Stack and Engineering Standards

8\. Information Architecture and Temporal Model

9\. Core Domain Model

10\. End-to-End Business Processes

11\. Key Operations / Use Cases

12\. Dynamic Daily Planning Engine

13\. Scenario / What-If Engine

14\. Feasibility and Optimization Engine

15\. Resource Allocation and Opportunity-Cost Model

16\. Execution, Actuals and Day-Close Cycle

17\. Decision Governance and Approval Model

18\. Lesson Learned and Organizational Learning

19\. Master Data Management and Governance

20\. Database Design and Physical Schema

21\. API Architecture and Contracts

22\. SAP S/4HANA Integration Architecture

23\. Security Architecture and Threat Model

24\. Logging, Monitoring and Observability

25\. Availability, Disaster Recovery and Business Continuity

26\. DevOps, CI/CD and Release Management

27\. Data Migration and Cutover

28\. Testing Strategy and Test Cases

29\. Verification, Validation and UAT

30\. UI/UX Information Architecture

31\. Configuration, Rules and Reference Data

32\. Implementation Plan and Work Breakdown

33\. Risks, Constraints, Assumptions and Mitigations

34\. Architecture Decision Records

35\. Glossary and Abbreviations

Appendix A. Canonical Event Catalog

Appendix B. API Error Catalog

Appendix C. Source Register

# 0\. Executive Architecture Summary

The target platform is not a static dashboard and not a closed scenario viewer. It is a dynamic, time-phased planning system whose primary object is the evolving state of the enterprise production flow. The system starts from a fact-anchored current state, projects future states in daily buckets, allows controlled manipulation of future decision variables, recalculates consequences through production dependencies and constrained resources, evaluates feasibility and business value, and turns an approved plan into an operational baseline that is later reconciled with actual results.

The central design rule is: Past is Fact; Future is Plan. Actual material consumption, actual progress, actual confirmations, actual costs and closed-day machine states are immutable. Future allocations and assumptions are versioned and branchable. Every future change must be represented as a typed event and must propagate through the dependency graph from commitment to product, production order, operation, resource and financial/commitment effect.

The minimum planning quantum is one planning day. Intraday events are accepted at any time, but their planning effect is applied to the next open planning day unless a specific event type is explicitly configured as an immediate same-day capacity adjustment. The standard behavior is therefore a rolling daily planning horizon.

COMMITMENT

\-> PRODUCT / PRODUCT FAMILY

\-> BOM + ROUTING

\-> PRODUCTION ORDER

\-> OPERATIONS

\-> RESOURCE DEMAND

\-> RESOURCE STATE

\-> DAILY PLAN

\-> FORECAST / SHORTAGE / RISK

\-> SCENARIO BRANCH

\-> FEASIBILITY

\-> OPTIMIZATION

\-> MANAGEMENT DECISION

\-> COMMITTED PLAN

\-> EXECUTION

\-> ACTUAL RESULT

\-> LESSON / CALIBRATION

\-> NEXT PLAN

SAP S/4HANA is treated as the operational system of record for SAP-owned master and transactional facts. The platform is a dynamic planning, impact-analysis and decision layer around those facts; it does not recreate ERP transaction processing. All write-backs to SAP are mediated through released interfaces and explicit integration contracts.

# 1\. Purpose, Scope, Design Authority and Source Basis

## 1.1 Purpose

This document defines the complete target architecture and implementable engineering baseline for a MAPNA PARS-oriented dynamic production planning platform. It is intended to be used as the architecture baseline for backend, frontend, integration, data, QA, DevOps, security and operations teams.

## 1.2 Scope

- Dynamic daily planning from commitment through actual result.
- Time-phased capacity planning for machines/work centers, manpower, materials, cash and selected external constraints.
- Production-order and operation-level planning aligned with SAP manufacturing concepts.
- Daily forecast of material shortages, capacity overloads and commitment impacts.
- What-if scenario branching from a fact-anchored current plan.
- Feasibility calculation, resource injection requirement and opportunity-cost analysis.
- Multi-criterion optimization with configurable objective functions.
- Management decision, approval, plan commitment and execution follow-up.
- Actual-vs-forecast reconciliation and first-class lesson learned.
- SAP S/4HANA integration, security, audit, observability and controlled deployment.

## 1.3 Explicit non-scope

- Replacing SAP FI/MM/PP/SD/PS/PM/QM transaction processing.
- Direct access to SAP application database tables for business processing.
- Replacing MES/shop-floor machine controllers.
- Real-time sub-second machine control or safety interlocks.
- Autonomous management decisions without configured approval authority.
- Uncontrolled AI-generated writes into SAP or the planning baseline.

## 1.4 Source basis

The official MAPNA Generator website states that PARS was established in 1377/1998, initially to transfer technology and manufacture thermal generators up to 160 MW, hydro generators up to 250 MW and power-plant busducts; it also describes wind-turbine activity, industrial generators, traction motors, electric motors, electric-vehicle drive motors, after-sales services and specialized power services. The site also states exports to Syria, Iraq and Tajikistan. These statements define the domain vocabulary used in this architecture; internal operational data is not inferred from them. \[SRC-01\]\[SRC-02\]

**SOURCE DATA QUALITY NOTE:** The official achievements page contains a numerical inconsistency: its heading states 44,000 MW while the following paragraph states 45,000 MW. The architecture does not hard-code either figure. Any executive KPI is expected to originate from governed operational data or a separately approved corporate KPI definition. \[SRC-03\]

# 2\. Business Context and Domain Boundaries

## 2.1 Publicly verified business context

| **Domain**                         | **Verified context**                                                                                  | **Architecture implication**                                                                                   |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Power generation equipment         | Hydro, thermal and wind generator products are stated on the official site.                           | Product-family model must support different BOM/routing structures and long lead-time resource profiles.       |
| Busduct                            | Power-plant busducts are explicitly stated as a product area.                                         | Discrete manufacturing flow must support non-generator product routings.                                       |
| Industrial / traction / mobility   | Industrial generators, traction motors, electric motors and electric-vehicle drive motors are stated. | Product model must not assume every product is a generator.                                                    |
| After-sales / specialized services | After-sales and specialized power services are explicitly stated.                                     | Service-order and installed-base concepts are included as configurable domain modules.                         |
| Technology transfer / engineering  | Website describes technology-transfer and improvement work.                                           | Engineering revision and controlled configuration management are first-class master data.                      |
| International business             | Exports to Syria, Iraq and Tajikistan are stated.                                                     | Delivery commitment model must support export logistics, country-specific milestones and long lead-time risks. |

## 2.2 Internal-domain assumptions required for implementation

The following are architectural assumptions rather than public claims: discrete production orders form the execution bridge; BOM and routing determine material and capacity demand; operation confirmations form the minimum execution evidence; daily planning uses time buckets of one day; resource bottlenecks can be machines, material, manpower or cash; multiple commitments may compete for the same scarce resource; and management may change priorities or inject resources. These assumptions are encoded as configurable rules so the platform can be validated against internal PARS policy during implementation.

## 2.3 Domain boundaries

| **Domain**          | **Owned by platform**                                   | **Referenced from SAP / external**                                           | **Notes**                                                  |
| ------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Commitment          | Commitment risk, forecast and decision views            | Sales orders, project milestones, customer data                              | No duplicate commercial master unless explicitly approved. |
| Product engineering | Scenario-facing product configuration/version reference | Material, BOM, routing, engineering documents                                | Platform stores planning snapshot/version references.      |
| Production          | Dynamic plan, scenario schedule, allocation             | Production orders, operations, confirmations                                 | SAP remains transaction system of record.                  |
| Resources           | Future state, capacity overlays, scenario allocations   | Work center/master calendars, inventory, HR availability, maintenance status | Dynamic event stream is platform-owned.                    |
| Finance             | Planning cash constraints/injections and impact         | Actual FI/CO balances and postings                                           | Planning finance is not ledger accounting.                 |
| Learning            | Lessons, patterns, calibration links                    | Actual outcome evidence                                                      | Platform-owned.                                            |
| Integration         | Canonical event log and message status                  | SAP/other endpoints                                                          | Platform-owned integration audit.                          |

# 3\. Architecture Principles and Non-Negotiable Rules

| **ID** | **Principle**                    | **Mandatory rule**                                                                                                        |
| ------ | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| P01    | Past is Fact                     | Closed planning-day actuals are immutable. Corrections use compensating events.                                           |
| P02    | Future is Plan                   | Future allocations are versioned, recalculable and branchable.                                                            |
| P03    | Daily Time Quantum               | The default planning time bucket is one calendar working day.                                                             |
| P04    | State + Event + Time             | The model is defined by temporal state and typed events, not static master-data joins.                                    |
| P05    | Every Change Has Impact          | Any material planning event must be propagated through dependencies to resources and commitments.                         |
| P06    | Scenario Is a Branch             | Scenarios fork from a current plan version and store only the delta/override events.                                      |
| P07    | Feasibility Before Preference    | Infeasible alternatives are not selectable; optimization operates only on feasible plans.                                 |
| P08    | Resource Competition Is Explicit | Shared resources and opportunity cost must be visible.                                                                    |
| P09    | SAP Is Not Rebuilt               | ERP master/transaction processing remains in SAP; the platform adds dynamic planning and decision capabilities.           |
| P10    | No Direct SAP DB Access          | Only approved released APIs/events/IDocs/RFCs through the integration boundary are permitted.                             |
| P11    | Deterministic Baseline           | Same inputs and same rule/model version must produce the same baseline plan unless stochastic mode is explicitly enabled. |
| P12    | Explainable Decisions            | Every plan and scenario must expose constraints, assumptions, affected objects and calculated impacts.                    |
| P13    | AI Is Advisory                   | AI may explain/recommend/draft but deterministic engines and approval workflows control the committed plan.               |
| P14    | On-Premise Continuity            | Core planning must operate without mandatory public-internet availability.                                                |
| P15    | Everything Versioned             | Master-data references, rules, plans, scenarios, decisions and model parameters are versioned.                            |

# 4\. C4 Level 1 — System Context

Figure 4-1 — C4 Level 1 context (Mermaid)

flowchart LR

USER\[Planners / Production Managers / Supply / Finance / Maintenance / Quality / Executives\]

MAPNA\[Dynamic Production Planning & Resource Allocation Platform\]

SAP\[SAP S/4HANA On-Premise\]

MES\[MES / Shop-floor / Machine data\]

P6\[Primavera / Project planning if used\]

SCADA\[SCADA / equipment status if used\]

HR\[HR / Workforce source\]

SUP\[Suppliers / logistics / external commitments\]

IDP\[Enterprise Identity Provider\]

OBS\[Monitoring / SIEM / SOC\]

USER --> MAPNA

SAP &lt;--&gt; MAPNA

MES &lt;--&gt; MAPNA

P6 &lt;--&gt; MAPNA

SCADA --> MAPNA

HR --> MAPNA

SUP --> MAPNA

IDP --> MAPNA

MAPNA --> OBS

## 4.1 External actors

| **Actor/system**               | **Interaction**                                           | **Authority**                                                     |
| ------------------------------ | --------------------------------------------------------- | ----------------------------------------------------------------- |
| Production Planner             | Create/revise plan, inspect constraints, create scenarios | Planning authority within assigned scope                          |
| Product/Project Owner          | Raise deviation, quantify impact, submit alternatives     | Owner of case facts and mitigation proposals                      |
| Supply/Procurement             | Review material constraints and supply actions            | Supply commitments and procurement actions                        |
| Maintenance                    | Report breakdown/repair state and maintenance windows     | Machine availability state                                        |
| Finance                        | Review cash constraints and approve injections            | Financial planning authority                                      |
| Quality                        | Raise quality holds and release constraints               | Quality disposition authority                                     |
| Executive / Steering Committee | Approve high-impact plan changes                          | Final business decision within governance threshold               |
| SAP S/4HANA                    | Provide governed master and transactional facts           | System of record for SAP-owned data                               |
| MES/Shop-floor                 | Provide execution status and machine signals              | System of record for production execution events where applicable |
| Identity Provider              | Authentication/claims                                     | Identity authority                                                |

# 5\. Macro Logical Architecture

Figure 5-1 — Logical architecture

+---------------------------+

| Presentation / Experience |

| Web / RTL / Mobile Web |

+-------------+-------------+

|

+-------------v-------------+

| API Gateway / BFF |

+-------------+-------------+

|

+-------------------+---------------+--------------------+-------------------+

| | | |

+----v-----+ +------v------+ +--------v------+ +-------v-------+

| Planning | | Scenario / | | Decision / | | Master & |

| Domain | | What-if | | Governance | | Configuration|

+----+-----+ +------+------+ +-------+-------+ +------+-------+

| | | |

+-------------------+----------------+-------------------+-------------------+

|

+-------------v-------------+

| Domain / Rules Kernel |

| State + Event + Time |

+-------------+-------------+

|

+----------------+---------------+----------------+------------------+

| | | |

+-------v------+ +------v--------+ +--------v------+ +-------v------+

| Feasibility | | Optimization | | Learning / | | Integration |

| Engine | | Engine | | Calibration | | Gateway |

+-------+------+ +------+--------+ +--------+------+ +-------+------+

| | | |

+----------------+---------------+----------------+------------------+

|

+---------v---------+

| Data Platform |

| PostgreSQL / |

| Redis / Kafka / |

| Object Storage |

+-------------------+

## 5.1 Component responsibilities

| **Component**       | **Primary responsibility**                                                                                  |
| ------------------- | ----------------------------------------------------------------------------------------------------------- |
| Experience UI       | Dashboards, planning workspace, scenario lab, timeline, resource boards, approvals, audit and lesson views. |
| API Gateway/BFF     | Authentication enforcement, rate limiting, aggregation, tenant and role context, request correlation.       |
| Planning Domain     | Baseline plan generation, daily state transition, schedule and allocation management.                       |
| Scenario Domain     | Branch creation, event overlays, branch comparison, scenario lifecycle.                                     |
| Decision Domain     | Alternative packages, approvals, decision record, plan commit.                                              |
| Rules Kernel        | Calendars, capacity equations, priority rules, business constraints and effective-dating.                   |
| Feasibility Engine  | Time-phased capacity/material/manpower/cash constraints and conflict propagation.                           |
| Optimization Engine | Generates feasible candidates and solves configurable objectives.                                           |
| Learning Domain     | Actual-vs-forecast analysis, lesson capture, pattern matching, parameter calibration.                       |
| Integration Gateway | SAP and non-SAP adapters, canonical model mapping, idempotency, retries, monitoring.                        |
| Data Platform       | Transactional relational store, event log, cache, object storage and analytics read models.                 |

## 5.2 Reference codebase structure

/platform

/apps

/web

/api

/planning-worker

/scenario-worker

/integration-worker

/modules

/domain-core

/planning

/scenario

/feasibility

/optimization

/decision

/learning

/integration

/contracts

/openapi

/events

/sap-mappings

/db

/migrations

/seed-reference

/infra

/k8s

/helm

/terraform-or-iac

/tests

/unit /component /integration /e2e /performance /security

/docs

/adr /runbooks /operations

The repository must enforce dependency direction: domain-core cannot depend on SAP adapters, web UI cannot call repositories directly, and optimization/solver adapters depend on a solver-neutral domain contract. Database migrations are forward-only in normal release flow; destructive migrations require a separately approved migration version and rollback plan.

# 6\. Physical / Deployment Architecture

Figure 6-1 — Reference deployment

\[Corporate Users / Plant LAN\]

|

\[Ingress / WAF / Load Balancer\]

|

\[Kubernetes / OpenShift cluster\]

| | |

\[Web\] \[App/API\] \[Planning/Optimization Workers\]

| | |

+-------+--------+

|

\[Kafka / Event Bus\]

|

+-------+---------+-------------------+

| | |

\[PostgreSQL HA\] \[Redis HA\] \[Object Storage\]

|

\[Backup / DR Site\]

SAP S/4HANA On-Premise &lt;--&gt; \[Integration Gateway\] &lt;--&gt; \[Platform\]

External BTP/SAP Integration Suite is optional and may be inserted via Cloud Connector.

## 6.1 Reference node set

| **Layer**                | **Reference deployment**                | **Minimum HA pattern**                 | **Sizing note**                                     |
| ------------------------ | --------------------------------------- | -------------------------------------- | --------------------------------------------------- |
| Ingress                  | 2 reverse-proxy/load-balancer instances | Active/standby or external ADC         | TLS termination and WAF policy.                     |
| Kubernetes control plane | 3 nodes                                 | 3-node quorum                          | Use organization-standard K8s distribution.         |
| Application workers      | 3+ nodes                                | N+1                                    | Horizontal scaling; stateless services.             |
| Planning workers         | 3+ worker pods                          | N+1                                    | CPU-heavy; scale horizontally by optimization jobs. |
| Kafka                    | 3 brokers                               | Quorum                                 | Replication factor 3 for production.                |
| PostgreSQL               | 3 nodes                                 | Primary + 2 replicas                   | Patroni or equivalent HA manager.                   |
| Redis                    | 3 nodes                                 | HA/sentinel or cluster                 | Cache only; never sole source of truth.             |
| Object storage           | 4+ drives/nodes                         | Erasure-coded or enterprise equivalent | Attachments, exports, snapshots.                    |
| Observability            | 3 nodes/pods                            | HA                                     | Metrics, traces, logs and alerts.                   |

**DEPLOYMENT RULE:** The exact hardware size must be calibrated by the performance test suite defined in Section 28. The architecture specifies minimum topology, not unverified production throughput.

# 7\. Technology Stack and Engineering Standards

| **Area**              | **Technology**                                                  | **Rationale**                                                                                             |
| --------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Frontend              | React + TypeScript + Vite + enterprise component library        | Strong data-grid/chart ecosystem, maintainability, RTL support, mobile web.                               |
| Backend               | Java 21 LTS + Spring Boot 4.1.x + Spring Security + Spring Data | Enterprise integration ecosystem, strong typing, SAP-adjacent integration patterns, mature observability. |
| Planning/optimization | Java OR-Tools CP-SAT as default; optional MILP solver adapter   | Deterministic constraint solving; vendor-neutral adapter boundary.                                        |
| Database              | PostgreSQL 17                                                   | Strong transactional semantics, JSONB, partitioning and mature tooling.                                   |
| Event bus             | Apache Kafka-compatible platform                                | Durable asynchronous integration, replay and decoupling.                                                  |
| Cache                 | Redis 7+                                                        | Low-latency cache, distributed locks only with care.                                                      |
| Object storage        | S3-compatible on-prem object store                              | Large attachments, exports, scenario artifacts.                                                           |
| Identity              | OIDC/OAuth2 provider (Keycloak or enterprise IdP)               | Central authentication and federated roles.                                                               |
| Workflow              | BPMN workflow engine (Flowable recommended)                     | Human approvals and long-running business processes.                                                      |
| Observability         | OpenTelemetry + Prometheus + Grafana + Loki/OpenSearch          | Unified metrics/traces/logs.                                                                              |
| Containers            | Kubernetes/OpenShift + Helm                                     | Portable on-prem deployment and controlled scaling.                                                       |
| CI/CD                 | GitLab CI or equivalent + artifact registry + GitOps            | Traceable builds, signed artifacts, environment promotion.                                                |
| API specification     | OpenAPI 3.1                                                     | Machine-readable contracts and code generation.                                                           |
| Schema migration      | Flyway                                                          | Version-controlled DB migration.                                                                          |

## 7.1 Engineering patterns

- Hexagonal architecture inside each domain module.
- Domain commands and events must not depend on controller or database classes.
- All external identifiers are stored alongside internal UUIDs.
- All mutating APIs require idempotency keys.
- Use optimistic concurrency for plan and scenario commits.
- No business logic in database triggers except invariant enforcement that cannot safely exist in application code.
- No distributed transaction across SAP and local database; use outbox/inbox and compensating actions.

# 8\. Information Architecture and Temporal Model

## 8.1 Two temporal universes

PAST / FACT UNIVERSE

\--------------------

Actual execution events

Actual consumption

Actual confirmations

Actual costs

Closed-day machine state

Closed-day inventory state

FUTURE / PLAN UNIVERSE

\---------------------

Expected receipts

Planned operation start/end

Planned allocations

Forecast material consumption

Forecast cost/cash

Scenario assumptions

Future capacity events

## 8.2 Planning day

| **Field**         | **Definition**                                             |
| ----------------- | ---------------------------------------------------------- |
| planning_day_id   | Stable internal identifier.                                |
| business_date     | Calendar date used as planning bucket.                     |
| plant_calendar_id | Working calendar governing capacity availability.          |
| status            | OPEN, FROZEN, CLOSED.                                      |
| actual_cutoff_ts  | Cut-off after which the day is treated as fact-anchored.   |
| plan_version_id   | Baseline plan active for the day.                          |
| closed_by         | User/system identity that closed the day.                  |
| closed_at         | Close timestamp.                                           |
| state_hash        | Deterministic hash of fact state used for reproducibility. |

## 8.3 Temporal rules

1\. Actual events are immutable after the day is closed; a correction creates a compensating event with a link to the original event.

2\. A future plan record may be replaced only by publishing a newer plan version; historical versions remain queryable.

3\. A scenario is evaluated against a specific baseline plan version. If the baseline changes, the scenario becomes STALE and must be rebased.

4\. No scenario may mutate actual facts.

5\. All forecast values carry source, confidence, model version and calculation timestamp.

6\. The system stores both effective_date and recorded_at so historical reconstruction is possible.

# 9\. Core Domain Model

Figure 9-1 — Core conceptual domain

classDiagram

Commitment "1" --> "1..\*" ProductPlan

ProductPlan "1" --> "1..\*" ProductionOrder

ProductionOrder "1" --> "1..\*" OperationPlan

OperationPlan "\*" --> "1" WorkCenter

OperationPlan "\*" --> "0..\*" MaterialDemand

MaterialDemand "\*" --> "1" Material

ProductionOrder "\*" --> "1" Product

Product "1" --> "1..\*" BOMVersion

Product "1" --> "1..\*" RoutingVersion

PlanningDay "1" --> "1..\*" PlanVersion

PlanVersion "1" --> "0..\*" Scenario

Scenario "1" --> "0..\*" ScenarioEvent

Scenario "1" --> "0..\*" ResourceRequirement

Scenario "1" --> "0..\*" DecisionAlternative

Decision "1" --> "1" DecisionAlternative

ActualEvent "\*" --> "1" ProductionOrder

ActualEvent "\*" --> "1" PlanningDay

## 9.1 Aggregate boundaries

| **Aggregate**    | **Root**        | **Owns**                                                | **Consistency boundary**               |
| ---------------- | --------------- | ------------------------------------------------------- | -------------------------------------- |
| Commitment       | Commitment      | Milestones, forecast, risk links                        | Commitment dates/status/priority.      |
| Product Plan     | ProductPlan     | Product-level planned completion and allocation summary | Plan version + product schedule.       |
| Production Order | ProductionOrder | Operations, allocation references, progress projection  | Order status and schedule.             |
| Resource         | Resource        | Calendar, capacity profile, dynamic availability        | Capacity availability by day.          |
| Material         | Material        | Planning parameters and alternative rules               | Material identity and planning policy. |
| Scenario         | Scenario        | Scenario events, computed impacts, candidate plans      | Scenario lifecycle and base version.   |
| Decision         | Decision        | Selected alternative, approval evidence                 | Decision authorization.                |
| Lesson           | Lesson          | Evidence, reusable pattern, calibration link            | Learning rule and applicability.       |

## 9.1 Temporal aggregate rules

| **Aggregate**          | **Immutable facts**                                | **Future plan state**                                             | **Branching rule**                                                       |
| ---------------------- | -------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Production Order       | Created/released/confirmed/cancelled actual events | Future release, priority, dates, resource allocation              | Scenario stores override/event delta; actual events remain global facts  |
| Work Center / Resource | Closed-day availability and actual downtime        | Future capacity calendar, maintenance windows, efficiency factors | Scenario overlays future capacity only                                   |
| Material               | Historical stock/consumption/receipts              | Expected receipts, reservations, projected balance                | Scenario may change future receipts/allocations                          |
| Cash                   | Posted/closed financial facts                      | Forecast cash availability and approved injections                | Scenario may inject or defer future funding assumptions                  |
| Commitment             | Confirmed historical milestone facts               | Forecast completion and due-date risk                             | Scenario may change priority/due-date assumptions according to authority |

**IMPLEMENTATION RULE:** A scenario engine must never clone actual history into mutable rows. It references the immutable actual timeline and overlays only future deltas. This is the technical mechanism that guarantees that Scenario A cannot accidentally change the historical truth shared with Scenario B or the baseline plan.

# 10\. End-to-End Business Processes

| **ID** | **Process**                         | **E2E map**                                                                                               |
| ------ | ----------------------------------- | --------------------------------------------------------------------------------------------------------- |
| P01    | Demand/Commitment to Plan           | Commitment -> product -> production flow -> resource requirements -> baseline plan -> risk forecast       |
| P02    | Engineering to Production Readiness | Engineering revision -> BOM/routing release -> planning snapshot -> order readiness                       |
| P03    | Plan to Produce                     | Planned order/production order -> release -> operation execution -> confirmations -> actual consumption   |
| P04    | Procure to Availability             | Material shortage -> supply action -> purchase/receipt forecast -> stock projection -> production impact  |
| P05    | Machine Availability                | Maintenance/breakdown -> capacity state -> affected operations -> replan -> repair confirmation -> replan |
| P06    | Daily Rolling Planning              | Close actuals -> rebuild future state -> resource forecast -> risks -> alternatives -> commit next plan   |
| P07    | Scenario / What-if                  | Fork baseline -> inject future event(s) -> recalculate -> feasibility -> optimization -> compare          |
| P08    | Management Decision                 | Escalation -> alternatives -> approval -> commit selected plan -> distribute actions                      |
| P09    | Quality Constraint                  | Quality hold -> block operation/product -> propagate impact -> disposition -> resume/replan               |
| P10    | Delivery and After-sales            | Product completion -> delivery -> installed base/service case -> service execution -> lesson evidence     |

## 10.1 BPMN-style daily process

Figure 10-1 — Daily rolling planning BPMN-style flow

START

\-> Ingest actual events

\-> Validate event completeness

\-> Freeze prior day

\-> Build fact-anchored current state

\-> Generate/refresh baseline forecast

\-> Check material/capacity/manpower/cash constraints

\-> If risk found: create risk case

\-> Generate feasible alternatives

\-> If no feasible alternative: RESOURCE_CRISIS

\-> Otherwise optionally optimize

\-> Management approval where threshold requires

\-> Commit next baseline plan

\-> Publish work/resource requirements

\-> Execute

\-> Collect actuals

\-> END OF DAY

\-> repeat

# 11\. Key Operations / Use Cases

| **ID** | **Use case**                      | **Actors**                 | **Pre**                                         | **Post**                                                 | **Main success**                                                                         | **Exceptions**                                                           |
| ------ | --------------------------------- | -------------------------- | ----------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| UC-001 | Close planning day                | Planner                    | Day OPEN; all mandatory actual feeds reconciled | Day CLOSED; actual facts frozen                          | Validate -> freeze -> hash -> publish close -> roll horizon                              | Missing actual feed -> block; reconciliation mismatch -> exception queue |
| UC-002 | Create production order plan item | Planner                    | Material/routing available                      | Planned PO exists in next baseline                       | Enter product/qty/date -> validate -> calculate demand -> allocate provisional resources | No capacity/material -> create risk                                      |
| UC-003 | Register machine breakdown        | Maintenance                | Work center/resource exists                     | Capacity overlay applied to future day(s)                | Enter start/repair estimate -> validate -> create event -> propagate impact              | Conflicting maintenance event -> resolve by version                      |
| UC-004 | Change product priority           | Planner/Manager            | Product plan exists                             | New priority version created; forecast recalculated      | Enter priority -> simulate -> show opportunity cost -> save/commit                       | Permission threshold requires approval                                   |
| UC-005 | Inject financial resource         | Finance                    | Authorized cost center/budget                   | Future cash capacity increases from effective day        | Enter amount/date/purpose -> validate -> scenario/replan                                 | Budget limit exceeded -> reject                                          |
| UC-006 | Forecast material shortage        | Planner/Supply             | BOM/routing + stock/receipts available          | Shortage date and consuming orders identified            | Project daily balance -> identify first negative bucket -> propagate                     | Bad source data -> confidence LOW                                        |
| UC-007 | Create scenario                   | Planner                    | Baseline plan ACTIVE                            | Scenario FORKED                                          | Select baseline -> clone metadata -> assign branch ID                                    | Baseline stale -> block or auto-rebase by policy                         |
| UC-008 | Run scenario simulation           | Planner                    | Scenario DRAFT                                  | Scenario CALCULATED                                      | Apply events -> replan -> feasibility -> impacts -> result                               | Engine timeout -> job remains retryable                                  |
| UC-009 | Optimize scenario                 | Planner/Portfolio Manager  | Scenario has at least one feasible candidate    | Ranked feasible alternatives                             | Select objective -> solve -> produce alternatives                                        | No feasible solution -> RESOURCE_CRISIS                                  |
| UC-010 | Approve alternative               | Manager/Steering Committee | Approval threshold met                          | Decision APPROVED/REJECTED                               | Review evidence -> approve/reject -> audit                                               | Concurrent approval or stale plan -> re-evaluate                         |
| UC-011 | Commit selected plan              | Planner                    | Decision approved; base version unchanged       | New baseline version ACTIVE                              | Validate conflicts -> publish -> emit plan committed event                               | Base version changed -> require rebase                                   |
| UC-012 | Record operation actual           | MES/SAP integration        | Operation exists                                | Actual event stored                                      | Ingest confirmation -> validate -> apply -> recalc future only                           | Duplicate event -> idempotent no-op                                      |
| UC-013 | Capture lesson                    | Planner/Quality            | Closed case with actual outcome                 | Lesson reusable pattern created                          | Compare predicted vs actual -> root cause -> pattern -> publish                          | Insufficient evidence -> draft only                                      |
| UC-014 | Recalculate after SAP delta       | Integration                | New SAP fact received                           | Current plan marked stale; affected scope recalculated   | Ingest -> map -> impact graph -> recompute                                               | Mapping failure -> quarantine                                            |
| UC-015 | Quality hold                      | Quality                    | Product/order identified                        | Affected flow blocked and downstream impact recalculated | Create hold -> block op -> propagate -> disposition                                      | Incorrect scope -> rollback hold event via compensating action           |

# 12\. Dynamic Daily Planning Engine

## 12.1 Engine responsibility

The Daily Planning Engine converts fact-anchored state plus known future events into a deterministic, daily-bucketed future plan. It must be incremental where possible: a localized resource change recalculates only affected products/orders/resources first, followed by a portfolio reconciliation pass when cross-case competition can change.

## 12.2 State transition

Figure 12-1 — Daily planning pseudo-code

For planning day D:

FactState(D) = all immutable actuals through D

FutureEvents(D+1..H) = approved future events

BasePlan(D+1..H) = previous baseline version or new generation

NextPlan = Replan(FactState, FutureEvents, MasterDataSnapshot, RulesVersion)

For each day t in D+1..H:

capacity\[t\] = calendar(t) - maintenance(t) - confirmed_losses(t)

supply\[t\] = on_hand(t-1) + receipts(t) - allocations(t)

demand\[t\] = explosion(BOM, routing, scheduled_operations)

constraints\[t\] = capacity\[t\], supply\[t\], manpower\[t\], cash\[t\], precedence\[t\]

schedule\[t\] = feasible_allocation(constraints\[t\], priorities, commitments)

state\[t\] = state\[t-1\] + receipts - consumption + execution_events

## 12.3 Daily planning algorithm

1\. Load immutable actuals up to planning cut-off.

2\. Load the latest approved baseline version.

3\. Load master-data snapshot and rule-set version effective for the horizon.

4\. Apply future confirmed events: receipts, maintenance, planned capacity, approved commitments and other hard constraints.

5\. Apply flexible decision variables from the baseline plan.

6\. Build remaining production workload from open production orders and operations.

7\. Time-phase material, capacity, manpower and cash requirements.

8\. Run constraint propagation from resource shortage to operation, order, product and commitment.

9\. Generate candidate reallocations or schedule changes within configured search limits.

10\. Calculate a feasible baseline; if infeasible, create a crisis record identifying the blocking set.

11\. Persist a complete plan version with calculation metadata and hashes.

12\. Publish resource requirement and risk read models to the UI.

## 12.4 Incremental recalculation rules

| **Change**                  | **Minimum recalculation scope**                                                 | **Escalation rule**                                              |
| --------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| One machine breakdown       | All operations assigned/eligible to machine; affected products and commitments  | Expand to competing work centers if reallocation occurs.         |
| One material receipt delay  | All future demand lines for material; downstream orders                         | Expand to products/commitments with critical dates.              |
| One product priority change | All resources competing with product; impacted products sharing those resources | Expand to entire portfolio if optimization is enabled.           |
| Cash injection              | Procurement/finance-blocked future actions within horizon                       | Expand if resource release changes machine/material competition. |
| New production order        | Order plus competing resource/material pools                                    | Portfolio reconciliation if it displaces existing work.          |
| Quality hold                | Held item and all dependent/consuming operations                                | Expand through parent product and commitment graph.              |

# 13\. Scenario / What-If Engine

## 13.1 Branching model

BASE PLAN V17

|

+-- Scenario S-A: Priority P01 -> 1

+-- Scenario S-B: CNC-04 unavailable 3 days

+-- Scenario S-C: +20B cash on 2026-10-01

+-- Scenario S-D: Outsource Operation 30

Each scenario stores:

\- base_plan_version_id

\- scenario_event list

\- rule/model version

\- calculated state hash

\- results / impacts

\- resource requirements

\- feasibility status

## 13.2 Scenario event schema

| **Field**               | **Meaning**                        | **Required**     |
| ----------------------- | ---------------------------------- | ---------------- |
| scenario_event_id       | UUID                               | Yes              |
| scenario_id             | Parent scenario                    | Yes              |
| event_type              | Typed business event               | Yes              |
| effective_day           | First affected planning day        | Yes              |
| target_type / target_id | Target aggregate                   | Yes              |
| payload_json            | Typed event payload                | Yes              |
| expected_version        | Optimistic concurrency version     | Yes for mutation |
| confidence              | HIGH/MEDIUM/LOW where forecasted   | No               |
| source                  | USER / SAP / MES / RULE / EXTERNAL | Yes              |
| created_by              | Actor                              | Yes              |
| created_at              | Audit timestamp                    | Yes              |

## 13.3 Scenario result requirements

- Commitment impact by product and due date.
- Resource loading by day.
- Material projected balance and first shortage day.
- Manpower demand and overtime need.
- Cash requirement by day.
- Change in throughput/WIP.
- Opportunity cost on displaced products.
- Assumptions and confidence levels.
- Feasibility state and exact violated constraints.
- Comparison against selected baseline version.

# 14\. Feasibility and Optimization Engine

## 14.1 Feasibility gate

Feasibility is a hard gate, not a score. An alternative is feasible only if all mandatory constraints are satisfied for every day of the scenario horizon. Soft constraints may be violated only when explicitly configured with a penalty and approval policy.

| **Constraint class**  | **Hard/soft**                    | **Example test**                                           |
| --------------------- | -------------------------------- | ---------------------------------------------------------- |
| Material availability | Hard by default                  | Projected available >= required quantity on consuming day. |
| Capacity              | Hard by default                  | Allocated hours <= available hours for work center/day.    |
| Operation precedence  | Hard                             | Start(op2) >= finish(op1) + lead/transfer time.            |
| Calendar              | Hard                             | Operation uses working capacity only.                      |
| Quality block         | Hard                             | Held lot/product cannot be consumed/processed.             |
| Manpower skill        | Hard by default                  | Required skill count available on day.                     |
| Cash                  | Configurable                     | Cumulative cash requirement <= approved available cash.    |
| Delivery due date     | Soft or hard by commitment class | Penalty if commitment class permits slippage.              |
| Strategic priority    | Objective/constraint             | Used through configured priority weight or threshold.      |

## 14.2 Optimization objective model

Objective = w1\*BusinessValue + w2\*OnTimeDelivery + w3\*CashEfficiency

\+ w4\*CapacityStability + w5\*RiskReduction

\- w6\*ResourceInjection - w7\*OpportunityCost - w8\*Penalty

Weights are configuration for the decision context, not embedded business truth.

The engine must output the complete weighted terms so management can see why alternatives differ.

## 14.3 No-solution behavior

If no feasible solution exists within configured search limits, the engine emits RESOURCE_CRISIS. The crisis record must list the minimum blocking constraints, affected commitments, earliest failure date and the classes of intervention capable of changing feasibility (capacity, material, manpower, cash, sequence, outsourcing, or commitment change).

## 14.3 Optimization variable model

The reference formulation is a time-bucketed mixed-integer/linear model. A production implementation may use OR-Tools, Gurobi, CPLEX or another approved solver; the API contract must remain solver-neutral.

Decision variables

\-----------------

x\[o,r,t\] = 1 if operation o is assigned to resource r on day t

y\[o,t\] = executable quantity/hours of operation o on day t

z\[p,t\] = 1 if product/commitment p is completed by day t

i\[r,t\] = injected capacity/resource amount on day t

Core constraints

\----------------

1\. Assignment: sum_r x\[o,r,t\] <= 1

2\. Capacity: sum_o demand\[o,r,t\] <= capacity\[r,t\] + i\[r,t\]

3\. Material balance: opening\[m,t\] + receipts\[m,t\] - demand\[m,t\] >= safety\[m,t\]

4\. Precedence: start\[o+1\] >= finish\[o\] for every routing predecessor

5\. Quantity: cumulative y\[o,t\] <= required_quantity\[o\]

6\. Commitment: completion\[p\] <= due_date\[p\] for on-time target cases

7\. Skill: assigned skill-hours <= available certified skill-hours

8\. Cash: cumulative planned cash use <= available cash + approved injection

9\. Frozen facts: no decision variable may modify closed-day actuals

Minimum-injection objective example

\-----------------------------------

Minimize Sum(i\[r,t\] \* unit_cost\[r,t\])

subject to all hard constraints and configured on-time / quality targets.

Value objective example

\------------------------

Maximize business_value(completions)

\- delay_penalties

\- injection_cost

\- opportunity_cost

The engine may support lexicographic objectives or weighted objectives, but the selected objective, weights and constraint set must be persisted in optimization_run and decision records.

## 14.4 Determinism and solver governance

- Persist solver name, solver version, model version, rule-set version, input state hash and random seed where applicable.
- For regulated/decision-critical runs, require deterministic mode and a maximum acceptable solver gap.
- If the solver terminates early, status must be FEASIBLE_BEST_FOUND, not OPTIMAL.
- Never present a mathematical optimum as a business-optimal decision unless all governed constraints and objective weights are included.
- A solver failure does not imply a feasible plan; return CALCULATION_FAILED and preserve the run evidence.

# 15\. Resource Allocation and Opportunity-Cost Model

## 15.1 Resource types

| **Resource**        | **Examples**                         | **State dimension**          | **Typical constraint** |
| ------------------- | ------------------------------------ | ---------------------------- | ---------------------- |
| Machine/work center | CNC, VPI, winding, assembly/test     | available hours by day       | Capacity               |
| Material            | Copper, insulation, steel, mica tape | quantity by day/lot          | Stock and receipts     |
| Manpower            | Technician, welder, test engineer    | headcount/skill-hours by day | Skill capacity         |
| Cash                | Working capital, procurement budget  | available cash by day        | Funding                |
| Energy              | Power availability                   | hours/energy window by day   | Utility limit          |
| Supplier            | Supplier capacity/ETA                | promise date/quantity        | Lead time              |
| Quality capacity    | Inspection/test capability           | hours/slots by day           | Test bottleneck        |

## 15.2 Opportunity cost

When a scarce resource is allocated to Product A, the engine computes the marginal impact on Products B..N that could otherwise consume the same capacity. Opportunity cost is represented in operational units (days/hours), commercial units where governed data exists, and resource-injection alternatives. It is never hidden inside an aggregate score only.

OpportunityCost(resource R, scenario S) =

Sum(impact_on_displaced_commitments)

\+ Sum(additional_resource_requirements_for_displaced_work)

\+ penalties(configured for displaced commitments)

# 16\. Execution, Actuals and Day-Close Cycle

## 16.1 Execution states

Production Order:

DRAFT -> RELEASED -> PARTIALLY_CONFIRMED -> CONFIRMED -> TECHNICALLY_COMPLETED -> CLOSED

|

+------------------------------> CANCELLED

Planning Day:

OPEN -> FROZEN -> CLOSED

Scenario:

DRAFT -> CALCULATING -> CALCULATED -> APPROVED -> COMMITTED -> ARCHIVED

|

+-> INFEASIBLE / STALE / REJECTED

## 16.2 Day-close algorithm

1\. Stop acceptance of unapproved edits to the closing day.

2\. Reconcile SAP/MES confirmations and material movements received before cut-off.

3\. Persist immutable actual events.

4\. Compute closing KPIs and forecast error seeds.

5\. Generate the next open planning day.

6\. Recalculate baseline future plan from the frozen actual state.

7\. Re-evaluate risks and create/refresh cases.

8\. Notify affected planners/managers.

## 16.3 Daily state-transition pseudocode

function advancePlanningDay(day):

actual = freezeAndLoadActualFacts(day)

baseline = loadOpenPlan(day)

futureInputs = loadEffectiveFutureEvents(day + 1, horizon)

state = deriveEnterpriseState(actual, baseline)

requirements = explodeRequirements(state, BOM, ROUTING)

capacity = projectCapacity(state, futureInputs, calendars, maintenance)

material = projectMaterials(state, requirements, receipts, allocations)

manpower = projectSkills(state, requirements, HRAvailability)

cash = projectCash(state, procurement, approvedInjections)

constraints = buildConstraints(capacity, material, manpower, cash, precedence, commitments)

plan = solveBaselinePlan(state, constraints, rulesVersion, modelVersion)

risks = detectRisks(plan, constraints)

persistPlanVersion(plan, risks)

emitDerivedEvents(plan, risks)

return plan

## 16.4 Same-day vs next-day event policy

| **Event class**                  | **Default effect**         | **Override allowed?** | **Rule**                                                                                                         |
| -------------------------------- | -------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Actual fact                      | Immediate fact update      | No                    | Persist as immutable actual event; impacts next open plan                                                        |
| Machine breakdown reported today | Next open planning day     | Yes                   | Same-day replanning only if configured and unused capacity can be reallocated without violating frozen execution |
| Future priority change           | Effective date specified   | Yes                   | Apply from effective planning day onward                                                                         |
| Future cash injection            | Effective date specified   | Yes                   | Available only from funding effective day                                                                        |
| New production order             | Future start date required | No for closed day     | Cannot create executable historical work                                                                         |

## 16.3 Actual-vs-plan rules

| **Metric**           | **Actual source**                  | **Plan source**                        | **Comparison**               |
| -------------------- | ---------------------------------- | -------------------------------------- | ---------------------------- |
| Operation progress   | Confirmed actuals                  | Planned work quantity/hours            | Completion variance          |
| Material consumption | Goods movements/actual consumption | Time-phased BOM demand                 | Quantity and timing variance |
| Machine time         | Confirmation/MES                   | Routing standard + calendar allocation | Load/efficiency variance     |
| Cost                 | FI/CO or approved actual-cost feed | Planned cost/cash requirement          | Cost variance                |
| Commitment date      | Delivery confirmation              | Forecast completion                    | Date variance                |

# 17\. Decision Governance and Approval Model

## 17.1 Decision authority levels

| **Level** | **Role archetype**                     | **Can do**                                                   | **Approval boundary**                           |
| --------- | -------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------- |
| L1        | Planner / Product Owner                | Create cases, run scenarios, quantify alternatives           | May commit within local threshold if authorized |
| L2        | Functional manager / portfolio manager | Review cross-product impact, select candidate for escalation | Approves functional resource reallocations      |
| L3        | Steering Committee / senior management | Approve high-impact commitment/resource changes              | Final for configured thresholds                 |
| L4        | System administrator                   | Technical config only                                        | No business approval                            |

## 17.2 Decision record

Every approved decision stores: decision_id, case_id, base_plan_version, alternatives considered, feasibility evidence, objective weights, selected alternative, approvers, timestamp, execution owner, expected outcomes and review date. The record is immutable; changes create a new decision version.

# 18\. Lesson Learned and Organizational Learning

Lesson Learned is a first-class operational object. It is generated from forecast-vs-actual evidence and can influence future forecasts through explicit rule links. The MVP does not require opaque machine learning. Reusable patterns may begin as deterministic rules with evidence and confidence.

DEVIATION -> DECISION -> ACTION -> ACTUAL RESULT

|

v

FORECAST ERROR

|

v

LESSON / PATTERN

|

v

CALIBRATION / RULE

|

v

NEXT FORECAST

| **Learning metric**    | **Definition**                                                                   |
| ---------------------- | -------------------------------------------------------------------------------- |
| Forecast Accuracy      | Difference between predicted and actual date/quantity/cost for governed metrics. |
| Recovery Effectiveness | Actual recovery achieved / predicted recovery.                                   |
| Recurrence Rate        | Rate at which equivalent root causes recur after lesson publication.             |
| Lesson Reuse Rate      | Share of relevant new cases where a prior lesson was surfaced/used.              |
| Lesson Influence       | Measured change in plan or forecast attributable to a lesson rule.               |

# 19\. Master Data Management and Governance

| **Entity**           | **Content**                                                   | **Primary system**                         | **Owner**                    |
| -------------------- | ------------------------------------------------------------- | ------------------------------------------ | ---------------------------- |
| Organization         | Plant, planning area, storage location, work center hierarchy | SAP / platform reference                   | Enterprise Architecture / PP |
| Material/Product     | Material, product family, unit, criticality                   | SAP Material Master                        | MM/PP                        |
| BOM                  | BOM versions/items/effectivity                                | SAP BOM                                    | Engineering/PP               |
| Routing              | Routing/operations/work centers/standard values               | SAP task list/routing                      | Engineering/PP               |
| Work center          | Capacity, machine class, eligible alternatives                | SAP Work Center + platform dynamic overlay | Production/Maintenance       |
| Calendar/shift       | Working days, shifts, holidays                                | SAP/calendar + platform planning calendar  | HR/Production                |
| Resource skill       | Skill/certification matrix                                    | HR/competency source                       | HR/Production                |
| Customer/partner     | Business partner/customer                                     | SAP BP                                     | Sales                        |
| Supplier             | Business partner/supplier                                     | SAP BP                                     | Procurement                  |
| Commitment class     | Priority, penalty, due-date criticality                       | Platform configuration                     | Executive governance         |
| Planning rule        | Constraints/objective weights                                 | Platform configuration                     | Planning governance          |
| Confidence class     | HIGH/MEDIUM/LOW meaning                                       | Platform configuration                     | Planning governance          |
| Engineering revision | Revision, validity, release status                            | PLM/DMS/SAP document references            | Engineering                  |

## 19.1 MDM lifecycle

DRAFT -> VALIDATED -> APPROVED -> EFFECTIVE -> SUPERSEDED -> RETIRED

No planning calculation may use RETIRED or unapproved master records.

Every planning calculation stores the effective master-data snapshot/version used.

# 20\. Database Design and Physical Schema

## 20.1 Data architecture

The transactional core uses PostgreSQL. Actual event tables and high-volume telemetry/event tables are append-only and partitioned by business date. Plan and scenario data are normalized enough for transactional correctness, with denormalized read models for dashboards. No analytical workload may block the planning transaction path.

## 20.2 Schemas

| **Schema**  | **Purpose**                                                       |
| ----------- | ----------------------------------------------------------------- |
| core        | Identity-neutral business entities and master references.         |
| planning    | Plan versions, daily buckets, resource allocations and forecasts. |
| scenario    | Branches, events, calculated scenario results.                    |
| execution   | Actual events, confirmations and reconciliation.                  |
| integration | Inbox/outbox, mappings, message logs and quarantine.              |
| learning    | Lessons, patterns, calibration links.                             |
| audit       | Immutable audit entries.                                          |
| readmodel   | Denormalized query projections.                                   |
| config      | Rules, parameters, thresholds, calendars.                         |

## 20.3 Complete application table catalog

| **Table**                      | **Fields (complete application baseline)**                                                                                                                                                                                                                                                                                | **Key indexes**                                                                                                      | **Relationships**                                       |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| core.organization              | organization_id UUID PK; parent_id UUID FK; code VARCHAR(40) UK; name VARCHAR(200); type VARCHAR(40); status VARCHAR(20); source_system VARCHAR(30); source_id VARCHAR(80); valid_from DATE; valid_to DATE NULL; version INT                                                                                              | UK(code); IX(parent_id)                                                                                              | self hierarchy                                          |
| core.plant                     | plant_id UUID PK; organization_id UUID FK; code VARCHAR(20) UK; name VARCHAR(120); timezone VARCHAR(50); calendar_id UUID FK; status VARCHAR(20)                                                                                                                                                                          | UK(code)                                                                                                             | organization, calendar                                  |
| core.material                  | material_id UUID PK; material_no VARCHAR(40) UK; description VARCHAR(250); material_type VARCHAR(40); base_uom VARCHAR(10); criticality VARCHAR(10); planning_policy VARCHAR(30); source_system VARCHAR(30); source_id VARCHAR(80); version INT                                                                           | UK(material_no); IX(criticality)                                                                                     | BOM, stock, demand                                      |
| core.product                   | product_id UUID PK; product_code VARCHAR(60) UK; product_family VARCHAR(60); material_id UUID FK; engineering_rev_id UUID NULL; serial_control BOOLEAN; status VARCHAR(20)                                                                                                                                                | UK(product_code); IX(product_family)                                                                                 | material, revision                                      |
| core.customer                  | customer_id UUID PK; external_bp_no VARCHAR(40) UK; name VARCHAR(250); country_code VARCHAR(3); status VARCHAR(20); source_system VARCHAR(30)                                                                                                                                                                             | UK(external_bp_no)                                                                                                   | commitment                                              |
| core.supplier                  | supplier_id UUID PK; external_bp_no VARCHAR(40) UK; name VARCHAR(250); country_code VARCHAR(3); lead_time_days NUMERIC(8,2); reliability_pct NUMERIC(5,2); status VARCHAR(20)                                                                                                                                             | UK(external_bp_no)                                                                                                   | procurement                                             |
| core.calendar                  | calendar_id UUID PK; code VARCHAR(30) UK; timezone VARCHAR(50); workday_rule VARCHAR(30); version INT; status VARCHAR(20)                                                                                                                                                                                                 | UK(code)                                                                                                             | plant, day                                              |
| core.calendar_day              | calendar_day_id UUID PK; calendar_id UUID FK; business_date DATE; is_working BOOLEAN; capacity_factor NUMERIC(6,3); shift_count INT; version INT                                                                                                                                                                          | UK(calendar_id,business_date)                                                                                        | calendar                                                |
| core.shift                     | shift_id UUID PK; calendar_id UUID FK; code VARCHAR(20); start_time TIME; end_time TIME; capacity_hours NUMERIC(8,2); status VARCHAR(20)                                                                                                                                                                                  | UK(calendar_id,code)                                                                                                 | calendar                                                |
| core.work_center               | work_center_id UUID PK; plant_id UUID FK; code VARCHAR(40) UK; name VARCHAR(160); resource_class VARCHAR(40); bottleneck_flag BOOLEAN; default_capacity_hours NUMERIC(10,2); status VARCHAR(20); source_id VARCHAR(80)                                                                                                    | UK(code); IX(resource_class,bottleneck_flag)                                                                         | operations                                              |
| core.resource                  | resource_id UUID PK; resource_code VARCHAR(60) UK; resource_type VARCHAR(30); name VARCHAR(200); plant_id UUID FK NULL; status VARCHAR(20); source_system VARCHAR(30); source_id VARCHAR(80); version INT                                                                                                                 | UK(resource_code); IX(resource_type,status); IX(plant_id,resource_type)                                              | generic resource aggregate; specialized resource tables |
| core.work_center_eligibility   | eligibility_id UUID PK; work_center_id UUID FK; operation_class VARCHAR(60); product_family VARCHAR(60); efficiency_factor NUMERIC(8,4); valid_from DATE; valid_to DATE NULL                                                                                                                                              | IX(work_center_id,operation_class,valid_from)                                                                        | work_center                                             |
| core.manpower_skill            | skill_id UUID PK; skill_code VARCHAR(40) UK; name VARCHAR(160); certification_required BOOLEAN; valid_from DATE; valid_to DATE NULL                                                                                                                                                                                       | UK(skill_code)                                                                                                       | manpower pool                                           |
| core.resource_person           | person_resource_id UUID PK; external_person_id VARCHAR(60) UK; organization_id UUID FK; status VARCHAR(20)                                                                                                                                                                                                                | UK(external_person_id)                                                                                               | skill mapping                                           |
| core.person_skill              | person_skill_id UUID PK; person_resource_id UUID FK; skill_id UUID FK; proficiency NUMERIC(6,3); valid_to DATE NULL                                                                                                                                                                                                       | UK(person_resource_id,skill_id)                                                                                      | skill                                                   |
| core.bom_header                | bom_id UUID PK; product_id UUID FK; revision VARCHAR(40); status VARCHAR(20); valid_from DATE; valid_to DATE NULL; source_id VARCHAR(80)                                                                                                                                                                                  | UK(product_id,revision)                                                                                              | bom item                                                |
| core.bom_item                  | bom_item_id UUID PK; bom_id UUID FK; component_material_id UUID FK; qty NUMERIC(18,6); uom VARCHAR(10); scrap_pct NUMERIC(8,4); sequence_no INT; required_before_op INT                                                                                                                                                   | IX(bom_id,sequence_no)                                                                                               | BOM/material                                            |
| core.routing                   | routing_id UUID PK; product_id UUID FK; revision VARCHAR(40); status VARCHAR(20); valid_from DATE; valid_to DATE NULL; source_id VARCHAR(80)                                                                                                                                                                              | UK(product_id,revision)                                                                                              | routing ops                                             |
| core.routing_operation         | routing_operation_id UUID PK; routing_id UUID FK; operation_no INT; description VARCHAR(200); standard_hours NUMERIC(12,3); setup_hours NUMERIC(12,3); queue_days NUMERIC(8,3); work_center_id UUID FK; skill_id UUID NULL; sequence_group VARCHAR(30)                                                                    | UK(routing_id,operation_no); IX(work_center_id)                                                                      | routing/workcenter                                      |
| core.engineering_revision      | engineering_rev_id UUID PK; product_id UUID FK; revision_code VARCHAR(40); status VARCHAR(20); effective_from DATE; effective_to DATE NULL; document_uri VARCHAR(1000)                                                                                                                                                    | UK(product_id,revision_code)                                                                                         | product                                                 |
| core.commitment                | commitment_id UUID PK; external_id VARCHAR(80) UK; customer_id UUID FK; product_id UUID FK; qty NUMERIC(18,6); due_date DATE; priority INT; commitment_class VARCHAR(40); commercial_value NUMERIC(20,2); penalty_value NUMERIC(20,2) NULL; status VARCHAR(30)                                                            | UK(external_id); IX(due_date,status); IX(priority)                                                                   | product/customer                                        |
| core.commitment_milestone      | milestone_id UUID PK; commitment_id UUID FK; milestone_type VARCHAR(40); planned_date DATE; actual_date DATE NULL; status VARCHAR(20)                                                                                                                                                                                     | IX(commitment_id,milestone_type)                                                                                     | commitment                                              |
| core.production_order_ref      | production_order_id UUID PK; sap_order_no VARCHAR(40) UK; product_id UUID FK; plant_id UUID FK; qty NUMERIC(18,6); basic_start DATE; basic_finish DATE; system_status VARCHAR(60); source_version VARCHAR(40)                                                                                                             | UK(sap_order_no); IX(product_id,basic_finish)                                                                        | operation, commitment mapping                           |
| core.production_operation_ref  | operation_id UUID PK; production_order_id UUID FK; operation_no INT; work_center_id UUID FK; planned_hours NUMERIC(12,3); confirmed_hours NUMERIC(12,3); status VARCHAR(30); planned_start DATE; planned_finish DATE; confirmation_qty NUMERIC(18,6)                                                                      | UK(production_order_id,operation_no); IX(work_center_id,planned_start)                                               | order/workcenter                                        |
| core.inventory_snapshot        | inventory_snapshot_id UUID PK; material_id UUID FK; plant_id UUID FK; storage_loc VARCHAR(20); snapshot_date DATE; unrestricted_qty NUMERIC(20,6); quality_qty NUMERIC(20,6); blocked_qty NUMERIC(20,6); reserved_qty NUMERIC(20,6)                                                                                       | IX(material_id,snapshot_date); IX(plant_id,snapshot_date)                                                            | material/plant                                          |
| core.supply_receipt            | receipt_id UUID PK; material_id UUID FK; supplier_id UUID FK; source_doc_type VARCHAR(30); source_doc_no VARCHAR(80); expected_date DATE; qty NUMERIC(20,6); confirmed_date DATE NULL; status VARCHAR(20)                                                                                                                 | IX(material_id,expected_date); UK(source_doc_type,source_doc_no)                                                     | material/supplier                                       |
| core.cash_bucket               | cash_bucket_id UUID PK; business_date DATE; currency VARCHAR(3); available_amount NUMERIC(22,2); reserved_amount NUMERIC(22,2); confidence VARCHAR(10); source_system VARCHAR(30)                                                                                                                                         | UK(business_date,currency); IX(business_date)                                                                        | finance planning                                        |
| planning.planning_day          | planning_day_id UUID PK; business_date DATE UK; status VARCHAR(20); actual_cutoff_ts TIMESTAMPTZ; plan_version_id UUID NULL; state_hash VARCHAR(128); closed_at TIMESTAMPTZ NULL                                                                                                                                          | UK(business_date); IX(status,business_date)                                                                          | plan version                                            |
| planning.plan_version          | plan_version_id UUID PK; plan_no VARCHAR(50) UK; planning_day_id UUID FK; base_version_id UUID NULL; version_no INT; status VARCHAR(20); rules_version VARCHAR(40); model_version VARCHAR(40); created_by VARCHAR(80); created_at TIMESTAMPTZ; state_hash VARCHAR(128)                                                    | UK(plan_no); IX(planning_day_id,status)                                                                              | planning day/scenario                                   |
| planning.product_plan          | product_plan_id UUID PK; plan_version_id UUID FK; product_id UUID FK; commitment_id UUID NULL; planned_start DATE; planned_finish DATE; planned_qty NUMERIC(18,6); progress_pct NUMERIC(7,3); risk_status VARCHAR(20)                                                                                                     | IX(plan_version_id,risk_status); IX(product_id,planned_finish)                                                       | product/commitment                                      |
| planning.order_plan            | order_plan_id UUID PK; plan_version_id UUID FK; production_order_id UUID FK; planned_start DATE; planned_finish DATE; priority INT; allocation_status VARCHAR(20); schedule_confidence VARCHAR(10)                                                                                                                        | UK(plan_version_id,production_order_id); IX(plan_version_id,planned_finish); IX(production_order_id,plan_version_id) | order plan                                              |
| planning.operation_plan        | operation_plan_id UUID PK; plan_version_id UUID FK; operation_id UUID FK; work_center_id UUID FK; planned_start DATE; planned_finish DATE; planned_hours NUMERIC(12,3); allocated_hours NUMERIC(12,3); status VARCHAR(20)                                                                                                 | IX(plan_version_id,work_center_id,planned_start); UK(plan_version_id,operation_id)                                   | order/resource                                          |
| planning.order_material_demand | demand_id UUID PK; plan_version_id UUID FK; order_plan_id UUID FK; material_id UUID FK; business_date DATE; required_qty NUMERIC(20,6); allocated_qty NUMERIC(20,6); shortage_qty NUMERIC(20,6); confidence VARCHAR(10)                                                                                                   | IX(plan_version_id,material_id,business_date); IX(order_plan_id,business_date)                                       | order/material/plan                                     |
| planning.resource_allocation   | allocation_id UUID PK; plan_version_id UUID FK; resource_type VARCHAR(30); resource_id UUID; business_date DATE; demand_value NUMERIC(20,6); capacity_value NUMERIC(20,6); allocated_value NUMERIC(20,6); utilization_pct NUMERIC(8,3); confidence VARCHAR(10)                                                            | IX(plan_version_id,resource_type,resource_id,business_date)                                                          | plan/resource                                           |
| planning.material_forecast     | material_forecast_id UUID PK; plan_version_id UUID FK; material_id UUID FK; business_date DATE; opening_qty NUMERIC(20,6); receipts_qty NUMERIC(20,6); demand_qty NUMERIC(20,6); projected_balance NUMERIC(20,6); shortage_flag BOOLEAN; first_shortage_day DATE NULL                                                     | IX(plan_version_id,material_id,business_date); IX(shortage_flag,first_shortage_day)                                  | material/plan                                           |
| planning.commitment_forecast   | commitment_forecast_id UUID PK; plan_version_id UUID FK; commitment_id UUID FK; forecast_date DATE; delay_days INT; on_time BOOLEAN; risk_status VARCHAR(20); root_cause_code VARCHAR(60)                                                                                                                                 | IX(plan_version_id,risk_status); IX(commitment_id,forecast_date)                                                     | commitment/plan                                         |
| planning.risk_case             | risk_case_id UUID PK; case_no VARCHAR(50) UK; plan_version_id UUID FK; entity_type VARCHAR(40); entity_id UUID; severity VARCHAR(20); status VARCHAR(20); root_cause_code VARCHAR(60); first_detected_day DATE; expected_impact_days INT                                                                                  | UK(case_no); IX(status,severity); IX(entity_type,entity_id)                                                          | plan/decision                                           |
| scenario.scenario              | scenario_id UUID PK; scenario_no VARCHAR(50) UK; base_plan_version_id UUID FK; name VARCHAR(200); status VARCHAR(30); owner VARCHAR(80); rules_version VARCHAR(40); model_version VARCHAR(40); created_at TIMESTAMPTZ; calculated_at TIMESTAMPTZ NULL; state_hash VARCHAR(128)                                            | UK(scenario_no); IX(base_plan_version_id,status)                                                                     | scenario events/results                                 |
| scenario.scenario_event        | scenario_event_id UUID PK; scenario_id UUID FK; event_type VARCHAR(50); effective_day DATE; target_type VARCHAR(40); target_id UUID; payload JSONB; expected_version INT NULL; confidence VARCHAR(10); created_by VARCHAR(80); created_at TIMESTAMPTZ                                                                     | IX(scenario_id,effective_day); IX(target_type,target_id)                                                             | scenario                                                |
| scenario.resource_requirement  | requirement_id UUID PK; scenario_id UUID FK; resource_type VARCHAR(30); resource_id UUID NULL; business_date DATE; required_value NUMERIC(20,6); available_value NUMERIC(20,6); gap_value NUMERIC(20,6); injection_type VARCHAR(40); confidence VARCHAR(10)                                                               | IX(scenario_id,resource_type,business_date); IX(gap_value)                                                           | scenario/resource                                       |
| scenario.scenario_impact       | impact_id UUID PK; scenario_id UUID FK; entity_type VARCHAR(40); entity_id UUID; baseline_value NUMERIC(22,6) NULL; scenario_value NUMERIC(22,6) NULL; delta_value NUMERIC(22,6) NULL; delta_days INT NULL; impact_type VARCHAR(40)                                                                                       | IX(scenario_id,entity_type,entity_id)                                                                                | scenario                                                |
| scenario.operation_plan        | scenario_operation_plan_id UUID PK; scenario_id UUID FK; operation_id UUID FK; business_date DATE; work_center_id UUID FK; planned_start DATE; planned_finish DATE; planned_hours NUMERIC(12,3); allocated_hours NUMERIC(12,3); status VARCHAR(20)                                                                        | IX(scenario_id,business_date,work_center_id); UK(scenario_id,operation_id)                                           | scenario/order/resource                                 |
| scenario.material_forecast     | scenario_material_forecast_id UUID PK; scenario_id UUID FK; material_id UUID FK; business_date DATE; opening_qty NUMERIC(20,6); receipts_qty NUMERIC(20,6); demand_qty NUMERIC(20,6); projected_balance NUMERIC(20,6); shortage_qty NUMERIC(20,6); first_shortage_flag BOOLEAN                                            | IX(scenario_id,material_id,business_date); IX(scenario_id,first_shortage_flag,business_date)                         | scenario/material                                       |
| scenario.commitment_forecast   | scenario_commitment_forecast_id UUID PK; scenario_id UUID FK; commitment_id UUID FK; forecast_date DATE; delay_days INT; on_time BOOLEAN; risk_status VARCHAR(20); root_cause_code VARCHAR(60)                                                                                                                            | IX(scenario_id,risk_status); IX(commitment_id,forecast_date)                                                         | scenario/commitment                                     |
| scenario.optimization_run      | optimization_run_id UUID PK; scenario_id UUID FK; objective_profile_code VARCHAR(50); solver VARCHAR(50); status VARCHAR(30); started_at TIMESTAMPTZ; completed_at TIMESTAMPTZ; objective_value NUMERIC(24,8) NULL; solver_gap NUMERIC(12,8) NULL; seed BIGINT NULL                                                       | IX(scenario_id,started_at)                                                                                           | scenario                                                |
| decision.alternative           | alternative_id UUID PK; scenario_id UUID FK; alternative_no VARCHAR(30); rank_no INT NULL; feasibility_status VARCHAR(20); objective_value NUMERIC(24,8) NULL; resource_injection NUMERIC(24,2) NULL; opportunity_cost NUMERIC(24,2) NULL; payload JSONB                                                                  | UK(scenario_id,alternative_no); IX(scenario_id,feasibility_status)                                                   | scenario                                                |
| decision.decision              | decision_id UUID PK; decision_no VARCHAR(50) UK; case_id UUID FK; selected_alternative_id UUID FK; status VARCHAR(20); decision_scope VARCHAR(40); approved_by VARCHAR(80); approved_at TIMESTAMPTZ NULL; expected_review_date DATE NULL; rationale TEXT                                                                  | UK(decision_no); IX(status,approved_at)                                                                              | alternative/risk                                        |
| decision.approval              | approval_id UUID PK; decision_id UUID FK; approver VARCHAR(80); role_code VARCHAR(50); action VARCHAR(20); comment TEXT; acted_at TIMESTAMPTZ                                                                                                                                                                             | IX(decision_id,acted_at)                                                                                             | decision                                                |
| execution.actual_event         | actual_event_id UUID PK; event_type VARCHAR(50); planning_day_id UUID FK; entity_type VARCHAR(40); entity_id UUID; event_time TIMESTAMPTZ; quantity NUMERIC(20,6) NULL; hours NUMERIC(16,3) NULL; amount NUMERIC(24,2) NULL; payload JSONB; source_system VARCHAR(30); source_id VARCHAR(80); immutable_hash VARCHAR(128) | IX(planning_day_id,event_type); IX(entity_type,entity_id,event_time); UK(source_system,source_id,event_type)         | execution                                               |
| execution.reconciliation       | reconciliation_id UUID PK; planning_day_id UUID FK; object_type VARCHAR(40); object_id UUID; planned_value NUMERIC(22,6); actual_value NUMERIC(22,6); variance_value NUMERIC(22,6); status VARCHAR(20); reason_code VARCHAR(60); created_at TIMESTAMPTZ                                                                   | IX(planning_day_id,status); IX(object_type,object_id)                                                                | planning/execution                                      |
| execution.quality_hold         | quality_hold_id UUID PK; entity_type VARCHAR(40); entity_id UUID; reason_code VARCHAR(60); created_on DATE; released_on DATE NULL; status VARCHAR(20); authority VARCHAR(80); notes TEXT                                                                                                                                  | IX(entity_type,entity_id,status)                                                                                     | execution                                               |
| learning.lesson                | lesson_id UUID PK; lesson_no VARCHAR(50) UK; root_cause_code VARCHAR(60); title VARCHAR(250); description TEXT; confidence VARCHAR(10); status VARCHAR(20); created_by VARCHAR(80); created_at TIMESTAMPTZ                                                                                                                | UK(lesson_no); IX(root_cause_code,status)                                                                            | learning                                                |
| learning.lesson_evidence       | lesson_evidence_id UUID PK; lesson_id UUID FK; source_type VARCHAR(40); source_id UUID; metric_code VARCHAR(60); predicted_value NUMERIC(22,6) NULL; actual_value NUMERIC(22,6) NULL; variance_value NUMERIC(22,6) NULL; notes TEXT                                                                                       | IX(lesson_id,metric_code)                                                                                            | lesson                                                  |
| learning.lesson_rule           | lesson_rule_id UUID PK; lesson_id UUID FK; parameter_code VARCHAR(80); old_value NUMERIC(22,8) NULL; new_value NUMERIC(22,8) NULL; effective_from DATE; effective_to DATE NULL; approval_status VARCHAR(20)                                                                                                               | IX(parameter_code,effective_from)                                                                                    | lesson/config                                           |
| integration.inbox_message      | message_id UUID PK; external_message_id VARCHAR(120); source_system VARCHAR(40); message_type VARCHAR(80); received_at TIMESTAMPTZ; payload JSONB; status VARCHAR(20); retry_count INT; last_error TEXT NULL; processed_at TIMESTAMPTZ NULL                                                                               | UK(source_system,external_message_id,message_type); IX(status,received_at)                                           | integration                                             |
| integration.outbox_event       | outbox_id UUID PK; aggregate_type VARCHAR(50); aggregate_id UUID; event_type VARCHAR(80); payload JSONB; created_at TIMESTAMPTZ; published_at TIMESTAMPTZ NULL; status VARCHAR(20); retry_count INT                                                                                                                       | IX(status,created_at); IX(aggregate_type,aggregate_id)                                                               | integration                                             |
| integration.message_mapping    | mapping_id UUID PK; source_system VARCHAR(40); source_object VARCHAR(80); source_key VARCHAR(120); target_type VARCHAR(80); target_id UUID; mapping_status VARCHAR(20); last_seen_at TIMESTAMPTZ                                                                                                                          | UK(source_system,source_object,source_key); IX(target_type,target_id)                                                | integration                                             |
| audit.audit_event              | audit_event_id UUID PK; event_time TIMESTAMPTZ; actor_id VARCHAR(100); action VARCHAR(80); object_type VARCHAR(60); object_id VARCHAR(100); before_hash VARCHAR(128) NULL; after_hash VARCHAR(128) NULL; correlation_id VARCHAR(100); ip_addr INET NULL; details JSONB                                                    | IX(event_time); IX(object_type,object_id); IX(actor_id,event_time)                                                   | audit                                                   |
| config.rule_set                | rule_set_id UUID PK; code VARCHAR(60) UK; version_no INT; status VARCHAR(20); effective_from DATE; effective_to DATE NULL; payload JSONB; approved_by VARCHAR(80) NULL                                                                                                                                                    | UK(code,version_no); IX(code,effective_from)                                                                         | configuration                                           |
| config.threshold               | threshold_id UUID PK; code VARCHAR(80) UK; value_numeric NUMERIC(24,8) NULL; value_text VARCHAR(250) NULL; effective_from DATE; effective_to DATE NULL; scope_json JSONB                                                                                                                                                  | UK(code,effective_from)                                                                                              | configuration                                           |
| readmodel.executive_snapshot   | snapshot_id UUID PK; business_date DATE; generated_at TIMESTAMPTZ; plan_version_id UUID; total_commitments INT; at_risk INT; resource_crises INT; material_shortages INT; decisions_pending INT; payload JSONB                                                                                                            | UK(business_date,plan_version_id)                                                                                    | read model                                              |
| readmodel.resource_heatmap     | heatmap_id UUID PK; plan_version_id UUID; resource_type VARCHAR(30); resource_id UUID; business_date DATE; utilization_pct NUMERIC(8,3); demand_value NUMERIC(20,6); capacity_value NUMERIC(20,6); status VARCHAR(20)                                                                                                     | IX(plan_version_id,resource_type,business_date)                                                                      | read model                                              |
| readmodel.product_timeline     | timeline_id UUID PK; plan_version_id UUID; product_id UUID; business_date DATE; planned_progress NUMERIC(8,3); actual_progress NUMERIC(8,3) NULL; status VARCHAR(20); risk_status VARCHAR(20)                                                                                                                             | IX(plan_version_id,product_id,business_date)                                                                         | read model                                              |

## 20.4 Physical design rules

- Partition execution.actual_event by planning_day_id/business month once volume threshold is crossed.
- Partition audit.audit_event by month or quarter based on measured volume.
- Index all foreign keys used in joins.
- Use covering indexes only for proven read paths.
- Use JSONB for extensible payloads, never for core relational relationships.
- Use UUID for internal IDs and preserve SAP/external IDs in dedicated columns.
- Never hard-delete actual or audit rows.
- Archive closed plan versions after configurable retention while keeping hashes and summary read models online.
- Use VACUUM/ANALYZE automation and monitor bloat.

## 20.5 Canonical data types and mandatory constraints

| **Type**        | **Canonical representation** | **Mandatory constraint**                                                       |
| --------------- | ---------------------------- | ------------------------------------------------------------------------------ |
| Internal ID     | UUID                         | Generated server-side; immutable                                               |
| External SAP ID | VARCHAR(80)                  | Unique within source system + object type                                      |
| Business date   | DATE                         | Always interpreted in plant planning timezone                                  |
| Timestamp       | TIMESTAMPTZ                  | Store offset-aware instant in UTC; render in plant/user timezone               |
| Quantity        | NUMERIC(20,6)                | Non-negative unless movement/event semantics explicitly permit signed quantity |
| Hours           | NUMERIC(16,3)                | Non-negative planned/actual durations                                          |
| Money           | NUMERIC(24,2)                | Currency code required; never mix currencies without explicit conversion       |
| Confidence      | ENUM-like VARCHAR(10)        | HIGH/MEDIUM/LOW only                                                           |
| Status          | VARCHAR(30)                  | Controlled vocabulary per aggregate state machine                              |
| Hash            | VARCHAR(128)                 | SHA-256 or stronger approved digest of canonical serialized evidence           |

All core tables must have created_at/created_by and updated_at/updated_by where the row is mutable. Actual and audit rows additionally require source_system, source_id and immutable_hash. Soft deletion is permitted for master/configuration rows only when required by lifecycle; actual facts are never soft-deleted or rewritten.

# 21\. API Architecture and Contracts

## 21.1 API conventions

- Base path: /api/v1.
- JSON over HTTPS; UTF-8; timestamps ISO-8601 with offset.
- Idempotency-Key required for POST commands.
- ETag / If-Match required for mutable aggregate updates.
- Every response contains request_id/correlation_id.
- Pagination is cursor-based for high-volume lists.
- Errors use RFC 7807 problem+json shape.

## 21.2 Core API catalog

| **Method** | **Path**                         | **Purpose**                          |
| ---------- | -------------------------------- | ------------------------------------ |
| POST       | /planning-days/{date}/close      | Close a planning day                 |
| GET        | /plans/current                   | Current active baseline plan         |
| POST       | /plans/recalculate               | Create/recalculate baseline plan     |
| POST       | /production-orders               | Create planning-side order reference |
| PATCH      | /production-orders/{id}/priority | Change future priority               |
| POST       | /resources/{id}/breakdowns       | Register breakdown event             |
| POST       | /finance/cash-injections         | Create future cash resource event    |
| GET        | /materials/{id}/forecast         | Material time-phased forecast        |
| POST       | /scenarios                       | Create scenario branch               |
| POST       | /scenarios/{id}/events           | Add scenario event                   |
| POST       | /scenarios/{id}/calculate        | Run scenario calculation             |
| GET        | /scenarios/{id}/impacts          | Scenario impacts                     |
| GET        | /scenarios/{id}/resources        | Future resource requirements         |
| POST       | /scenarios/{id}/optimize         | Optimize scenario                    |
| POST       | /scenarios/{id}/commit           | Commit approved scenario             |
| POST       | /decisions                       | Create decision record               |
| POST       | /decisions/{id}/approve          | Approve/reject decision              |
| POST       | /actual-events                   | Ingest actual fact                   |
| GET        | /commitments/{id}/timeline       | Commitment end-to-end trace          |
| GET        | /lessons/similar                 | Find reusable lessons                |
| POST       | /lessons                         | Create lesson                        |

## 21.3 Example — create scenario

POST /api/v1/scenarios

Idempotency-Key: 7d3f...

{

"basePlanVersionId": "7d0d...",

"name": "Prioritize P-017",

"horizon": {"from":"2026-09-22","to":"2026-12-20"},

"initialEvents": \[

{

"type":"PRIORITY_CHANGED",

"effectiveDay":"2026-09-22",

"targetType":"PRODUCT_PLAN",

"targetId":"91af...",

"payload":{"newPriority":1}

}

\]

}

## 21.4 Example — scenario calculation response

{

"scenarioId":"SC-0017",

"status":"CALCULATED",

"feasibility":"FEASIBLE_CONDITIONAL",

"commitmentImpacts":\[...\],

"resourceRequirements":\[...\],

"materialShortages":\[...\],

"opportunityCost":\[...\],

"calculation":{"modelVersion":"PLAN-1.0.0","rulesVersion":"R-2026.09","durationMs":18340}

}

## 21.5 Critical sequence diagrams

### 21.5.1 Machine breakdown -> dynamic replan

sequenceDiagram

actor Maintenance

participant API

participant EventStore

participant Planner

participant Feasibility

participant ReadModel

Maintenance->>API: POST /resources/{id}/breakdowns

API->>EventStore: Persist event + idempotency key

EventStore-->>Planner: RESOURCE_BREAKDOWN

Planner->>Planner: Freeze past; overlay future loss

Planner->>Planner: Recalculate operations/order/product dates

Planner->>Feasibility: Check capacity/material/manpower/cash

Feasibility-->>Planner: Feasible plan / RESOURCE_CRISIS

Planner->>ReadModel: Publish new plan version + impacts

ReadModel-->>API: Updated at-risk commitments

### 21.5.2 Scenario -> optimize -> approve -> commit

sequenceDiagram

actor Planner

participant API

participant Scenario

participant Engine

participant Optimization

participant Decision

participant SAP

Planner->>API: Create scenario from active plan

API->>Scenario: Store branch + future event(s)

Planner->>API: Calculate scenario

API->>Engine: Rebuild future state

Engine->>Optimization: Generate feasible candidates

Optimization-->>Engine: Alternatives + gaps + objective values

Engine-->>Scenario: Persist scenario result

Planner->>Decision: Submit selected candidate

Decision->>Decision: Apply approval threshold / SoD

Decision-->>API: APPROVED

API->>SAP: Commit/write-back approved changes

SAP-->>API: Business object IDs/status

API->>Scenario: Mark COMMITTED and create baseline version

## 21.6 Command contract baseline

POST /api/v1/resources/{resourceId}/breakdowns

{

"effectiveDay": "2026-10-03",

"durationDays": 3,

"reasonCode": "MECH_FAILURE",

"confidence": "HIGH",

"source": "MAINTENANCE"

}

POST /api/v1/production-orders/{id}/priority

{

"effectiveDay": "2026-10-04",

"newPriority": 1,

"reasonCode": "EXECUTIVE_REPRIORITIZATION"

}

POST /api/v1/finance/cash-injections

{

"effectiveDay": "2026-10-05",

"currency": "IRR",

"amount": 20000000000,

"purpose": "MATERIAL_EXPEDITING",

"confidence": "MEDIUM"

}

POST /api/v1/scenarios/{id}/optimize

{

"objective": "MIN_RESOURCE_INJECTION",

"constraints": {

"criticalCommitmentsOnTime": true,

"maxCashInjection": 30000000000,

"maxOvertimeHoursPerDay": 4

}

}

**COMMAND SEMANTICS:** Commands create events or immutable decision records; they do not directly mutate a read model. The domain engine consumes the command, validates authority/effective date/version, persists the event transactionally, and asynchronously or synchronously (by SLA) creates the next plan version.

# 22\. SAP S/4HANA Integration Architecture

## 22.1 Integration principle

The preferred pattern is SAP released APIs for request/response, events/IDocs for asynchronous changes, and RFC only when a released API is not available and an integration architecture exception is approved. SAP Integration Suite/Cloud Integration may be used as the managed integration layer in hybrid deployments; SAP documentation confirms it supports cloud-to-on-premise and hybrid integration, and SAP Cloud Connector can provide controlled on-premise access without opening inbound ports. \[SRC-04\]\[SRC-05\]

## 22.2 Recommended integration matrix

| **Object**              | **Direction**          | **Preferred pattern**                                  | **Fallback**         | **Frequency**                         |
| ----------------------- | ---------------------- | ------------------------------------------------------ | -------------------- | ------------------------------------- |
| Material master         | SAP -> Platform        | Released OData/API                                     | IDoc                 | Initial + delta                       |
| BOM                     | SAP -> Platform        | Released API / IDoc                                    | RFC exception        | Initial + release/delta               |
| Routing/work center     | SAP -> Platform        | Released API                                           | RFC exception        | Initial + delta                       |
| Production orders       | SAP &lt;-&gt; Platform | OData/API + async event                                | IDoc/RFC exception   | Near real-time + batch reconciliation |
| Operation confirmations | SAP/MES -> Platform    | Event/IDoc/API                                         | Batch file           | Near real-time/batch                  |
| Inventory stock         | SAP -> Platform        | API/query + periodic snapshot                          | IDoc                 | Near real-time + daily reconciliation |
| Purchasing/receipts     | SAP -> Platform        | API/event                                              | IDoc                 | Near real-time                        |
| Actual cost             | SAP -> Platform        | API/extract                                            | Batch                | Daily/periodic                        |
| Business partner        | SAP -> Platform        | BP API                                                 | IDoc                 | Initial + delta                       |
| Quality hold            | SAP -> Platform        | Quality API/event                                      | IDoc                 | Near real-time                        |
| Maintenance status      | SAP -> Platform        | PM API/event/MES                                       | IDoc                 | Near real-time                        |
| Plan write-back         | Platform -> SAP        | Released production planning/order API where supported | Approved RFC wrapper | On commit                             |

## 22.2A SAP master/transaction mapping baseline

| **Platform object**                    | **SAP semantic object**                                           | **Ownership**      | **Read/write rule**                                         |
| -------------------------------------- | ----------------------------------------------------------------- | ------------------ | ----------------------------------------------------------- |
| Material                               | Material Master / relevant released material API                  | SAP MM             | SAP -> Platform; platform never authors SAP material master |
| Business Partner / Customer / Supplier | Business Partner                                                  | SAP                | SAP -> Platform                                             |
| BOM                                    | BOM / production or engineering BOM according to configured use   | SAP PP/Engineering | SAP -> Platform; planning snapshot is versioned             |
| Routing / Operation                    | Task list / routing / operation                                   | SAP PP             | SAP -> Platform                                             |
| Work Center / Capacity                 | Work center + capacity/shift/calendar data                        | SAP PP/CRP         | SAP -> Platform; dynamic outage overlay is platform-owned   |
| Production Order                       | Production order header / item / operations                       | SAP PP             | Bidirectional only through approved business APIs/events    |
| Confirmation                           | Operation confirmation / final confirmation                       | SAP PP or MES      | SAP/MES -> Platform as actual fact                          |
| Inventory / MRP elements               | Stock and relevant receipts/reservations                          | SAP MM/PP          | SAP -> Platform                                             |
| Purchase receipt                       | Purchase order/schedule line/goods receipt                        | SAP MM             | SAP -> Platform                                             |
| Quality hold                           | Inspection lot / quality notification/status where applicable     | SAP QM             | SAP -> Platform                                             |
| Maintenance state                      | Equipment / maintenance order / breakdown status where applicable | SAP PM             | SAP -> Platform                                             |
| Actual cost                            | CO/FI actual postings relevant to governed objects                | SAP FI/CO          | SAP -> Platform; never rewritten by platform                |
| Document/revision                      | Document info/DMS/engineering revision reference where used       | SAP DMS/PLM        | SAP -> Platform                                             |

**API RELEASE RULE:** The exact SAP service or event name is release/configuration dependent. The integration team must select the released interface from SAP Business Accelerator Hub for the target S/4HANA release and record that concrete endpoint, version, authorization object and payload mapping in the integration repository before build. The architecture does not authorize direct table/DB access merely because a field is visible in SAP.

## 22.3 Integration reliability pattern

SAP -> Adapter -> Inbox(idempotent) -> Canonical Event -> Domain Handler -> Outbox -> Read Models

Failures:

1\. Schema validation failure -> QUARANTINE

2\. Temporary network failure -> RETRY with exponential backoff

3\. Duplicate -> ACK/no-op

4\. Business validation failure -> REJECTED with remediation code

5\. Persistent failure -> DEAD LETTER + alert

Never: distributed 2-phase commit between SAP and platform.

## 22.4 Security

- TLS 1.2+; prefer TLS 1.3 where supported.
- mTLS for system-to-system channels where supported.
- OAuth2/client credentials or SAP-supported technical user mechanism for APIs.
- Use SAP Cloud Connector for hybrid connectivity where applicable; no direct inbound exposure of SAP internal ports.
- Principal propagation only where end-user traceability is explicitly required and supported.
- Store certificates/secrets in enterprise vault, not Git or container images.

# 23\. Security Architecture and Threat Model

## 23.1 Trust zones

| **Zone**          | **Assets**                  | **Control**                                              |
| ----------------- | --------------------------- | -------------------------------------------------------- |
| User zone         | Browsers/workstations       | SSO, MFA where corporate IdP supports, endpoint security |
| Presentation zone | Ingress/WAF                 | TLS, rate limiting, WAF, headers, bot controls           |
| Application zone  | APIs/planning workers       | Service identities, mTLS, least privilege                |
| Data zone         | DB/Kafka/Redis/object store | Network isolation, encryption, backup                    |
| Integration zone  | SAP adapters                | Allow-listed routes, connector, certificate auth         |
| Admin zone        | Ops tools                   | Privileged access, session recording where required      |

## 23.2 STRIDE controls

| **Threat**             | **Example**                         | **Control**                                         |
| ---------------------- | ----------------------------------- | --------------------------------------------------- |
| Spoofing               | Fake user/service identity          | OIDC, mTLS, short-lived tokens                      |
| Tampering              | Plan or scenario altered            | RBAC/ABAC, optimistic concurrency, audit hashes     |
| Repudiation            | Decision denied later               | Immutable audit, approval evidence, correlation IDs |
| Information disclosure | Plan/costs exposed                  | Row-level authorization, TLS, encryption at rest    |
| Denial of service      | Calculation flood                   | Rate limits, job quotas, circuit breakers           |
| Elevation              | Planner performs executive approval | SoD roles and approval thresholds                   |

## 23.3 Authorization model

Use RBAC for coarse roles and ABAC for plant/organization/product-family scope. A user must satisfy both capability and scope. Example permission: DECISION_APPROVE plus scope=PLANT:PL01 and threshold <= configured monetary limit. Executive decisions require a separate role and cannot be approved by the initiating user.

# 24\. Logging, Monitoring and Observability

| **Signal**           | **Must capture**                                                                   | **Retention target**               |
| -------------------- | ---------------------------------------------------------------------------------- | ---------------------------------- |
| Application logs     | timestamp, level, service, request_id, correlation_id, actor, error code, duration | 90 days online; archive per policy |
| Audit log            | who/what/when/object/before-after hashes/decision evidence                         | 7 years target, configurable       |
| Metrics              | API latency, job duration, plan calc time, Kafka lag, DB health, resource usage    | 13 months summarized               |
| Traces               | cross-service trace/span IDs                                                       | 30 days                            |
| Integration messages | message IDs, source, type, status, retry count                                     | 1 year or business retention       |
| Planning engine      | input version, output hash, runtime, solver status, gap                            | 7 years for decision-critical runs |

## 24.1 Critical alerts

- Planning calculation failure or timeout beyond SLA.
- Stale SAP/MES feed beyond configured freshness threshold.
- Duplicate or high-volume integration failures.
- Resource crisis for critical commitment class.
- Database replication lag or failover.
- Optimization solver gap above configured threshold.
- Unauthorized approval attempt.
- Audit-log write failure.

# 25\. Availability, Disaster Recovery and Business Continuity

| **Requirement**          | **Target**                | **Design**                                            |
| ------------------------ | ------------------------- | ----------------------------------------------------- |
| Application availability | 99.9% monthly             | N+1 app pods/nodes; rolling deploys                   |
| Planning data RPO        | <= 15 minutes             | Synchronous DB replica where feasible + WAL archiving |
| Planning data RTO        | <= 2 hours                | Automated restore/runbook + standby DB                |
| Message durability       | No lost committed events  | Kafka replication + persistent DB inbox/outbox        |
| Site failure             | Restore at secondary site | Replicated backups and IaC rebuild                    |
| Backup test              | Quarterly                 | Automated restore verification                        |

## 25.1 Business continuity modes

- Normal mode: SAP/MES feeds plus dynamic planning.
- Degraded mode: last-known facts plus manual event entry; integration freshness clearly shown.
- Offline contingency: read-only last-known plan export plus controlled manual planning worksheet; no false claim of real-time synchronization.
- Recovery mode: replay integration inbox from last durable point and regenerate plan version.

# 26\. DevOps, CI/CD and Release Management

git

|

+--> build -> unit test -> static analysis -> dependency scan -> container build

|

+--> contract test -> integration test -> performance smoke

|

+--> sign artifact -> registry

|

+--> deploy DEV -> TEST -> UAT -> PROD

Database: Flyway expand/contract migrations.

Config: versioned, environment-specific secrets externalized.

Deployment: Helm + GitOps promotion.

## 26.1 Branching

| **Branch**      | **Purpose**                        |
| --------------- | ---------------------------------- |
| main            | Release-ready code.                |
| feature/\*      | Short-lived development.           |
| release/\*      | UAT stabilization.                 |
| hotfix/\*       | Production fixes.                  |
| architecture/\* | ADR/reference implementation work. |

## 26.2 Quality gates

- Unit coverage target >= 80% for domain/rule code.
- 100% contract coverage for SAP canonical messages.
- No critical/high known security vulnerabilities at release.
- Database migration forward and rollback/forward-compatibility test passed.
- Performance benchmark meets Section 28 target.
- Audit and authorization tests pass.

# 27\. Data Migration and Cutover

## 27.1 Migration stages

1\. Inventory source systems and data ownership.

2\. Extract SAP masters and historical transactional facts using approved APIs/extracts.

3\. Load staging tables without modifying target facts.

4\. Normalize keys and units of measure.

5\. Run referential and business-rule quality checks.

6\. Load master snapshot and historical fact events.

7\. Reconcile against SAP counts/totals.

8\. Dry-run plan calculation from migrated facts.

9\. Business sign-off.

10\. Cutover: freeze, final delta, reconcile, activate platform baseline.

## 27.2 Data quality gates

| **Check**               | **Blocking?**            | **Example**                                         |
| ----------------------- | ------------------------ | --------------------------------------------------- |
| Material key uniqueness | Yes                      | No duplicate material_no.                           |
| BOM completeness        | Yes for planned products | All required components resolve.                    |
| Routing completeness    | Yes for planned products | Every required operation maps to eligible capacity. |
| Calendar coverage       | Yes                      | Every horizon day has a calendar state.             |
| Stock reconciliation    | Yes                      | Snapshot matches source within approved tolerance.  |
| Production order status | Yes                      | Open orders mapped to known products.               |

# 28\. Testing Strategy and Test Cases

## 28.1 Test levels

- Unit: domain rules, equations, state transitions.
- Component: database repositories, engine modules.
- Contract: API and SAP message schemas.
- Integration: SAP/inbound/outbound/idempotency.
- Scenario: branch isolation and deterministic results.
- Performance: baseline planning and optimization throughput.
- Security: authentication, authorization, injection, secrets, audit.
- Recovery: failover, replay, restore, data consistency.
- UAT: business scenarios and decision workflows.

## 28.2 Functional test catalog

| **ID** | **Test**                    | **Expected result**                                                             |
| ------ | --------------------------- | ------------------------------------------------------------------------------- |
| FT-001 | Close day freezes actuals   | Actual event after close cannot modify closed day; compensating event required. |
| FT-002 | Create production order     | Valid product/routing creates plan item and demand.                             |
| FT-003 | Invalid product             | Order rejected with PRODUCT_NOT_PLANNABLE.                                      |
| FT-004 | Machine breakdown           | Future capacity reduced and impacted work recalculated.                         |
| FT-005 | Repair event                | Capacity restored from repair day onward.                                       |
| FT-006 | Material shortage forecast  | First negative balance day identified correctly.                                |
| FT-007 | Priority change             | Portfolio impact and opportunity cost visible.                                  |
| FT-008 | Cash injection              | Procurement-blocked demand becomes feasible only from effective day.            |
| FT-009 | Scenario fork isolation     | Scenario changes do not alter baseline.                                         |
| FT-010 | Scenario compare            | Deltas match independent recalculation.                                         |
| FT-011 | Feasibility hard constraint | Plan exceeding machine capacity marked infeasible.                              |
| FT-012 | Soft delivery constraint    | Late commitment receives penalty when allowed.                                  |
| FT-013 | RESOURCE_CRISIS             | No feasible plan yields crisis record.                                          |
| FT-014 | Optimization determinism    | Same input/model returns same result within defined solver tolerance.           |
| FT-015 | Stale scenario              | Base plan change marks scenario stale.                                          |
| FT-016 | Commit scenario             | Approved scenario publishes new baseline.                                       |
| FT-017 | Concurrent commit           | Second commit rejected due to version conflict.                                 |
| FT-018 | Actual confirmation         | Future plan after actual day recalculates without changing actual.              |
| FT-019 | Quality hold                | Downstream production blocked.                                                  |
| FT-020 | Lesson generation           | Forecast-vs-actual creates evidence and lesson draft.                           |
| FT-021 | Lesson rule approval        | Calibration change requires authorized approval.                                |
| FT-022 | Duplicate integration       | Duplicate SAP message is idempotent.                                            |
| FT-023 | Integration quarantine      | Schema-invalid message isolated.                                                |
| FT-024 | Permission boundary         | Planner cannot approve executive decision.                                      |
| FT-025 | Audit completeness          | Every business mutation creates audit trail.                                    |

## 28.3 Performance tests

| **PT** | **Scenario**           | **Target**                                                                                      |
| ------ | ---------------------- | ----------------------------------------------------------------------------------------------- |
| PT-001 | Current plan dashboard | p95 <= 2 s for cached/read-model queries.                                                       |
| PT-002 | Incremental replan     | <= 30 s for reference test dataset.                                                             |
| PT-003 | Full 90-day baseline   | <= 180 s for reference test dataset.                                                            |
| PT-004 | Scenario branch        | <= 180 s for reference test dataset.                                                            |
| PT-005 | Concurrent users       | 500 authenticated users with no error rate > 1% during test.                                    |
| PT-006 | Event ingestion        | Sustain at least 100 events/s in benchmark environment with p95 < 1 s ingestion acknowledgment. |

## 28.4 Security tests

- Expired token rejected.
- Wrong role denied.
- Cross-plant data denied.
- SQL/NoSQL injection payloads rejected/sanitized.
- SSRF and file upload controls tested.
- Sensitive data not present in logs.
- Audit events cannot be edited by business roles.
- Secret rotation without application code change.

# 29\. Verification, Validation and UAT

## 29.1 Major feature acceptance criteria

| **Feature**           | **Acceptance criterion**                                                                                                                           |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Daily planning        | Given frozen actuals and governed master snapshot, the engine produces a reproducible day-by-day future plan with documented resource constraints. |
| Scenario engine       | A scenario can be forked, changed, calculated, compared and discarded without altering the baseline.                                               |
| Material forecast     | The system identifies first shortage date and affected orders with traceable demand lines.                                                         |
| Resource feasibility  | Every selected alternative has a machine/material/manpower/cash feasibility explanation.                                                           |
| Optimization          | The engine produces one or more feasible alternatives and exposes objective terms and opportunity cost.                                            |
| Commitment trace      | A user can trace commitment -> product -> PO -> operation -> resource -> event -> impact.                                                          |
| Actual reconciliation | Closed-day actuals remain immutable and future plan is recalculated from them.                                                                     |
| Learning              | Forecast errors become reusable lessons and can alter configured parameters after approval.                                                        |
| SAP integration       | Source identifiers, message status, retries and reconciliation are fully auditable.                                                                |

## 29.2 UAT scenarios tailored to PARS business context

| **ID** | **Business scenario**                | **UAT goal**                                                                                       |
| ------ | ------------------------------------ | -------------------------------------------------------------------------------------------------- |
| UAT-01 | Thermal generator commitment at risk | Simulate machine capacity loss; show impact through production flow and delivery.                  |
| UAT-02 | Hydro generator long-lead material   | Delay a critical imported material; forecast shortage and compare procurement vs sequence options. |
| UAT-03 | Busduct production conflict          | Create new order competing for shared capacity; quantify impact on existing commitments.           |
| UAT-04 | Wind product priority change         | Raise wind product priority; show cross-product opportunity cost.                                  |
| UAT-05 | Industrial/traction motor demand     | Add production order and validate material/capacity time-phased loading.                           |
| UAT-06 | Cash injection                       | Inject funding; validate that only blocked procurement paths from the effective date are released. |
| UAT-07 | Quality hold                         | Block a component; propagate downstream effect; release hold and replan.                           |
| UAT-08 | Daily actualization                  | Post actual confirmations and consumption; close day; validate new tomorrow baseline.              |
| UAT-09 | Decision committee                   | Compare alternatives; approve one; publish actions and record audit.                               |
| UAT-10 | Lesson reuse                         | Create lesson from an actual breakdown and surface it on a similar future risk.                    |

# 30\. UI/UX Information Architecture

## 30.1 Primary screens

| **Screen**              | **Purpose**                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------- |
| Executive Control Tower | At-risk commitments, resource crises, decisions required, trend and drill-down.             |
| Planning Workspace      | Daily timeline, products, production orders, operations, resource load and replan controls. |
| Scenario Lab            | Create branch, inject events, calculate, compare, optimize, inspect resource requirements.  |
| Resource Board          | Machine/material/manpower/cash by day; bottlenecks and conflicts.                           |
| Material Risk           | Projected balance, first shortage date, consuming orders, supply actions.                   |
| Commitment Trace        | Commitment -> product -> order -> operation -> resource -> event.                           |
| Decision Workbench      | Alternatives, feasibility, objective terms, opportunity cost, approvals.                    |
| Execution & Actuals     | Confirmations, actual cost, consumption and reconciliation.                                 |
| Lessons                 | Past cases, reusable patterns, calibration impact.                                          |
| Integration Monitor     | SAP messages, stale feeds, errors, quarantine, replay.                                      |
| Administration          | Rules, thresholds, calendars, roles and configuration versions.                             |

## 30.2 UX rules

- Progressive disclosure: executives see impact first; planners see causal detail on drill-down.
- Every red/amber status must be clickable to the underlying evidence.
- Past and future must have visually distinct states.
- Scenario changes must show BEFORE vs AFTER.
- Every scenario result must show the effective date of each assumption.
- Use Persian RTL and English localization from the same UI model; no hard-coded labels.
- No KPI without source timestamp and data freshness indicator.

# 31\. Configuration, Rules and Reference Data

## 31.1 Configurable rule families

| **Rule family**  | **Examples**                                              | **Versioned?** | **Approval**           |
| ---------------- | --------------------------------------------------------- | -------------- | ---------------------- |
| Priority         | Priority 1..N; escalation threshold                       | Yes            | Planning governance    |
| Commitment class | Hard/soft due date, penalty policy                        | Yes            | Executive governance   |
| Capacity         | Calendar, efficiency, downtime policy                     | Yes            | Production/Maintenance |
| Material         | Safety stock, alternative material policy, shortage class | Yes            | Supply/Engineering     |
| Manpower         | Skills, overtime limits                                   | Yes            | HR/Production          |
| Cash             | Budget and approval threshold                             | Yes            | Finance                |
| Optimization     | Objective weights, solver limits                          | Yes            | Planning governance    |
| Confidence       | Meaning and usage of HIGH/MEDIUM/LOW                      | Yes            | Planning governance    |
| Learning         | Calibration rules and evidence thresholds                 | Yes            | Planning governance    |

# 32\. Implementation Plan and Work Breakdown

## 32.1 Delivery waves

| **Wave** | **Theme**                | **Deliverables**                                                                              |
| -------- | ------------------------ | --------------------------------------------------------------------------------------------- |
| Wave 0   | Foundation               | Identity, platform, DB, CI/CD, observability, canonical model, SAP connectivity.              |
| Wave 1   | Fact and baseline        | Master sync, production orders, operations, daily state, baseline plan, executive read model. |
| Wave 2   | Dynamic events           | Breakdown, material receipt/shortage, priority change, cash injection, replan engine.         |
| Wave 3   | Scenario lab             | Branching, scenario calculation, resource requirements, comparison.                           |
| Wave 4   | Feasibility/optimization | Hard constraints, optimization adapter, opportunity cost, resource crisis.                    |
| Wave 5   | Decision and execution   | Approvals, plan commit, SAP write-back, actual reconciliation.                                |
| Wave 6   | Learning                 | Lessons, pattern matching, calibration and accuracy metrics.                                  |
| Wave 7   | Industrialization        | Performance hardening, DR, security hardening, UAT, cutover.                                  |

## 32.2 Team structure

| **Team**              | **Primary skills**                                    | **Ownership**               |
| --------------------- | ----------------------------------------------------- | --------------------------- |
| Architecture          | Enterprise, solution, SAP, security                   | Architecture baseline, ADRs |
| Backend               | Java/Spring, domain design                            | Core services, APIs         |
| Planning/Optimization | Operations research, scheduling, Java/Python          | Planning and solver         |
| Frontend              | React/TS, data visualization, RTL                     | UI                          |
| SAP Integration       | ABAP/OData/IDoc/Cloud Integration                     | Adapters/mappings           |
| Data                  | PostgreSQL, data quality                              | Schema, migration           |
| QA                    | Automation, performance, security                     | All quality gates           |
| DevOps/SRE            | K8s, CI/CD, observability, backup                     | Platform                    |
| Business SMEs         | PP, production, supply, finance, maintenance, quality | Rules/UAT                   |

# 33\. Risks, Constraints, Assumptions and Mitigations

| **ID** | **Risk**                                             | **Severity** | **Mitigation**                                                      |
| ------ | ---------------------------------------------------- | ------------ | ------------------------------------------------------------------- |
| R01    | Internal SAP APIs/configuration differ from expected | High         | API discovery pack + release-specific contract test before build.   |
| R02    | Poor master-data quality                             | High         | Data-quality gate and quarantine; no planning on unresolved master. |
| R03    | Planner distrust of optimization                     | High         | Explainable alternatives; show constraints and objective terms.     |
| R04    | Solver runtime too high                              | Medium       | Incremental replan, decomposition, time limits, warm starts.        |
| R05    | Conflicting calendars across sources                 | Medium       | Single planning calendar authority + reconciliation.                |
| R06    | Overuse of scenarios creates stale branches          | Medium       | Automatic stale detection and rebase workflow.                      |
| R07    | Integration outage                                   | High         | Last-known-state mode, freshness indicators, replayable inbox.      |
| R08    | False precision in forecast                          | High         | Confidence labels and evidence requirements.                        |
| R09    | Direct SAP write-back causes mismatch                | High         | Commit protocol + idempotent commands + reconciliation.             |
| R10    | AI recommendations bypass governance                 | High         | AI is advisory; typed APIs + approvals mandatory.                   |
| R11    | Production data volume grows unexpectedly            | Medium       | Partitioning, archive strategy, benchmark thresholds.               |
| R12    | Business rules are changed informally                | High         | Versioned config + approval + effective dating.                     |

## 33.1 Assumptions

- SAP remains authoritative for SAP-owned master/transactional facts.
- Production planning can be represented in one-day buckets for the initial product.
- Internal users can identify ownership for machine, material, manpower and cash data.
- Management approval thresholds can be expressed numerically and versioned.
- Internal interfaces needed for MES/SCADA/Primavera can be supplied as governed contracts.

# 34\. Architecture Decision Records

| **ADR** | **Decision**              | **Rationale**                                                                                                                                                       |
| ------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ADR-001 | Daily planning bucket     | Use one working day as minimum planning quantum. Enables operational planning without sub-day simulation complexity; matches user-defined minimum effect principle. |
| ADR-002 | Temporal immutability     | Closed-day facts are immutable; corrections are compensating events. Preserves auditability and forecast-vs-actual learning.                                        |
| ADR-003 | Scenario branch model     | Scenario stores deltas against a baseline plan version. Avoids duplicated datasets and keeps comparisons explainable.                                               |
| ADR-004 | Modular monolith first    | Deploy one application boundary with internal modules before extracting services. Reduces distributed-system complexity while preserving bounded contexts.          |
| ADR-005 | On-premise first          | Core planning and data remain operational without internet. Supports plant continuity and local control.                                                            |
| ADR-006 | SAP integration boundary  | No direct SAP DB access; use released APIs/events/IDocs and approved RFC exceptions. Protects upgradeability and integrity.                                         |
| ADR-007 | Feasibility gate          | No infeasible alternative reaches final selection. Separates technical possibility from management preference.                                                      |
| ADR-008 | Explainable optimization  | Store objective terms, constraints, solver metadata and alternative deltas. Builds planner trust and enables audit.                                                 |
| ADR-009 | AI boundary               | AI cannot directly mutate baseline or SAP. Prevents uncontrolled automation in mission-critical planning.                                                           |
| ADR-010 | Learning as configuration | Initial lessons influence rules via explicit approved calibration links. Provides controlled learning before opaque ML.                                             |

# 35\. Glossary and Abbreviations

| **Term**        | **Definition**                                                                                                                   |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Actual          | Immutable execution fact for a closed planning day.                                                                              |
| BOM             | Bill of Material.                                                                                                                |
| BTP             | SAP Business Technology Platform.                                                                                                |
| CNF             | Complete/final confirmation terminology used in SAP production execution contexts; exact semantics depend on configured process. |
| CPI             | SAP Cloud Integration / historical naming context; current SAP product naming is Integration Suite Cloud Integration.            |
| ERP             | Enterprise Resource Planning.                                                                                                    |
| FEASIBLE        | All hard constraints satisfied for the plan horizon.                                                                             |
| MES             | Manufacturing Execution System.                                                                                                  |
| MRP             | Material Requirements Planning.                                                                                                  |
| PARS            | MAPNA Generator Engineering and Manufacturing Company.                                                                           |
| PCNF            | Partial confirmation terminology used in SAP production execution contexts.                                                      |
| PLAN VERSION    | Immutable published future plan snapshot.                                                                                        |
| SCENARIO        | Branch from a specific plan version with future overrides.                                                                       |
| RESOURCE CRISIS | No feasible plan under current constraints and search rules.                                                                     |
| S/4HANA         | SAP ERP platform referenced by this architecture.                                                                                |
| STATE HASH      | Deterministic fingerprint of calculation inputs/results.                                                                         |
| TECO            | Technical completion status in SAP; exact settlement/accounting behavior must follow SAP configuration.                          |
| WIP             | Work in Process.                                                                                                                 |
| What-if         | Controlled future branch in which one or more decision variables are changed.                                                    |

# Appendix A. Canonical Event Catalog

| **Event**                         | **Time class**        | **Target**       | **Effect**                                       |
| --------------------------------- | --------------------- | ---------------- | ------------------------------------------------ |
| PRODUCTION_ORDER_CREATED          | Future                | production_order | Creates future workload.                         |
| PRODUCTION_ORDER_PRIORITY_CHANGED | Future                | production_order | Changes competition priority from effective day. |
| MACHINE_BREAKDOWN                 | Future/Actual trigger | work_center      | Removes capacity from effective day.             |
| MACHINE_REPAIRED                  | Future                | work_center      | Restores capacity from effective day.            |
| MATERIAL_RECEIPT_CONFIRMED        | Future/Actual         | material         | Adds supply to daily stock projection.           |
| MATERIAL_RECEIPT_DELAYED          | Future                | material receipt | Shifts supply date.                              |
| MATERIAL_SHORTAGE_DETECTED        | Derived               | material         | Raised by forecast engine.                       |
| CASH_INJECTED                     | Future                | cash bucket      | Adds future available cash.                      |
| QUALITY_HOLD_CREATED              | Future/Actual         | product/order    | Blocks affected operation path.                  |
| QUALITY_HOLD_RELEASED             | Future                | product/order    | Removes block.                                   |
| COMMITMENT_PRIORITY_CHANGED       | Future                | commitment       | Changes objective weight/priority.               |
| COMMITMENT_DUE_DATE_CHANGED       | Future                | commitment       | Changes hard/soft deadline.                      |
| MANPOWER_CAPACITY_CHANGED         | Future                | skill/resource   | Changes skill capacity.                          |
| PLAN_RECALCULATED                 | Derived               | plan             | New plan version generated.                      |
| SCENARIO_CREATED                  | Command               | scenario         | Creates branch.                                  |
| SCENARIO_CALCULATED               | Derived               | scenario         | Scenario result stored.                          |
| DECISION_APPROVED                 | Command               | decision         | Authorizes alternative.                          |
| PLAN_COMMITTED                    | Command               | plan             | Publishes selected plan.                         |
| ACTUAL_OPERATION_CONFIRMED        | Actual                | operation        | Immutable execution fact.                        |
| ACTUAL_MATERIAL_CONSUMED          | Actual                | material/order   | Immutable consumption fact.                      |
| ACTUAL_COST_POSTED                | Actual                | cost object      | Immutable financial fact.                        |
| LESSON_PUBLISHED                  | Derived               | lesson           | Makes lesson reusable.                           |

# Appendix B. API Error Catalog

| **Code** | **Error**              | **Meaning**                                          | **Resolution**                                        |
| -------- | ---------------------- | ---------------------------------------------------- | ----------------------------------------------------- |
| PLN-001  | PLAN_STALE             | Base plan changed since scenario was created.        | Rebase and recalculate.                               |
| PLN-002  | NO_FEASIBLE_PLAN       | All candidates violate at least one hard constraint. | Review RESOURCE_CRISIS interventions.                 |
| PLN-003  | RULE_VERSION_MISSING   | No effective rule set for planning date.             | Activate approved rule version.                       |
| PLN-004  | MASTER_DATA_INCOMPLETE | Required material/BOM/routing/calendar missing.      | Correct MDM data.                                     |
| INT-001  | DUPLICATE_MESSAGE      | Same source message already processed.               | No action; idempotent acknowledgement.                |
| INT-002  | SCHEMA_INVALID         | Message does not match contract.                     | Quarantine and correct source.                        |
| INT-003  | SOURCE_UNAVAILABLE     | Upstream endpoint unavailable.                       | Retry; use stale-state warning.                       |
| AUTH-001 | FORBIDDEN              | Actor lacks required permission/scope.               | Escalate to authorized role.                          |
| VAL-001  | INVALID_EFFECTIVE_DATE | Future event falls into closed/invalid day.          | Choose next open day or compensating correction flow. |

# Appendix C. Source Register

| **ID** | **Source**                                            | **URL**                                                                                                                       | **Usage**                                                                                                                                     |
| ------ | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| SRC-01 | MAPNA Generator official homepage                     | <https://mapnagenerator.com/>                                                                                                 | Company overview, product/capability statements, contact and current site context.                                                            |
| SRC-02 | MAPNA Generator official About/Intro page             | <https://mapnagenerator.com/Fa/Intro>                                                                                         | History, thermal/hydro generator capacities, busduct, wind, industrial/traction/electric products, after-sales/services and export statement. |
| SRC-03 | MAPNA Generator official Achievements page            | <https://mapnagenerator.com/Fa/Achivements>                                                                                   | Stated installed-generation contribution and engineering improvement examples; note site numerical inconsistency.                             |
| SRC-04 | SAP Help — SAP Integration Suite / Cloud Integration  | <https://help.sap.com/docs/integration-suite/sap-integration-suite/ci>                                                        | Integration Suite supports process integration across cloud and on-premise landscapes.                                                        |
| SRC-05 | SAP Help — Cloud Connector for on-premise integration | <https://help.sap.com/docs/integration-suite/sap-integration-suite/using-sap-cloud-connector-with-cloud-integration-adapters> | Controlled access from SAP BTP integration to on-premise systems.                                                                             |
| SRC-06 | Spring Boot system requirements                       | <https://docs.spring.io/spring-boot/system-requirements.html>                                                                 | Current stable Spring Boot system requirements; Java 17+ minimum for Spring Boot 4.1.1.                                                       |
| SRC-07 | PostgreSQL 17 documentation                           | <https://www.postgresql.org/docs/17/>                                                                                         | PostgreSQL 17 architecture, declarative partitioning and operational features.                                                                |
| SRC-06 | PostgreSQL 17 documentation                           | <https://www.postgresql.org/docs/17/ddl.html>                                                                                 | Declarative partitioning and relational data-definition capabilities.                                                                         |
| SRC-07 | Spring Boot system requirements                       | <https://docs.spring.io/spring-boot/system-requirements.html>                                                                 | Current Spring Boot platform/runtime compatibility reference used for stack baseline.                                                         |

# Implementation Baseline Checklist

1\. Architecture sign-off: ADR-001..ADR-010 accepted.

2\. SAP interface inventory completed and release-specific APIs selected.

3\. Master-data ownership matrix approved.

4\. Daily planning calendar and cut-off rule approved.

5\. Commitment classes and approval thresholds approved.

6\. Baseline objective function configuration approved.

7\. Initial reference products/routings loaded and reconciled.

8\. Performance dataset built and benchmark passed.

9\. Security roles / SoD matrix approved.

10\. DR backup/restore drill passed.

11\. UAT scenarios passed and production cutover approved.

**IMPLEMENTATION RULE:** This document is the architecture baseline. Any deviation from the mandatory principles, temporal model, SAP integration boundary, or audit rules requires a documented Architecture Decision Record and explicit approval before code is merged.