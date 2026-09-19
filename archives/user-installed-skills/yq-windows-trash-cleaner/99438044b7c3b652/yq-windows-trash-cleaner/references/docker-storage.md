# Docker Desktop storage guide

## Inventory first

Capture `docker system df -v`, all containers including stopped ones, image references, builder/cache state, volume names/mountpoints/labels, and the Docker Desktop VHDX file size and allocated size. If the engine is stopped, report that logical inventory is unavailable; do not start an auto-restarting container fleet merely to obtain it without considering impact.

## Safe boundaries

- `docker system prune -a` removes unused containers, networks, images, and build cache but not volumes unless `--volumes` is supplied. Preview the affected inventory and require approval.
- Never infer that “dangling” or “unmounted” means disposable.
- Inspect volume contents/labels and search Compose files, backup scripts, and historical container mounts.
- Treat database, restore, evidence, benchmark, and unknown volumes as retained.
- Builder state can be rebuildable but may make future builds slow; report that tradeoff.

## VHDX compaction

Deleting Docker objects reduces logical usage but may not shrink the host VHDX. Compaction requires all Docker/WSL consumers stopped and the VHDX unmounted. Record the VHDX length and allocated size before/after. Abort if the file is in use, the engine cannot be inventoried, or administrator access is unavailable.

Compaction is not a substitute for object review, and VHDX apparent free space is not a guaranteed reclaim amount.
