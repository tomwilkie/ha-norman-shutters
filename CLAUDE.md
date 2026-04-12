# Norman Shutters HA Integration

## After every change

Always run the following before finishing:

```bash
ruff check custom_components/ tests/
ruff format --check custom_components/ tests/
pytest tests/ -v
```

Fix any lint errors or test failures before considering the task complete.
