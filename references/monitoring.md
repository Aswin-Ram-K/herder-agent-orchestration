# Real-Time Monitoring — Triage, Alerting, and State Tracking

This reference covers how to monitor sub-agents in real-time from within the
orchestrator pane, triage issues, and alert the human at the right moments.

## The Monitoring Loop

As the orchestrator, you should periodically check the state of all sub-agents.
Aim for a check every ~30 seconds, or after each handoff/completion.

```
MONITORING CYCLE:
  1. herdr agent list --json
  2. Sort by urgency (blocked → done → unknown → working → idle)
  3. Take action on each
  4. Report back what you did
```

## State Triage Order

### 1. `blocked` — Highest Priority

An agent is blocked on input (approval, question, permission). This is the most
urgent state because the agent cannot make progress until unblocked.

**Action:**

```bash
herdr agent read <name> --lines 30
# Read the prompt/question
herdr agent send <name> "<answer>"
```

If you can't answer it yourself, escalate to the human:

```
Agent "<name>" is blocked. It's asking:
"<the question>"

What should I tell it?
```

### 2. `done` — Review Required

An agent has finished. But `done` does NOT mean "correct." Always read the output
before using it.

**Action:**

```bash
herdr agent read <name> --lines 100
# Read the output
# Decide: is the output correct? Does it need review?
```

**When to trust `done` output:**

- The output matches the success criterion from the brief
- There's a clear completion signal (e.g., "LOGIN_VALIDATION_DONE")
- The agent has Authority-A (lifecycle hooks)

**When to be cautious:**

- No completion signal in the output
- The agent uses screen detection (Authority-B)
- The output seems incomplete or cut off

### 3. `unknown` — Investigate

herdr couldn't classify the agent's state. This usually means screen detection
has nothing to go on.

**Action:**

```bash
herdr agent explain <name> --json
# Check:
# - What manifest/source is it matching?
# - Is it matching the right agent?
# - Is it a known agent in herdr's database?

herdr agent read <name> --lines 30
# Check the actual output — is it working, idle, or stuck?
```

### 4. `working` — Normal

The agent is actively running. No action needed unless it's been `working` for
unreasonably long (see §Stalled Detection below).

**Action:** Check periodically, no intervention needed.

### 5. `idle` — Suspicious for Authority-B

For screen-detection agents, `idle` can be a false negative — the agent may be
waiting at an unrecognized prompt.

**Action:**

```bash
# Read the agent's recent output to see if it's actually idle
herdr agent read <name> --lines 20
```

If the output shows a prompt the agent is waiting on, treat it as `blocked` and answer it.

## Monitoring Commands

### Quick Fleet Scan

```bash
herdr agent list --json
```

Returns all agents with their states. Use this as your starting point.

### Read Agent Output

```bash
# Recent output (default)
herdr agent read <name> --lines 50

# Unwrapped output (easier to parse)
herdr agent read <name> --source recent-unwrapped --lines 50

# Visible viewport only
herdr agent read <name> --source visible --lines 30
```

### Diagnose State Issues

```bash
herdr agent explain <name> --json
```

Shows why herdr thinks the agent is in its current state, which manifest/source
is being used, and which rules matched.

### Wait for Completion

Instead of polling, wait for a specific state:

```bash
herdr agent wait <name> --status done --timeout 120000
# Or: --status blocked, --status working, etc.

herdr wait output <pane-id> --match "BUILD SUCCESS" --timeout 30000
```

## Alerting the Human

### When to Alert

| Event | Alert? | Reason |
|-------|--------|--------|
| First agent blocked | YES | Something needs human attention |
| All agents done | YES | Milestone reached |
| Any agent done | NO | Too much noise, except first/last |
| Any agent working | NO | Normal operation |
| Any agent idle | NO | Normal, unless suspicious |
| Any agent unknown | YES (if urgent) | Detection failure may block progress |

### How to Alert

```bash
# Desktop notification
herdr notification show "Agent blocked" --body "reviewer is waiting on your input" --sound request

herdr notification show "All agents done" --body "Review the results in your pane" --sound done
```

### In-Pane Alerts

You can also announce alerts in your own pane output:

```
🔔 ALERT: Agent "implementer" has reached `done`. Checking output...
✓ Output looks valid. Handing off to reviewer.
```

## Monitoring Patterns

### Pattern: Check After Each Handoff

After sending input to a sub-agent, check its state to confirm it received the input
and started working:

```bash
herdr agent send implementer "Here's the review feedback: ..."
# Wait a moment
herdr agent read implementer --lines 5
# Should see it acknowledging the feedback and starting work
```

### Pattern: Check Before Each Handoff

Before sending work to the next agent in a pipeline, verify the previous agent is done:

```bash
herdr agent wait implementer --status done --timeout 120000
# Now safe to review and send to reviewer
```

### Pattern: Batch Check (Every N Seconds)

For long-running orchestrations, batch your monitoring:

```
[00:00] Fleet scan — all agents working. Check again at 00:30.
[00:30] Fleet scan — agent A is blocked. Unblocking... Done.
[01:00] Fleet scan — agent A done. Reading output...
[01:05] Sending output to agent B...
[01:30] Fleet scan — agent B working, agent C idle. Continue.
[02:00] Fleet scan — all agents done. Integrating results...
[02:05] Reporting to human.
```

### Pattern: Continuous Monitoring (Advanced)

Subscribe to status-change events (if herdr supports it in your version):

```bash
# Check your version's socket API for the event name
# herdr --help | grep -i event
# or fetch: https://herdr.dev/docs/socket-api/
```

Use continuous monitoring when you want zero-latency detection of state changes
(rather than polling every 30 seconds).

## Stalled Detection

If an agent has been `working` for an unusually long time (e.g., >5 minutes for
a small task), it may be stuck in an infinite loop or processing something slow.

**Investigation:**

```bash
# Check if the agent is producing output (not truly stuck)
herdr agent read <name> --source visible --lines 10

# If output is recent, it's still working (just slow)
# If output is stale, it may be stuck

# For Authority-B agents, try:
herdr agent read <name> --lines 50
```

**Actions:**

- If it's slow but producing output: wait more
- If it's completely stuck: send a "are you still working?" message
- If it's stuck on a loop: cancel and re-brief

```bash
herdr agent send <name> "Are you still working on this? Respond with a status update."
```
