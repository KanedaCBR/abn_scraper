# Database Testing Protocol & Procedure

**Status:** Active
**Version:** 1.0
**Date:** 2026-01-03
**Scope:** Cross-project

This protocol defines a systematic, repeatable process for testing database operations (Create, Read, Update, Delete, and Transformation logic) using static test datasets and predefined expected results.

---

## 1. Objective

To perform systematic, repeatable testing of database operations using:
- Static test datasets
- Predefined expected results
- Clear approval gates between phases

---

## 2. Guardrails (Strict Adherence Required)

| Guardrail | Description |
|-----------|-------------|
| **Freeze Point** | Once Test Data and Expected Output are approved by the user, they are "Frozen." The agent must NOT modify these files during the testing phase. |
| **Isolation** | Tests must be run against a dedicated testing environment or schema to prevent data contamination. |
| **No Progress Gate** | The agent is strictly PROHIBITED from executing tests until the user has explicitly reviewed and approved the Test Plan (defined in Phase 1). |

---

## 3. Phase 1: Preparation & Design (The "Review" Gate)

Before any testing occurs, the agent must generate and present a **Test Package** for user approval.

### Agent Actions

#### Step 1: Analyze Schema
Review the target database schema/table definitions.

#### Step 2: Generate Test Data (Input)
Create JSON files (max 20 records) for the following scenarios:

| Scenario | Description |
|----------|-------------|
| **Baseline** | Standard alphanumeric values |
| **Null Handling A** | First 50% of fields populated; remainder NULL |
| **Null Handling B** | Second 50% of fields populated; remainder NULL |
| **Boundary/Stress** | Long strings (e.g., 70+ characters) and special characters |
| **Validation** | Data that intentionally violates constraints (e.g., strings in integer fields) AND data that strictly adheres to them |

#### Step 3: Generate Expected Output
For every input file, create a corresponding "Expected Output" file. This represents what the database state should look like after the operation is successful.

#### Step 4: Submit for Review
Present the Data and Expected Output in a tabular format for user review.

### STOP - Mandatory Approval Gate

```
========================================
PHASE 1 COMPLETE - AWAITING USER APPROVAL
========================================

The agent MUST wait for explicit user approval before proceeding to Phase 2.

User must confirm:
[ ] Test data reviewed and approved
[ ] Expected outputs reviewed and approved
[ ] Test environment confirmed ready

Proceed to Phase 2? (Y/N)
========================================
```

---

## 4. Phase 2: Execution

Once approved, the agent executes tests following these steps:

| Step | Action | Details |
|------|--------|---------|
| 1 | **Environment Reset** | Ensure the target database/table is cleared of previous data |
| 2 | **Ingestion** | Load the "Frozen" Test Data into the database |
| 3 | **Capture** | Execute the required database operation/query and capture the result exactly as produced |
| 4 | **Storage** | Save results to `test_results/actual/` using naming convention matching the test case |

### Naming Convention

| Test Case | Input File | Actual Output File |
|-----------|------------|-------------------|
| 01 - Baseline | `test_01_baseline_input.json` | `test_01_baseline_actual.json` |
| 02 - Null A | `test_02_null_a_input.json` | `test_02_null_a_actual.json` |
| 03 - Null B | `test_03_null_b_input.json` | `test_03_null_b_actual.json` |
| 04 - Boundary | `test_04_boundary_input.json` | `test_04_boundary_actual.json` |
| 05 - Validation | `test_05_validation_input.json` | `test_05_validation_actual.json` |

---

## 5. Phase 3: Analysis & Reporting

The agent must provide a comparative report highlighting the success or failure of the suite.

### Report Requirements

#### Comparison Table
Side-by-side comparison of "Expected" vs. "Actual"

#### Status Flag
Clear PASS or FAIL for each test case

#### Discrepancy Log
If a test fails, identify the specific field or record where the actual output deviated from expected

### Example Report Format

| Test Case ID | Scenario | Expected Result | Actual Result | Status |
|--------------|----------|-----------------|---------------|--------|
| 01 | Baseline Alphanumeric | 20 records inserted | 20 records inserted | **PASS** |
| 02 | Null Handling A | 20 records, null fields preserved | 20 records, null fields preserved | **PASS** |
| 03 | Null Handling B | 20 records, null fields preserved | 20 records, null fields preserved | **PASS** |
| 04 | Boundary (Long Entry) | String truncated at 70 | Error: String too long | **FAIL** |
| 05 | Validation (Invalid) | Constraint error raised | Constraint error raised | **PASS** |

### Discrepancy Detail (for FAIL cases)

```
========================================
DISCREPANCY LOG - Test Case 04
========================================
Field: description
Record: 3
Expected: "Lorem ipsum dolor..." (truncated at 70 chars)
Actual: ERROR - "String too long for column 'description'"
Root Cause: Column length constraint not matching expected behavior
========================================
```

---

## 6. File Structure

The agent will organize the workspace as follows:

```
project_root/
├── test_data/
│   ├── input/                    # (Frozen) JSON input files
│   │   ├── test_01_baseline_input.json
│   │   ├── test_02_null_a_input.json
│   │   ├── test_03_null_b_input.json
│   │   ├── test_04_boundary_input.json
│   │   └── test_05_validation_input.json
│   │
│   └── expected/                 # (Frozen) Expected results
│       ├── test_01_baseline_expected.json
│       ├── test_02_null_a_expected.json
│       ├── test_03_null_b_expected.json
│       ├── test_04_boundary_expected.json
│       └── test_05_validation_expected.json
│
└── test_results/
    ├── actual/                   # Captured results from test run
    │   ├── test_01_baseline_actual.json
    │   ├── test_02_null_a_actual.json
    │   ├── test_03_null_b_actual.json
    │   ├── test_04_boundary_actual.json
    │   └── test_05_validation_actual.json
    │
    └── report.md                 # Final summary report
```

---

## 7. Quick Reference Checklist

### Phase 1 Checklist (Preparation)
- [ ] Schema analyzed
- [ ] Baseline test data created
- [ ] Null Handling A test data created
- [ ] Null Handling B test data created
- [ ] Boundary/Stress test data created
- [ ] Validation test data created
- [ ] Expected outputs generated for all scenarios
- [ ] Test package presented to user
- [ ] **USER APPROVAL RECEIVED**

### Phase 2 Checklist (Execution)
- [ ] Test environment reset/cleared
- [ ] Test data loaded
- [ ] Operations executed
- [ ] Results captured to `test_results/actual/`

### Phase 3 Checklist (Reporting)
- [ ] Comparison table generated
- [ ] PASS/FAIL status assigned
- [ ] Discrepancy log created for failures
- [ ] Report saved to `test_results/report.md`

---

## 8. Governance Reference

**Authority:** [../SYSTEM_CONTRACT.md](../CF - SYSTEM_CONTRACT.md)
**Related:** [TEST_SPEC_TEMPLATE.md](CF - TEST_SPEC_TEMPLATE.md)

This protocol is part of the CascadeForge testing framework and should be used in conjunction with project-specific TEST_SPECIFICATIONS.md files.

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial protocol definition |
