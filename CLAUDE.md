# Norman Shutters HA Integration

## After every change

Always run the following before finishing:

```bash
make all
```

This runs lint, format checks, and tests. The Makefile handles venv setup automatically. Fix any errors or failures before considering the task complete.

## Deploying to Home Assistant

After merging to `main`, install the latest version into the running HA instance via the MCP `update.install` service. You must pass the full (long) git SHA of the commit you want to install:

```
mcp__home-assistant__ha_call_service(
    domain="update",
    service="install",
    entity_id="update.norman_shutters_update",
    data={"version": "<full-git-sha>"},
    wait=False,
)
```

The full SHA can be obtained with `git rev-parse HEAD` (or `git rev-parse <branch>`). The entity ID is `update.norman_shutters_update`. HA will need a restart after installation for the new integration code to take effect.

Once installed, restart HA:

```
mcp__home-assistant__ha_call_service(
    domain="homeassistant",
    service="restart",
    wait=False,
)
```
