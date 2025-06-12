# Migrate from mypy to pyright for type checking

## Summary

Replace mypy with pyright as the primary type checker for the SimBuilder project to improve
performance, IDE integration, and provide better error messages.

## Background

Currently, the project uses mypy for static type checking with configuration in both `mypy.ini` and
`pyproject.toml`. Pyright offers several advantages over mypy:

- **Performance**: Pyright is significantly faster, especially on large codebases
- **IDE Integration**: Better integration with VS Code and other editors
- **Error Messages**: More informative and actionable error messages
- **Configuration**: More flexible configuration options
- **Language Server**: Built-in language server protocol support

## Current mypy Configuration

The project currently has mypy configured with:

- Python 3.12 target version
- Strict type checking settings (disallow_untyped_defs, disallow_incomplete_defs, etc.)
- Ignored imports for external libraries: neo4j, nats, loguru, typer, rich, openai, liquid, tenacity
- Configuration in both `mypy.ini` and `[tool.mypy]` section of `pyproject.toml`

## Tasks

### 1. Install and Configure pyright

- [ ] Add `pyright` to development dependencies in `pyproject.toml`
- [ ] Remove `mypy` from development dependencies
- [ ] Create `pyproject.toml` configuration section for pyright
- [ ] Configure pyright settings to match current mypy strictness level

### 2. Update Pre-commit Configuration

- [ ] Replace mypy hook in `.pre-commit-config.yaml` with pyright
- [ ] Update additional dependencies for the pyright hook
- [ ] Test pre-commit hooks functionality

### 3. Update Build/Task Scripts

- [ ] Update `tasks.py` to replace mypy commands with pyright
- [ ] Update lint task to use pyright instead of mypy
- [ ] Update bootstrap task dependencies
- [ ] Update clean task to remove pyright cache instead of mypy cache

### 4. Update Project Configuration Files

- [ ] Remove `mypy.ini` file
- [ ] Remove `[tool.mypy]` section and overrides from `pyproject.toml`
- [ ] Add comprehensive pyright configuration to `pyproject.toml`

### 5. Handle Type Stub Libraries

- [ ] Review and update type stub dependencies (e.g., `types-python-jose`)
- [ ] Verify that pyright can handle the external library imports currently ignored by mypy
- [ ] Add any necessary type stub packages for better type coverage

### 6. Testing and Validation

- [ ] Run pyright on the entire codebase and fix any new type issues
- [ ] Verify that all existing type annotations work correctly with pyright
- [ ] Test pre-commit hooks with pyright
- [ ] Update CI/CD workflows if any exist

### 7. Documentation Updates

- [ ] Update README.md or development documentation to mention pyright usage
- [ ] Update any contributor guidelines or development setup instructions
- [ ] Document any differences in type checking approach

## Expected pyright Configuration

The pyright configuration should include:

```toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
exclude = [
    "**/node_modules",
    "**/__pycache__",
    ".venv",
]
include = ["src", "tests"]
reportMissingImports = true
reportMissingTypeStubs = false
reportPrivateUsage = "warning"
reportUnknownMemberType = "warning"
reportUnknownArgumentType = "warning"
reportUnknownVariableType = "warning"
```

## Files to be Modified

- `pyproject.toml` (dependencies and configuration)
- `.pre-commit-config.yaml` (hooks)
- `tasks.py` (build tasks)
- `mypy.ini` (to be removed)

## Benefits After Migration

- Faster type checking during development and CI
- Better IDE experience with more responsive type hints
- Improved error messages for easier debugging
- Better integration with VS Code if team uses it
- More active development and faster issue resolution from Microsoft

## Acceptance Criteria

- [ ] All type checking functionality from mypy is preserved
- [ ] Pre-commit hooks work correctly with pyright
- [ ] Build/development tasks execute successfully
- [ ] No new type errors are introduced (existing code should pass type checking)
- [ ] Documentation is updated to reflect the change
- [ ] Performance improvement is measurable (faster type checking)

## Priority

**Medium** - This is a developer experience improvement that doesn't affect runtime functionality
but will improve development workflow.

## Estimated Effort

**2-4 hours** - The migration is straightforward but requires careful testing to ensure all
configurations work correctly.
