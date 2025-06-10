## 2025-06-10

```bash
PYTHONPATH=./src TD_AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1 TD_AZURE_CLIENT_ID=00000000-0000-0000-0000-000000000000 TD_AZURE_CLIENT_SECRET=dummypass TD_SUBSCRIPTION_ID=11111111-1111-1111-1111-111111111111 python -m tenant_discovery.cli config info
# Validate Tenant Discovery configuration; encountered ModuleNotFoundError: pydantic
uv pip install -e .
# Install project in editable mode

PYTHONPATH=./src TD_AZURE_TENANT_ID=3cd87a41-1f61-4aef-a212-cefdecd9a2d1 TD_AZURE_CLIENT_ID=00000000-0000-0000-0000-000000000000 TD_AZURE_CLIENT_SECRET=dummypass TD_SUBSCRIPTION_ID=11111111-1111-1111-1111-111111111111 python -m tenant_discovery.cli config info
# Second attempt; ModuleNotFoundError persists

gh issue create --title "Tenant Discovery CLI: ModuleNotFoundError for pydantic" --body ...
# Created GitHub issue #3 to track bug

git switch -c fix/pydantic-dependency
# Switched to new branch for fix

python -c "import importlib, sys; print(importlib.util.find_spec('pydantic'))"
# Verified pydantic still unavailable
```