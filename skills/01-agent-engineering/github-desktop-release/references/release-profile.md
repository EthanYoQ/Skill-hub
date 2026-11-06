# Project release profile

Keep cross-project procedure in the Skill and repository facts in one machine-readable profile. Prefer `.release/release-profile.json` unless the repository already owns another explicit path.

The profile defines stable project policy, not a release instance. The release contract freezes the current SHA, version, tag, runner image, toolchain, and run identities separately.

## Minimal shape

```json
{
  "schemaVersion": 1,
  "provider": "github-actions",
  "platforms": {
    "windows": {
      "qualificationWorkflow": ".github/workflows/qualify-windows.yml",
      "artifactName": "qualified-windows",
      "architectures": ["x64"],
      "retentionDays": 14,
      "acceptanceReceipts": [
        "acceptance/install.json",
        "acceptance/launch.json",
        "acceptance/quiet-window.json",
        "acceptance/error-dialogs.json",
        "acceptance/uninstall.json",
        "acceptance/packaged-smoke.json",
        "acceptance/signing.json"
      ],
      "signingPolicy": {
        "mode": "allow-unsigned-with-disclosure",
        "disclosureRequired": true
      }
    },
    "macos-arm64": {
      "qualificationWorkflow": ".github/workflows/qualify-macos-arm64.yml",
      "artifactName": "qualified-macos-arm64",
      "architectures": ["arm64"],
      "retentionDays": 14,
      "acceptanceReceipts": [
        "acceptance/package.json",
        "acceptance/mount.json",
        "acceptance/launch.json",
        "acceptance/architecture.json",
        "acceptance/signing.json",
        "acceptance/notarization.json"
      ],
      "signingPolicy": {
        "mode": "allow-unsigned-with-disclosure",
        "disclosureRequired": true
      }
    }
  },
  "releaseAssets": [
    { "name": "App-Setup-{version}-x64.exe", "platform": "windows", "role": "installer" },
    { "name": "App-mac-arm64-{version}.dmg", "platform": "macos-arm64", "role": "installer" }
  ],
  "promotion": {
    "workflow": ".github/workflows/publish-verified-release.yml",
    "finalState": "published"
  },
  "artifactSelection": "workflow-run-attempt-artifact-id",
  "releaseChannel": {
    "draft": false,
    "prerelease": false,
    "expectedLatest": true
  },
  "retryPolicy": {
    "maxConsecutiveFailuresPerStage": 2
  },
  "hashPolicy": {
    "binary": "raw-sha256",
    "text": "raw-plus-newline-canonical-sha256"
  }
}
```

## Rules

- List exact workflow paths, artifact names, receipt paths, platform architectures, release asset names, retention, release channel, and signing policies. Reject globs and ambiguous same-name artifacts.
- Keep project-specific receipt counts, workflow filenames, smoke commands, signing choices, and asset names here rather than in `SKILL.md`.
- The example Windows receipt set is the **standard** core: install, launch/packaged smoke, bounded quiet/error observation, uninstall, and signing. It is sufficient only while installer, upgrade, and native-ABI boundaries are unchanged.
- For deep Windows acceptance, use a separate committed profile (for example `release-profile.windows-deep.json`) that adds exact `acceptance/upgrade-data.json`, `acceptance/native-abi.json`, and any project-specific migration receipts. Select the profile before qualification; its raw hash binds every qualification and promotion run, so an undeclared deep receipt or a late profile edit is rejected.
- A profile may describe either tier, never an implicit mixture. Do not use a wildcard, an optional receipt, or an undeclared extra JSON file to make a deep check conditional.
- Use `{version}` only as an explicit asset-name placeholder; resolve it when freezing the release contract.
- Platform keys are qualification entities, not operating-system families: `windows`, `macos-arm64`, and `macos-x64`. A generic `macos` key is rejected so the two macOS architectures keep independent run identities, artifacts, and signing receipts. Add `macos-x64` as its own entity (own workflow, artifact name, and assets) when Intel is released.
- Each entity lists exactly one architecture: `windows` → `["x64"]`, `macos-arm64` → `["arm64"]`, `macos-x64` → `["x64"]`. Tokens are limited to ASCII letters, digits, dot, underscore, and hyphen; comparison is case-insensitive.
- Every macOS release asset name must contain `-mac-<arch>-` for its entity: `-mac-arm64-` for `macos-arm64` and `-mac-x64-` for `macos-x64` (for example `App-mac-arm64-{version}.dmg`). This is a naming requirement the project accepts by copying `validate-release-profile.mjs` verbatim: the copied validator rejects the profile otherwise, and the bundled macOS templates check the built asset names again. Rename the project's macOS assets rather than editing the copied script.
- Select artifacts by workflow, run ID, attempt, and artifact ID; an equal artifact name is not identity.
- Use a fixed `artifactName` per entity: `qualified-windows`, `qualified-macos-arm64`, and `qualified-macos-x64`. The bundled templates upload under exactly these names and fail closed when the profile differs. Do not append SHA, run ID, or attempt; promotion separately binds immutable workflow/run/attempt/artifact IDs.
- Point each entity's `qualificationWorkflow` at its own copy of the matching template (`electron-nsis-qualification.yml`, `macos-arm64-qualification.yml`, `macos-x64-qualification.yml`). The freeze script derives the running workflow path from `GITHUB_WORKFLOW_REF` and rejects a run whose path differs.
- Every qualification workflow must receive the same committed `profile_path`, hash its raw bytes before build, and carry that hash in the common contract, run ledger, and manifest.
- Keep `promotion.finalState` and `releaseChannel.draft` consistent: `draft` requires `draft: true`, while `published` requires `draft: false`.
- Interpret `expectedLatest` as project policy rather than a universal completion rule. It must be `false` for draft or prerelease channels.
- Keep each receipt path relative to its evidence root and reject traversal, absolute paths, ADS, trailing dot/space, case-insensitive collisions, and reparse-point escapes.
- Reject unknown fields at every object layer instead of silently accepting misspelled policy keys.
- Validate the profile before planning a cloud run. A missing or invalid profile is a planning blocker, not permission to infer defaults.
