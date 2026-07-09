# Tab Management — Patterns and Constraints

This reference covers tab-specific orchestration patterns, when to use single-tab
vs multi-tab setups, and how to manage tabs during an orchestration cycle.

## Tab Architecture

### Single-Tab Orchestration (Primary Mode)

All work happens in ONE tab. The orchestrator + all sub-agents are visible simultaneously.

```
TAB: "task-name"
┌────────┬────────┬────────┬────────┐
│ ORCH   │ SUB-A  │ SUB-B  │ SUB-C  │
│        │        │        │        │
└────────┴────────┴────────┴────────┘
```

**When to use:** 3-4 panes or fewer, the human wants to watch everything at once,
no tab-switching needed.

**Pros:**

- Everything visible at a glance
- No tab-switching overhead
- Human always sees the orchestrator's reasoning
- Clean, focused workspace

**Cons:**

- Hard to read past 4 panes
- Limited horizontal space per pane

### Multi-Tab Orchestration (Extended Mode)

Extra tabs for deep-dives, monitoring, or when the workspace is too large for one tab.

```
TAB: "orchestrator"    TAB: "deep-dive-A"    TAB: "monitor"
┌────────┬────────┐    ┌──────────────────┐  ┌──────────────────┐
│ ORCH   │ SUB-A  │    │ SUB-A deep view  │  │ status logs      │
│        │ SUB-B  │    │                  │  │ metrics          │
└────────┴────────┘    └──────────────────┘  └──────────────────┘
```

**When to use:** 5+ sub-agents, need detailed views of individual agents, or need
dedicated monitoring tabs.

**Cons:** The human must switch tabs to see deep views.

## Tab Creation During Orchestration

### Creating Tabs on Demand

Sometimes you need a new tab mid-orchestration:

```bash
# Create a new tab for a deep-dive
herdr tab create --workspace <wid> --label "deep-dive" --no-focus

# Later, move a sub-agent's pane to it
herdr pane move <pane-id> --tab <new-tab-id>
```

**When to create a new tab:**

- A sub-agent needs more space than a narrow right-side pane can provide
- You want a dedicated monitoring/health tab
- The human requests a specific view

**When NOT to create a new tab:**

- The work fits in the existing tab
- The human wants everything visible at once
- Creating tabs defeats the purpose of single-tab orchestration

### Cleaning Up Tabs

When a sub-agent's tab is no longer needed:

```bash
# Close the tab (keeps workspace intact)
herdr tab close <wid>:<tid>
```

Close tabs you created for deep-dives once the deep-dive is complete.

## Tab Navigation

### When the Human Must Switch Tabs

```bash
# Tell the human to switch tabs
"Switch to the 'deep-dive' tab to see agent A's detailed output."
```

Only ask the human to switch tabs when:

- You have a dedicated deep-dive tab
- The human explicitly asked for it
- You're in multi-tab mode

### When the Orchestrator Must Switch Tabs

```bash
# If you need to read something in another tab
herdr tab focus <wid>:<tid>
herdr pane read <pane-id> --lines 50
# ... do the work ...
herdr tab focus <your-tab-id>  # Switch back
```

Always switch back to your orchestration tab after reading something in another tab.

## Tab Layout Examples

### Example: 5-Agent Fan-Out (Split Across Tabs)

```
TAB: "orchestrator"        TAB: "workers"
┌────────┬────────┐        ┌────────┬────────┬────────┐
│ ORCH   │ MON    │        │ W1     │ W2     │ W3     │
│        │        │        │        │        │        │
└────────┴────────┘        └────────┴────────┴────────┘
```

Tab 1: Orchestrator + monitoring pane
Tab 2: All 3 workers (too many for a single tab with the orchestrator)

### Example: Pipeline with Review

```
TAB: "pipeline"             TAB: "review"
┌────────┬────────┬────────┐  ┌──────────────────┐
│ ORCH   │ IMP    │ REV    │  │ REVIEW DETAILS   │
│        │        │        │  │                  │
└────────┴────────┴────────┘  └──────────────────┘
```

Tab 1: Main pipeline flow
Tab 2: Detailed review output (the human can review at their own pace)

## Tab Best Practices

1. **Default to one tab.** Single-tab orchestration is the primary mode.
2. **Name tabs clearly.** "orchestrator", "deep-dive", "monitor" — not "tab 1", "tab 2".
3. **Create tabs with --no-focus.** Don't steal the user's attention.
4. **Clean up tabs you create.** Close deep-dive tabs when they're no longer needed.
5. **Limit extra tabs to 2-3 max.** More than that and the workspace gets fragmented.
6. **Switch back after reading.** If you look at another tab, return to yours.
