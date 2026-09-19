# Memory diagnosis decision guide

## Evidence hierarchy

1. A repeatable workload causes the same within-boot growth pattern.
2. Two component on/off cycles suppress and restore that growth.
3. Pool tags and filter/driver ownership support the same component.
4. Restart resets the accumulated pool.
5. Timing alone or one tag-name association is only a hypothesis.

## Interpret common observations

| Observation | Interpretation |
|---|---|
| High process private bytes and stable kernel pool | Application workload, not kernel leak |
| Paged/nonpaged pool grows monotonically after workload ends | Kernel-lifetime retention or leak candidate |
| `FMfn` + `File` + `IoFE` grow together | File-object/filter-manager amplification; identify the active filter chain before blaming one driver |
| `SQSF` grows | Storage QoS activity is present; not sufficient alone to disable `storqosflt` |
| `EtwB` grows | Inspect ETW sessions, buffer mode, ownership, and whether buffers later release |
| Restart returns pool to baseline | Confirms kernel-lifetime accumulation; does not prove origin |
| Shutdown/power-on preserves high pool while Restart clears it | Fast Startup or sleep may be preserving kernel state |

## Coverage rules

- Group by exact boot time.
- Measure first/last sample span and maximum sample gap.
- A 24/48-hour claim requires coverage near that span, not merely current uptime.
- Include a representative long workload and a post-workload observation window.
- Treat a large gap, monitor failure, or reboot as incomplete evidence.

Default warning thresholds for a 32 GB client are starting points, not universal facts: total pool 4 GB, file-family tags 1 GB, `SQSF` 256 MB, `EtwB` 1 GB. Adapt to hardware and baseline. Critical defaults may be twice the warning level.

## Minimal adjustment order

1. Reduce optional login-start storms.
2. Delay optional indexers/updaters only when startup evidence supports it.
3. A/B optional services one at a time.
4. Update or repair the proven component.
5. Disable an optional filter/driver only with reproducible evidence, rollback, and functional testing.

Never use Defender, storage, network, audio, or graphics-driver disablement as an exploratory first step.
