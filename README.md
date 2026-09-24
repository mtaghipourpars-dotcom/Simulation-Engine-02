# MAPNA PARS Production Control Tower — Agent Skill Package

This package restructures the project documentation into the Agent Skills open format.

## Canonical structure

```text
mapna-pars-production-control-tower/
├── SKILL.md
├── README.md
├── references/
│   ├── MAPNA_PARS_Dynamic_Production_Control_Tower_MASTER_SPEC_V2.0.docx
│   ├── MAPNA_PARS_Dynamic_Production_Planning_Architecture_v1.0_2.docx
│   ├── MAPNA_PARS_Dynamic_Production_Control_Tower_Implementation_Spec_V1.0_2.docx
│   ├── MAPNA_PARS_Dynamic_Production_Control_Tower_Implementation_Spec_V1.1_UI_Features.docx
│   ├── MAPNA_PARS_Dynamic_Production_Planning_Architecture_v1.1_UI_Features.docx
│   ├── menu-functionality.md
│   └── scenarios.md
├── scripts/
└── assets/
```

The format follows the canonical Agent Skills specification: a skill directory contains a required `SKILL.md`; optional `references/`, `scripts/`, and `assets/` are used for progressive disclosure. The main `SKILL.md` is intentionally kept concise while detailed material remains in references.

## Source precedence

`MASTER_SPEC_V2.0` is the authoritative implementation contract. Earlier V1/V1.1 documents are retained as references and historical detail; they must not silently override the Master Specification.

## Validation

Run:

```bash
skills-ref validate ./mapna-pars-production-control-tower
```

Then run the project build/test suite and verify the release gates defined in `SKILL.md`.
