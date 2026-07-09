# Failure Handling — What to Do When Things Go Wrong

This reference covers failure modes, recovery strategies, and escalation paths
for orchestration failures.

## Failure Modes

### F1: Agent Stuck (No Output, State = `working` or `idle`)

**Symptoms:**

- Agent has been `working` or `idle` for >5 minutes
- No new output in the agent's pane
- The agent isn't responding to `herdr agent read`

**Diagnosis:**

```bash
# Check if there's any recent output at all
herdr agent read <name> --source visible --lines 5
herdr agent read <name> --source recent-unwrapped --lines 10

# Check the pane's PTY state
herdr pane read <pane-id> --source recent --lines 10

# Check if herdr is seeing the right process
herdr agent explain <name> --json
```

**Recovery:**

1. **Ping the agent** — send a message and see if it responds:

   ```bash
   herdr agent send <name> "Status check: are you still working? Respond briefly."
   ```

2. **If no response in 30 seconds** — the pane may be dead. Create a replacement:

   ```bash
   NEW_PANE=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
   herdr pane run "$NEW_PANE" "<original-agent-command> --task '<original-task>'"
   ```

3. **Close the dead pane** after the replacement is working:

   ```bash
   herdr pane close <dead-pane-id>
   ```

### F2: Agent in Wrong State

**Symptoms:**

- Agent is `idle` but clearly producing output
- Agent is `working` but actually stuck at a prompt
- Agent is `blocked` but the human sees nothing

**Diagnosis:**

```bash
herdr agent explain <name> --json
```

Check:

- **Manifest source** — is herdr matching the right agent?
- **Authority** — is it Authority A (hook) or Authority B (screen detection)?
- **Bottom buffer** — is the live bottom buffer matching what you expect?

**Recovery:**

- **Authority B (screen detection) wrong** — read the pane directly to see the truth:

  ```bash
  herdr agent read <name> --lines 50
  ```

  Trust what you read over the reported state.

- **herdr matching wrong process** — if herdr sees `tmux` instead of the agent,
  the agent is invisible. Run the agent directly in the pane without tmux.

- **False `blocked`** — sometimes screen detection triggers on a false positive.
  If the human sees no prompt, try sending a space character:

  ```bash
  herdr pane send-keys <pane-id> " "
  ```

### F3: Agent Producing Wrong Output

**Symptoms:**

- Agent is `done` but the output is incomplete, incorrect, or off-scope
- Pipeline stage produced unusable output

**Recovery:**

1. **Read the output** in your pane to assess what went wrong
2. **Decide the fix:**
   - **Resend the original task** — sometimes the agent just needs a retry:

     ```bash
     herdr agent send <name> "Your output was incomplete. Please finish the task. Scope: <re-state scope>."
     ```

   - **Create a fixer agent** — better than restarting the same agent:

     ```bash
     FIX_PANE=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
     herdr pane run "$FIX_PANE" "<agent> --task 'Fix the issues found in <component>: <summary>'"
     ```

   - **Escalate to the human** — if the issue is fundamental (wrong approach, not just a bug):

     ```
     Agent "<name>" produced output that doesn't match the brief:
     [what was expected]
     [what was produced]
     
     Do I: [A] Resend the task, [B] Create a fixer, [C] Stop and report?
     ```

### F4: Agent Collision (Two Agents Editing Same File)

**Symptoms:**

- Two agents report editing the same file
- One agent's changes get overwritten by the other
- Git conflicts appear

**Detection:**
Watch for this during briefing. Before deploying, confirm:

```
Sub-agent A owns: src/auth/login.ts, src/auth/logout.ts
Sub-agent B owns: src/auth/profile.ts, src/auth/settings.ts
→ No overlap ✓

Sub-agent A owns: src/api/
Sub-agent B owns: src/api/
→ Collision! ❌
```

**Prevention:**

- Define disjoint scopes in each agent's brief
- Use worktrees for parallel work in the same repo

**Recovery:**

1. **Identify the collision** — check which agents are editing the same files
2. **Pause the agent that arrived second:**

   ```bash
   # If possible, send a "hold on" message
   herdr agent send <later-agent> "Hold — you may collide with <other-agent> on <files>. Let me know when I can re-assign."
   ```

