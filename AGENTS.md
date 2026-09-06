# Agent Instructions

This file is the repository-wide source of truth for OMP, Pi, Codex, and Claude. `CLAUDE.md` imports it for Claude; OMP, Pi, and Codex must read and follow it directly.

## Primary goal

The goal of this project is an **unconditional proof of Erdős Problem 193**. Keep that goal visible when choosing, running, and evaluating work. Conditional theorems, finite computations, experiments, and heuristic evidence are useful only insofar as they advance an unconditional proof; never present them as the final result.

## Unit-step follow-up checkpoint

For work on the Cambie–Kalviainen / Shallit positive-basis follow-up, start with
[`research/unit-step/AI-CHECKPOINT.md`](research/unit-step/AI-CHECKPOINT.md) and
[`research/unit-step/PROBLEM.md`](research/unit-step/PROBLEM.md). The target is the
exact minimum dimension for avoiding collinear triples, not an expanding list
of unvetted applications. The
[joint minimum formulation](research/unit-step/JOINT-MINIMUM.md) relates this to
the minimum 3D step count, with explicit quantifiers and no assumption that the
two minima coincide. Keep these questions distinct from the original Erdős 193
theorem. Preserve manuscript attribution and the distinctions between
proved lower bounds, unreviewed upper-bound drafts, and finite evidence.

## Progress communication

- Signpost meaningful phases of work. Tell the user what is happening, why it is the next useful step, and what result or decision it should produce.
- For a long-running task, post an ETA before starting it. Give an honest range when runtime is uncertain, report material changes to the estimate, and post periodic progress updates rather than going silent.
- Report blockers, failed approaches, and changes of direction promptly, with enough context to explain the next action.

## Host resource limits

- The host has 8 CPU cores. Use **no more than 4 cores in aggregate**, including subprocesses, workers, and native numerical-library threads.
- Configure tools and libraries accordingly (for example, worker counts and `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, and `NUMEXPR_NUM_THREADS`). Prefer fewer cores when 4 are unnecessary.
- Avoid unbounded parallelism and monitor memory and disk use for large computations. Do not trade host stability for speed.

## Resumable Python work

- Make every Python process that performs substantive work safely resumable after interruption.
- Persist checkpoints or append-only intermediate results at useful intervals, using atomic writes where replacement is required. Record enough metadata to reject incompatible or corrupt checkpoints.
- On restart, detect validated prior progress and continue from it instead of recomputing completed work. Make result writes idempotent and document the resume behavior in the CLI help or startup log.
- Handle `SIGINT` and `SIGTERM` where practical by flushing a consistent checkpoint before exit.

## Long-running calculation observability

- Instrument long calculations with durable, timestamped logs. At minimum log: parameters and code/config identity, start/resume state, completed and total work, throughput, elapsed time, estimated remaining time, checkpoint paths, resource-relevant settings, and the final outcome or error.
- Emit progress often enough to distinguish healthy work from a stall without flooding logs. Flush progress and error records promptly.
- Keep logs and checkpoints separate from final proof artifacts, and make runs reproducible from the recorded metadata.

## Evidence and visualization

- Update the `viz/` site whenever verified progress materially changes the proof state, the best-known evidence, a key obstruction, or the planned route to an unconditional proof.
- Keep visualization claims synchronized with the underlying proof or experiment artifacts. Clearly label conditional, computational, heuristic, and proved statements; never overstate material progress.
- Do not churn the site for routine refactors or inconclusive runs.

## Token and context discipline

- Treat token usage as a constrained resource. Locate relevant sections with indexes, search, file sizes, and targeted ranges before reading content.
- Do not read large files wholesale when a summary, schema, selected range, or streaming/local computation will answer the question. In particular, inspect large JSON, logs, generated tables, and binary-derived artifacts with bounded queries or scripts.
- Reuse concise notes and prior results instead of repeatedly loading the same material. Delegate or parallelize only when it reduces total work rather than duplicating context.
- Keep user updates concise but do not omit decisions, evidence, risks, ETAs, or blockers.
