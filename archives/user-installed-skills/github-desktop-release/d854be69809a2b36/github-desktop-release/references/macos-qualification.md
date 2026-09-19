# macOS qualification

Use this branch only when the release profile requests macOS. Derive commands and package formats from the frozen repository; do not copy Windows, NSIS, or Electron assumptions into this adapter.

## Freeze platform facts

- Requested architecture: arm64, x64, or universal, with exact expected machine type for every binary.
- Package formats and updater roles: DMG, ZIP, PKG, blockmap, update metadata, or another explicitly supported set.
- Runner image, Xcode/Command Line Tools, language runtime, package manager, native/vendor inputs, and signing/notarization policy.
- Bundle identifier, version/build number comparison, entitlements, hardened runtime, minimum OS, and expected application bundle path.

## Qualification sequence

1. Checkout the frozen SHA and verify the declared runner/toolchain before install or build.
2. Run the locked project install and package entrypoint. Prove native/vendor sources exist in the frozen tree or are fetched deterministically.
3. Verify every Mach-O architecture and the bundle/package identity before smoke testing.
4. Mount the DMG or inspect the package, launch the packaged application where the runner supports it, capture termination and unexpected dialog/crash evidence, then eject/clean the mounted image.
5. Verify signing with platform tools. Record whether the app is unsigned, ad-hoc, Developer ID signed, or another explicit state. Ad-hoc and Developer ID are distinct facts.
6. Verify notarization and stapling when required. When absent by policy, record Gatekeeper/distribution impact instead of implying success.
7. Record independent receipts for package, mount, launch, architecture, signing, notarization, native/vendor smoke, and updater compatibility as required by the project profile.

## Common failure boundaries

- A successful DMG/ZIP build is not launch, signing, notarization, or public Release qualification.
- A package built for the wrong architecture cannot be rescued by renaming the asset.
- Missing vendored native sources require a deterministic source fix before another costly run.
- Updater assets must match the updater implementation; do not publish a ZIP or metadata file merely because the packager emitted it.
