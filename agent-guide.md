# Agent Guide (Odoo 18) — GlucosePumps

This repo runs Odoo 18 via Docker Compose and mounts custom addons from the repo root into `/mnt/custom_addons`.

- Addon (module) name: `glucose_pumps_demo`
- Odoo URL: http://localhost:8069
- Containers: `odoo18-app` (Odoo), `odoo18-db` (Postgres)

## Non‑negotiables (Definition of Done)
A task is **not done** until all are true:

1. Code follows Odoo best practices (below) and is secure by default.
2. The addon is **installed or upgraded** in the running instance.
3. The instance is confirmed **loaded and responsive** (HTTP + logs).
4. UI/flows are verified using **Chrome DevTools MCP** (console/network sanity).

## Odoo implementation best practices
### ORM & correctness
- Prefer ORM over SQL; if SQL is unavoidable, parameterize and document why.
- Use `api.constrains`, `api.depends`, and computed/stored fields appropriately.
- Avoid side effects in compute methods; avoid writes inside computes.
- Use `sudo()` only when required; keep it scoped and justified.
- Keep business logic in models (not views/wizards); keep controllers thin.

### Security & access control
- Add/adjust security in `security/ir.model.access.csv` and (when needed) record rules.
- Never rely on UI hiding for security; enforce access in server-side code.
- Validate user input (especially wizards/controllers) and raise `ValidationError` / `UserError`.

### Data, upgrades, migrations
- Put demo/sample data in `data/` as XML/CSV with stable XML IDs.
- Never break upgrades: keep field renames/moves explicit (use `oldname` patterns or migration steps when needed).
- Use module hooks (`post_init_hook`, `uninstall_hook`) only when truly necessary; make them idempotent.

### Views & UX
- Keep views minimal; reuse inherited views rather than duplicating.
- Ensure all new fields appear where users need them; add help/tooltips for non-obvious fields.
- Respect multi-company and access rights (don’t assume a single company).

### Logging & performance
- Use `_logger` for meaningful operational logs (avoid noisy logs).
- Batch ORM operations when possible; avoid N+1 queries in loops.

## Testing requirements
### Automated (Odoo tests)
- Add tests for non-trivial logic: constraints, state transitions, wizards, and security.
- Place tests under `glucose_pumps_demo/tests/` and use `odoo.tests.common.TransactionCase` (or `SavepointCase` when appropriate).

Run tests in Docker (example):
- `docker exec -e ODOO_RC=/etc/odoo/odoo.conf odoo18-app odoo -c /etc/odoo/odoo.conf -d odoo --test-enable -i glucose_pumps_demo --stop-after-init`

### Manual (Chrome DevTools MCP)
Use Chrome DevTools MCP to validate UI pages/flows:

1. Open the login page and ensure it renders:
   - Navigate to `http://localhost:8069/web/login`
2. Log in (use configured credentials for the environment).
3. Navigate to the relevant menus/views you changed.
4. Validate DevTools:
   - **Console**: no uncaught errors.
   - **Network**: no failing XHR/fetch requests (4xx/5xx), especially on view load and button actions.
   - **Performance sanity** (optional): no obvious request storms/N+1 patterns.

## Required install/upgrade + “instance loaded” verification
### Upgrade/install the addon
Pick one:

- Upgrade existing DB/module:
  - `docker exec -e ODOO_RC=/etc/odoo/odoo.conf odoo18-app odoo -c /etc/odoo/odoo.conf -d odoo -u glucose_pumps_demo --stop-after-init`
- Install into a fresh DB (only when appropriate):
  - `docker exec -e ODOO_RC=/etc/odoo/odoo.conf odoo18-app odoo -c /etc/odoo/odoo.conf -d odoo -i glucose_pumps_demo --stop-after-init`

### Confirm the instance is loaded
- HTTP check:
  - `curl -I http://localhost:8069/web/login`
- Log sanity (no tracebacks during module load/upgrade):
  - `docker compose logs odoo --tail=200 | grep -iE "traceback|error"`

Only then can you state the task is complete.

## Quick runbook
- Start stack: `docker compose up -d`
- Watch logs: `docker compose logs -f odoo`
- Restart Odoo (after changes if needed): `docker compose restart odoo`

## Output expectations for completed tasks
When finishing a task, report these explicitly:
- What changed (files + high-level behavior)
- What command was run to install/upgrade (`-u`/`-i`)
- Evidence the instance loaded (HTTP check + no tracebacks)
- MCP verification summary (console/network results)
