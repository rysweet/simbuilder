## 2025-06-12

````bash
git checkout -b fix/tenant-discovery-cli-entry-point
# Created and switched to fix/tenant-discovery-cli-entry-point for CLI entry-point fix (per issue #36).
# Updated pyproject.toml: canonicalized and completed CLI entry-points in [project.scripts] and [tool.poetry.scripts] for all major CLI tools, including tenant-discovery, per #36.
```bash
pip install -e .
# Activated editable install for simbuilder package to enable new/updated console scripts, including tenant-discovery.
````
```bash
git checkout -b feat/tenant-discovery-offline-mode
# Attempted to create new branch for offline CLI mode (issue #39); failed (already exists).
```
```bash
git checkout feat/tenant-discovery-offline-mode
# Switched to existing branch for tenant-discovery offline/demo mode (per issue #39 requirements).
```
