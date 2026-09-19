# Cleanup classification

## Usually safe after exact verification

- build outputs with a documented rebuild command;
- package-manager download caches;
- application temporary directories whose owner is stopped;
- clean, registered, merged Git worktrees removed with Git;
- Docker build cache and unreferenced images explicitly listed and approved.

## Conditional review

- old backups where retention and recovery points are understood;
- Codex sessions and transcripts;
- inactive containers or images tied to reproducibility;
- anonymous Docker volumes with unknown content;
- database logs requiring transactional retention;
- crash dumps or diagnostic evidence;
- model/browser/download caches that are expensive to recreate.

## Keep by default

- source trees, uncommitted/untracked work, active worktrees;
- databases and restore/evidence volumes;
- current sessions and task artifacts;
- secrets, credentials, configuration, license files;
- system-managed files and directories.

## Deletion gates

For every approved target verify:

1. literal resolved path or semantic object ID;
2. expected owner and action type;
3. no reparse-point escape;
4. current size/hash or other drift precondition;
5. application/process quiescence when required;
6. recovery or regeneration method;
7. explicit candidate ID approval.

Measure volume free bytes before and after. Sparse files, deduplication, hard links, compression, and filesystem allocation mean candidate sizes may not equal released bytes.
