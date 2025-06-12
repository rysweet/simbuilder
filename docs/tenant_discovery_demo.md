# Tenant Discovery Demo Walk-Through

**Date:** 2025-06-10 **Environment:**

- `AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1` (from project `.env`)
- All commands run in the project root with environment variables set

This document demonstrates step-by-step use of the tenant-discovery CLI with the configured tenant.

## Current CLI Status

**Available Commands:**

- `tdcli config info` - Display current configuration settings
- `tdcli config check` - Validate configuration and environment variables

**Missing Commands (Not Yet Implemented):**

- `tdcli discovery start` - Start tenant discovery job
- `tdcli discovery list` - List discovery jobs
- `tdcli discovery status` - Check discovery job status
- `tdcli graph info` - Show graph database information and node counts
- `tdcli graph check` - Run graph connectivity and consistency checks

______________________________________________________________________

## Step 1: Environment Setup

**Command:**

```bash
export TD_AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1
export TD_AZURE_CLIENT_SECRET=demo-secret
```

**Result:** Environment variables set for tenant discovery demo

______________________________________________________________________

## Step 2: Discovery Start

**Command:**

```bash
TD_AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1 TD_AZURE_CLIENT_SECRET=demo-secret uv run tdcli discovery start
```

**Output:**

```text
Usage: tdcli [OPTIONS] COMMAND [ARGS]...
Try 'tdcli --help' for help.
╭─ Error ─────────────────────────────────────────────────────╮
│ No such command 'discovery'.                                │
╰─────────────────────────────────────────────────────────────╯

[exit code: 2]
```

**Result:** FAILED (command not implemented)

**GitHub Tracking:**

- Issue needed: Discovery command not implemented
- PR needed: Stub implementation for discovery commands

______________________________________________________________________

## Step 3: Discovery Status Poll

**Command:**

```bash
TD_AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1 TD_AZURE_CLIENT_SECRET=demo-secret uv run tdcli discovery list
```

**Output:**

```text
Usage: tdcli [OPTIONS] COMMAND [ARGS]...
Try 'tdcli --help' for help.
╭─ Error ─────────────────────────────────────────────────────╮
│ No such command 'discovery'.                                │
╰─────────────────────────────────────────────────────────────╯

[exit code: 2]
```

**Result:** FAILED (command not implemented)

______________________________________________________________________

## Step 4: Graph Info

**Command:**

```bash
TD_AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1 TD_AZURE_CLIENT_SECRET=demo-secret uv run tdcli graph info
```

**Output:**

```text
Usage: tdcli [OPTIONS] COMMAND [ARGS]...
Try 'tdcli --help' for help.
╭─ Error ─────────────────────────────────────────────────────╮
│ No such command 'graph'.                                    │
╰─────────────────────────────────────────────────────────────╯

[exit code: 2]
```

**Result:** FAILED (command not implemented)

**Note:** Graph functionality exists in `src/simbuilder_graph/cli.py` (`graph_info()` and
`graph_check()` functions) but is not integrated into the tdcli command structure.

______________________________________________________________________

## Step 5: Graph Check

**Command:**

```bash
TD_AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1 TD_AZURE_CLIENT_SECRET=demo-secret uv run tdcli graph check
```

**Output:**

```text
Usage: tdcli [OPTIONS] COMMAND [ARGS]...
Try 'tdcli --help' for help.
╭─ Error ─────────────────────────────────────────────────────╮
│ No such command 'graph'.                                    │
╰─────────────────────────────────────────────────────────────╯

[exit code: 2]
```

**Result:** FAILED (command not implemented)

______________________________________________________________________

## Available Commands Verification

**Command:**

```bash
uv run tdcli --help
```

**Output:**

```text
 Usage: tdcli [OPTIONS] COMMAND [ARGS]...

 Tenant Discovery CLI

╭─ Options ───────────────────────────────────────────────────╮
│ --install-completion          Install completion for the    │
│                               current shell.                │
│ --show-completion             Show completion for the       │
│                               current shell, to copy it or  │
│                               customize the installation.   │
│ --help                        Show this message and exit.   │
╰─────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────╮
│ config   Configuration management commands                  │
╰─────────────────────────────────────────────────────────────╯
```

**Available Config Commands:**

```bash
uv run tdcli config --help
```

**Output:**

```text
 Usage: tdcli config [OPTIONS] COMMAND [ARGS]...

 Configuration management commands

╭─ Options ───────────────────────────────────────────────────╮
│ --help          Show this message and exit.                 │
╰─────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────╮
│ info    Display current configuration settings.             │
│ check   Validate configuration and environment variables.   │
╰─────────────────────────────────────────────────────────────╯
```

______________________________________________________________________

## Demo Results Summary

### Command Results:

- **tdcli discovery start**: ❌ FAILED (exit code: 2) - Command not implemented
- **tdcli discovery list**: ❌ FAILED (exit code: 2) - Command not implemented
- **tdcli graph info**: ❌ FAILED (exit code: 2) - Command not implemented
- **tdcli graph check**: ❌ FAILED (exit code: 2) - Command not implemented

### Available Functionality:

- ✅ **tdcli config info**: Available (displays configuration)
- ✅ **tdcli config check**: Available (validates environment)

### Issues Identified:

1. **Discovery commands missing**: No `discovery` subcommand group in tdcli
1. **Graph commands missing**: No `graph` subcommand group in tdcli
1. **Integration gap**: Graph functions exist in `src/simbuilder_graph/cli.py` but not connected to
   main CLI

### Required GitHub Issues/PRs:

- **Issue**: "Implement tdcli discovery commands (start, list, status)"
- **Issue**: "Integrate graph commands into tdcli (info, check)"
- **PR**: "Add discovery subcommand group to tdcli"
- **PR**: "Add graph subcommand group to tdcli"

### Graph Node Counts:

**Status**: Unable to verify - graph commands not accessible through CLI

### Next Steps:

1. Create GitHub issues for missing functionality
1. Implement discovery and graph subcommand groups in tdcli
1. Re-run demo once commands are implemented
1. Verify graph database connectivity and node counts

______________________________________________________________________

*Demo completed on 2025-06-10 23:51 UTC* *All command failures documented and ready for
implementation tracking*
