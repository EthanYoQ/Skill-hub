# Release contract

The release contract is immutable input frozen before qualification, not a retrospective report. It binds source, platform runs, toolchains, exact assets, acceptance meaning, and promotion policy so later stages cannot rebuild or reinterpret the release.

## Minimal shape

```json
{
  "schemaVersion": 1,
  "repository": "owner/repo",
  "profileSha256": "64-lowercase-hex",
  "frozen": {
    "commit": "40-character-lowercase-sha",
    "tag": "vX.Y.Z",
    "version": "X.Y.Z",
    "requiredPlatforms": ["windows", "macos"],
    "platforms": {
      "windows": {
        "workflow": ".github/workflows/qualify-windows.yml",
        "runner": { "expectedLabel": "windows-2022", "actualImageVersion": "captured-before-install" },
        "appToolchain": { "source": "committed project contract" },
        "artifactName": "qualified-windows",
        "acceptanceProfile": "profile-defined exact receipt set"
      },
      "macos": {
        "workflow": ".github/workflows/qualify-macos.yml",
        "runner": { "expectedLabel": "macos-14", "actualImageVersion": "captured-before-install" },
        "appToolchain": { "source": "committed project contract" },
        "artifactName": "qualified-macos",
        "acceptanceProfile": "profile-defined exact receipt set"
      }
    },
    "releaseAssetSet": [
      { "name": "App-Setup-X.Y.Z.exe", "platform": "windows", "role": "installer" },
      { "name": "App-X.Y.Z-arm64.dmg", "platform": "macos", "role": "installer" }
    ],
    "promotion": {
      "workflow": ".github/workflows/publish-verified-release.yml",
      "artifactSelection": "workflow-run-attempt-artifact-id",
      "releaseChannel": { "draft": false, "prerelease": false, "expectedLatest": true }
    }
  }
}
```

Field names may follow an existing repository schema, but the semantic boundaries cannot be omitted or reinterpreted during promotion.

## Freeze rules

- Use a full commit SHA, never a branch, short SHA, or later default-branch tip. Promotion must directly prove the qualified SHA satisfies the repository's ancestry policy.
- Generate and hash the contract before install, build, or acceptance. Verify dispatch inputs, checkout, runner image, application runtime, package manager, and tool versions against it.
- Treat the promotion verifier runtime as separate from every application toolchain.
- List exact requested platforms, architectures, workflows, artifact names, receipt paths, signing/notarization policies, release assets, retention, and channel expectations.
- Require signing evidence for every platform. When unsigned or unnotarized delivery is allowed, bind the validation result and non-empty unsigned distribution impact to the contract and release notes.
- Select cross-run artifacts by workflow, run ID, attempt, and artifact ID. A matching name from another run is not identity.
- Keep binary assets on raw SHA-256. Eligible UTF-8 text may add newline-canonical SHA-256 while retaining its raw hash.
- Link every platform ledger to the same contract/profile hashes. A contract linked to a run is immutable.
- A product SHA, version/tag, runner/toolchain, asset set, acceptance meaning, signing policy, or profile change creates a new contract and requires the affected formal qualification again.
- A trusted verifier-only correction may reuse already qualified artifacts only after complete real-receipt replay proves their contract, raw bytes, and acceptance facts remain unchanged.

## Promotion validation

Before write permission is granted, verify:

1. every required platform run succeeded with the same frozen head SHA and contract meaning;
2. each workflow/run/attempt/artifact ID is unique, unexpired, and belongs to the expected platform;
3. contracts, ledgers, manifests, checksums, receipts, signing/notarization disclosures, and artifact raw bytes agree;
4. the exact aggregated release asset set contains no missing, duplicate, or extra file;
5. tag, draft, channel policy, assets, and existing remote state can enter the GitHub Release state machine safely.

Any mismatch stops in read-only verification. Do not edit the contract to fit reality, substitute a same-named artifact, or rebuild during promotion.
