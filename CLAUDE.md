# Norman Shutters HA Integration

## After every change

Always run the following before finishing. Tools like `ruff` and `pytest` are installed in the `.venv` virtualenv — always source it first:

```bash
source .venv/bin/activate && ruff check custom_components/ tests/
source .venv/bin/activate && ruff format --check custom_components/ tests/
source .venv/bin/activate && pytest tests/ -v
```

Fix any lint errors or test failures before considering the task complete.