3. **Re-scope the second agent** to disjoint files
4. **Document the scope** for future reference

### F5: Pipeline Break

**Symptoms:**

- Stage N+1 starts before stage N is done
- Stage N's output is consumed before it's ready
- Pipeline agent reports `blocked` on missing input

**Recovery:**

1. **Wait for stage N** before starting stage N+1:

   ```bash
   herdr agent wait <stage-n-agent> --status done --timeout 120000
   ```

2. **Read stage N's output** before handing to stage N+1:

   ```bash
   N_OUTPUT=$(herdr agent read <stage-n-agent> --lines 100)
   herdr agent send <stage-n1-agent> "Here's stage N's output: $N_OUTPUT"
   ```

3. **If stage N's output is bad** — fix or retry stage N before proceeding

### F6: Cascade Failure

**Symptoms:**

- One agent fails, causing its downstream agents to fail
- Multiple agents report issues in sequence

**Recovery:**

1. **Pause the pipeline/fan-out** — stop deploying new agents until the issue is resolved
2. **Fix the root cause** — usually the first failing agent
3. **Restart downstream agents** — after fixing the root cause, re-deploy agents
   that depended on the failed agent

```bash
# Pause: send "hold" to all agents
for agent in agent-a agent-b agent-c; do
  herdr agent send "$agent" "Pause all work. Awaiting instructions."
done

# Fix the root cause
herdr agent read <root-agent> --lines 100
# ... fix it ...

# Resume downstream agents
herdr agent send <agent-b> "Root cause fixed. Resuming: <new-task>"
herdr agent send <agent-c> "Root cause fixed. Resuming: <new-task>"
```

### F7: Herdr Server Unavailable

**Symptoms:**

- `herdr status` returns an error
- All herdr commands fail
- The server crashed or was stopped

**Recovery:**

```bash
# Check if the server is running
herdr status

# If not running, start it
herdr --session <session-name> &
# or in foreground:
herdr --session <session-name>
```

**After restart:**

- Layout returns (workspace → tab → pane structure)
- Processes DO NOT return (panes come back as fresh shells)
- Agent integrations may need to be re-enabled: `herdr integration status`

**Prevention:**

- Use `herdr --session <name>` for named sessions (easier to reconnect)
- Keep a fallback SSH session open for server restarts

### F8: Timeout

**Symptoms:**

- An agent hasn't reached `done` within the expected time
- A handoff is waiting on a `done` state that never arrives

**Recovery:**

```bash
# Check what's happening
herdr agent read <name> --lines 50

# If the agent is clearly stuck:
# Option 1: Ping it
herdr agent send <name> "Timeout check: please report your status."

# Option 2: Create a replacement
NEW_PANE=$(herdr pane split <your-pane-id> --direction right --no-focus ...)
herdr pane run "$NEW_PANE" "<agent> --task '<original-task>'"

# Option 3: Escalate to human
```

**Timeout values:**

- Small tasks (single function): 2 minutes
- Medium tasks (multiple functions): 5 minutes
- Large tasks (entire module): 10 minutes
- When in doubt: 5 minutes is a safe default

## Escalation Framework

| Failure | Can You Fix? | Escalate to Human? |
|---------|-------------|-------------------|
| Agent stuck (F1) | Yes — ping, replace | If ping fails and replacement fails |
| Wrong state (F2) | Yes — read pane directly | If you can't determine the truth |
| Wrong output (F3) | Sometimes — re-send or fixer | If the issue is fundamental |
| Collision (F4) | Yes — re-scope | If re-scoping isn't possible |
| Pipeline break (F5) | Yes — wait and retry | If the pipeline is fundamentally broken |
| Cascade (F6) | Yes — pause and fix | If cascade is extensive |
| Server down (F7) | Yes — restart server | If you can't restart the server |
| Timeout (F8) | Sometimes — ping or replace | If agent is truly stuck |

## Post-Failure Reporting

After a failure and recovery, report to the human:

```
⚠️ Failure recovered

What happened: [brief description]
How I fixed it: [action taken]
Impact: [what was affected, what still needs attention]
```
