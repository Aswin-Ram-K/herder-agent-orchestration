# Pane Orchestration — Deep Dive

This reference contains detailed patterns for tab-internal pane orchestration — how
to design, size, and arrange panes so the orchestrator and sub-agents all fit in one
tab while remaining readable.

## Pane Layout Patterns

### Pattern: 2 Panes (You + 1 Sub-Agent)

```
┌──────────────┬──────────────┐
│              │              │
│  ORCHESTRATOR│  SUB-AGENT   │
│  (50%)       │  (50%)       │
│              │              │
└──────────────┴──────────────┘
```

Best for: single sub-task, review cycles, agent+human collaboration.

### Pattern: 3 Panes (You + 2 Sub-Agents)

```
┌──────────┬──────────┬──────────┐
│          │          │          │
│ ORCH     │ SUB-A    │ SUB-B    │
│ (40%)    │ (30%)    │ (30%)    │
│          │          │          │
└──────────┴──────────┴──────────┘
```

Best for: parallel fan-out with 2 independent tasks, implementer+reviewer.

### Pattern: 4 Panes (You + 3 Sub-Agents)

```
┌───────┬───────┬───────┬───────┐
│       │       │       │       │
│ ORCH  │ SUB-A │ SUB-B │ SUB-C │
│ (35%) │ (22%) │ (22%) │ (22%) │
│       │       │       │       │
└───────┴───────┴───────┴───────┘
```

Best for: council, 3 independent sub-tasks.

### Pattern: 5+ Panes — Consider Splitting

When you need more than 4 panes total, legibility degrades. Options:

1. **Batch the sub-tasks** — do a first round with panes 1-4, then a second round
2. **Split across tabs** — if the human is OK with tab-switching
3. **Manager/Worker** — have the orchestrator coordinate a smaller set of workers
   that each manage their own sub-tasks

## Pane Sizing Rules

### The Orchestrator Pane

Your pane should be **at least 35%** of the tab width. This ensures:

- The human can read your reasoning
- Your output is scrollable
- You have room for structured reports

### Sub-Agent Panes

Sub-agent panes should be **at least 20%** each. Below that:

- Output is hard to read
- Terminal rendering degrades
- The agent's output appears truncated

### Resize Mid-Run

You can resize panes mid-orchestration if a sub-agent needs more room:

```bash
herdr pane resize <pane-id> --ratio 0.30  # Give 30% to this pane
```

Useful when:

- A sub-agent is producing long output (tests, logs)
- A sub-agent is generating code (needs width)
- You want to focus on one agent while others wait

## Pane Creation Strategies

### Strategy: Sequential Right-Splits

```bash
# Each split creates a new pane to the right, pushing existing right panes left
PANE_A=$(herdr pane split <your-pane> --direction right --no-focus ...)
PANE_B=$(herdr pane split <your-pane> --direction right --no-focus ...)
PANE_C=$(herdr pane split <your-pane> --direction right --no-focus ...)
```

Result: YOUR PANE ─ A ─ B ─ C (all at the same level, all directly right of you)

**Pros:** Clean flat structure, all panes at same level
**Cons:** Each split shifts existing panes left

### Strategy: Chained Right-Splits

```bash
# Each new pane is right of the previous one
PANE_A=$(herdr pane split <your-pane> --direction right --no-focus ...)
PANE_B=$(herdr pane split $PANE_A --direction right --no-focus ...)
PANE_C=$(herdr pane split $PANE_B --direction right --no-focus ...)
```

Result: YOUR PANE ─ A ─ B ─ C (C is right of B, B is right of A)

**Pros:** Predictable — each new pane goes after the last
**Cons:** Harder to resize all panes equally (they're not siblings)

### Strategy: Down-Split for Vertical Monitoring

If the horizontal space is tight, split down for a second row:

```
┌──────────────┬────────────┬────────────┐
│              │            │            │
│  ORCHESTRATOR│  SUB-A     │  SUB-B     │
│  (40%)       │  (30%)     │  (30%)     │
│              │            │            │
├──────────────┤            │            │
│              │            │            │
│  MONITOR     │  SUB-C     │  SUB-D     │
│  (40%)       │  (30%)     │  (30%)     │
│              │            │            │
└──────────────┴────────────┴────────────┘
```

Best for: 4+ sub-agents where horizontal space is limited but you still want
everything visible.

## Common Pane Setup Mistakes

1. **Your pane too narrow** — The human can't read your reasoning. Keep it ≥35%.
2. **Too many panes** — Past 4 panes in a tab, nothing is readable. Batch your work.
3. **Not resizing after adding panes** — When you add a 4th pane, the original 3 panes
   shrink. Resize your pane after creating all sub-agent panes.
4. **Using --focus instead of --no-focus** — This steals the user's terminal focus
   each time you create a pane. Always use --no-focus for scripting.
5. **Not naming agents** — Pane IDs compact. Names persist. Name everything.

## Testing Pane Layouts

To test a pane layout without deploying real agents:

```bash
# Create a test layout with just shells
PANE_A=$(herdr pane split <your-pane> --direction right --no-focus ...)
herdr pane run "$PANE_A" "sleep 30 && echo 'agent-a done'"

PANE_B=$(herdr pane split <your-pane> --direction right --no-focus ...)
herdr pane run "$PANE_B" "sleep 30 && echo 'agent-b done'"
```

This creates a layout you can test. Replace the shell commands with actual agent
deployments once the layout works.
