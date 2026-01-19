# Known Issues for Future Resolution

## Issue 1: Retrieval Strategy Priority

**Date Identified:** 2026-01-19

**Problem:**
The system does not consistently try date-range retrieval first before falling back to keyword search. Currently, the retrieval strategy selection lacks a clear priority order.

**Expected Behavior:**
1. Planner should instruct Retriever to try **date-range search first**
2. If date-range search returns insufficient results, fall back to **keyword search**
3. This should be the default behavior for most queries

**Root Cause:**
This is a **Planner orchestration issue**, not a Retriever issue. The Planner generates `retrieval_instructions` that the Retriever executes. The Planner needs to encode this priority logic.

**Where to Fix:**
- `Planner` agent prompt/logic (Section 12.3 in agent-system-design.md)
- Possibly add retrieval strategy priority configuration to `PlannerOutput`

**Related Context:**
- Architecture: `_bmad-output/planning-artifacts/agent-system-design.md`
- Retrieval tools: `get_entries_by_date_range()`, `search_entries()` in StorageRepository

**Status:** Pending (to be addressed after E2E evaluation infrastructure is in place)

---

*Add new issues below using the same format*
