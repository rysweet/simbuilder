# Stub: Integrate graph commands into tdcli

This is a stub branch for integrating existing graph commands into the main tdcli interface.

## Related Issue

- Issue #29: Integrate graph commands into tdcli (info, check)

## Commands to Integrate

- `tdcli graph info` - Show graph database information and node counts
- `tdcli graph check` - Run graph connectivity and consistency checks

## Implementation Notes

- Graph functions ALREADY EXIST in `src/simbuilder_graph/cli.py`
- Functions `graph_info()` and `graph_check()` are implemented
- Need to add graph subcommand group to `src/tenant_discovery/cli.py`
- Import and integrate existing functions
- Ensure consistent error handling and environment variable handling

## Existing Implementation

- `src/simbuilder_graph/cli.py` contains working functions
- Need integration, not reimplementation
