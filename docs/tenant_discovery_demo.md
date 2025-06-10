# Tenant Discovery Demo Walk-Through

**Environment:**

- `AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1` (from project `.env`)
- All commands run in the project root.

This document demonstrates step-by-step use of the tenant-discovery CLI with the configured tenant.
For each step:

- The exact CLI command, environment setup, and output are displayed.
- Any errors or failures are documented, with issues and stub PRs opened in GitHub as required.

______________________________________________________________________

## Step 1: Show Current Configuration

With only required env vars (no client ID or subscription ID):

**Command:**

```bash
TD_AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1 \
TD_AZURE_CLIENT_SECRET=cli-secret \
tdcli config info
```

**Output:**

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳─────────────────────────────────────────────┳────────────────────────────────────────────────────────────┓
┃ Setting                              ┃ Value                                       ┃ Description                                                ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻─────────────────────────────────────────────┻────────────────────────────────────────────────────────────┫
┃ Azure Tenant ID                      ┃ 3cd87a41-1f61-4aef-a212-cefdecd9a2d1        ┃ Azure tenant ID for authentication                         ┃
┃ Azure Client ID                      ┃ [not set]                                   ┃ Azure client ID for authentication (optional)              ┃
┃ Azure Client Secret                  ┃ ***cret                                      ┃ Azure client secret (masked)                               ┃
┃ Subscription ID                      ┃ [not set]                                   ┃ Azure subscription ID for resource discovery (optional)    ┃
┃ Graph DB URL                         ┃ bolt://localhost:30000                      ┃ Neo4j graph database connection URL                        ┃
┃ Service Bus URL                      ┃ nats://localhost:30002                      ┃ NATS service bus connection URL                            ┃
┃ Log Level                            ┃ INFO                                        ┃ Logging level for the service                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻─────────────────────────────────────────────┻────────────────────────────────────────────────────────────┛
⚠ Azure Client ID is not set; some operations may be unavailable.
⚠ Subscription ID is not set; resource discovery may be limited.

✓ Configuration loaded successfully
```

______________________________________________________________________

## Step 2: Validate Configuration

**Command:**

```bash
TD_AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1 \
TD_AZURE_CLIENT_SECRET=cli-secret \
tdcli config check
```

**Output:**

```text
Validating Tenant Discovery configuration...

✓ Azure Tenant ID format
⚠ Azure Client ID presence (optional) [optional] not set
✓ Azure Client Secret presence
⚠ Subscription ID presence (optional) [optional] not set
✓ Graph DB URL format
✓ Service Bus URL format
✓ Log Level validity

✓ All required configuration checks passed!
```

______________________________________________________________________

### 2025-06-10 Run: `tdcli config check`

**Command:**

```bash
tdcli config check
```

**Output:**

```text
DEBUG: Validator input for optional_nullify_zero_uuid: None
DEBUG: Value is None/Falsey, returning None
DEBUG: Validator input for optional_nullify_zero_uuid: None
DEBUG: Value is None/Falsey, returning None
✗ Configuration validation failed:
  • azure_tenant_id: Field required
  • azure_client_secret: Field required
TRACEBACK:
Traceback (most recent call last):
  File "/home/rysweet/src/simbuilder/src/tenant_discovery/cli.py", line 130, in check
    settings = TenantDiscoverySettings(_env_file=None)  # type: ignore
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/rysweet/src/simbuilder/.venv/lib/python3.12/site-packages/pydantic_settings/main.py", line 176, in __init__
    super().__init__(
  File "/home/rysweet/src/simbuilder/.venv/lib/python3.12/site-packages/pydantic/main.py", line 253, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 2 validation errors for TenantDiscoverySettings
azure_tenant_id
  Field required
    For further information visit https://errors.pydantic.dev/2.11/v/missing
azure_client_secret
  Field required
    For further information visit https://errors.pydantic.dev/2.11/v/missing

[exit code: 1]
```

**Result:** FAILED (required environment variables missing)

**GitHub Tracking:**

- [Issue #24: ENV missing blocks tdcli config check](https://github.com/rysweet/simbuilder/issues/24)
- [PR #25: Stub: Fix ENV required for tdcli config check](https://github.com/rysweet/simbuilder/pull/25)

______________________________________________________________________

### 2025-06-10 Run: `tdcli discovery start`

**Command:**

```bash
tdcli discovery start
```

**Output:**

````text
Usage: tdcli [OPTIONS] COMMAND [ARGS]...
Try 'tdcli --help' for help.
---

### 2025-06-10 Run: `tdcli discovery run`

**Command:**
```bash
tdcli discovery run
````

**Output:**

````text
Usage: tdcli [OPTIONS] COMMAND [ARGS]...
Try 'tdcli --help' for help.
╭─ Error ─────────────────────────────────────────────────────╮
│ No such command 'discovery'.                                │
╰─────────────────────────────────────────────────────────────╯
---

### 2025-06-10 Run: `tdcli discovery list`

**Command:**
```bash
tdcli discovery list
````

**Output:**

```text
Usage: tdcli [OPTIONS] COMMAND [ARGS]...
Try 'tdcli --help' for help.
╭─ Error ─────────────────────────────────────────────────────╮
│ No such command 'discovery'.                                │
╰─────────────────────────────────────────────────────────────╯

[exit code: 2]
```

**Result:** FAILED (no such command)

**GitHub Tracking:** See
[Issue #26: discovery command not found](https://github.com/rysweet/simbuilder/issues/26) and
[PR #27: Stub: Add PR for discovery command not found](https://github.com/rysweet/simbuilder/pull/27)

\[exit code: 2\]

```

**Result:** FAILED (no such command)

**GitHub Tracking:**
See [Issue #26: discovery command not found](https://github.com/rysweet/simbuilder/issues/26)
and [PR #27: Stub: Add PR for discovery command not found](https://github.com/rysweet/simbuilder/pull/27)
╭─ Error ─────────────────────────────────────────────────────╮
│ No such command 'discovery'.                                │
╰─────────────────────────────────────────────────────────────╯

[exit code: 2]
```

**Result:** FAILED (no such command)

**GitHub Tracking:**

- [Issue #26: discovery command not found](https://github.com/rysweet/simbuilder/issues/26)
- [PR #27: Stub: Add PR for discovery command not found](https://github.com/rysweet/simbuilder/pull/27)
  _Result: Both commands exit 0 as expected. CLI operates with only tenant ID and client secret;
  client ID/subscription ID are optional._
