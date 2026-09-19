#!/usr/bin/env node

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  assertDefaultBranchAncestry,
  assertAcceptanceReceipt,
  assertAuthoritativeReadback,
  assertContractBindings,
  assertLedgerSigning,
  assertQualificationRun,
  assertSigningDisclosure,
  assertSigningReceipt,
  assertUploadedAssetReadback,
  boundedAuthoritativeReadback,
  completionClaims,
  decideSafeResume,
  parseQualificationRuns,
  parseSigningReceiptBytes,
  selectQualificationArtifact,
  validatePromotionProfile,
  verifyExtractedQualification,
  verifyManifestIndex,
} from "./github-desktop-promotion.mjs";

const sha = "a".repeat(40);
const digestA = "1".repeat(64);
const digestB = "2".repeat(64);
const digestC = "3".repeat(64);
const contractDigest = "4".repeat(64);
const signingDigest = "5".repeat(64);
const profileDigest = "6".repeat(64);

function rejects(action, pattern) {
  assert.throws(action, pattern);
}

const profileFixture = {
  schemaVersion: 1,
  provider: "github-actions",
  artifactSelection: "workflow-run-attempt-artifact-id",
  platforms: {
    windows: {
      qualificationWorkflow: ".github/workflows/qualify-windows.yml",
      artifactName: "qualified-windows",
      architectures: ["x64"],
      retentionDays: 14,
      acceptanceReceipts: ["acceptance/signing.json"],
      signingPolicy: { mode: "allow-unsigned-with-disclosure", disclosureRequired: true },
    },
  },
  releaseAssets: [{ name: "App-{version}.exe", platform: "windows", role: "installer" }],
  promotion: { workflow: ".github/workflows/promote.yml", finalState: "published" },
  releaseChannel: { draft: false, prerelease: false, expectedLatest: true },
  retryPolicy: { maxConsecutiveFailuresPerStage: 2 },
  hashPolicy: { binary: "raw-sha256", text: "raw-plus-newline-canonical-sha256" },
};
assert.equal(validatePromotionProfile(profileFixture), profileFixture);
rejects(() => validatePromotionProfile({ ...profileFixture, artifactSelection: "name" }), /artifactSelection must equal/u);

const mapping = parseQualificationRuns(JSON.stringify({
  windows: { runId: 101, attempt: 2, artifactId: 9001 },
  macos: { runId: 102, attempt: 1, artifactId: 9002 },
}), ["windows", "macos"]);
assert.deepEqual(mapping.windows, { runId: 101, attempt: 2, artifactId: 9001 });
rejects(() => parseQualificationRuns(JSON.stringify({ windows: mapping.windows }), ["windows", "macos"]), /keys must be exactly/u);
rejects(() => parseQualificationRuns(JSON.stringify({ windows: { runId: 101, attempt: 2 } }), ["windows"]), /artifactId/u);

const run = {
  head_sha: sha,
  run_attempt: 2,
  status: "completed",
  conclusion: "success",
  path: ".github/workflows/qualify-windows.yml@refs/heads/main",
};
assert.doesNotThrow(() => assertQualificationRun({ run, expectedSha: sha, expectedAttempt: 2, expectedWorkflow: ".github/workflows/qualify-windows.yml" }));
rejects(() => assertQualificationRun({ run: { ...run, head_sha: "b".repeat(40) }, expectedSha: sha, expectedAttempt: 2, expectedWorkflow: ".github/workflows/qualify-windows.yml" }), /SHA mismatch/u);
rejects(() => assertQualificationRun({ run, expectedSha: sha, expectedAttempt: 1, expectedWorkflow: ".github/workflows/qualify-windows.yml" }), /attempt mismatch/u);
assert.doesNotThrow(() => assertDefaultBranchAncestry({ status: "ahead", merge_base_commit: { sha } }, sha));
rejects(() => assertDefaultBranchAncestry({ status: "diverged", merge_base_commit: { sha } }, sha), /not an ancestor/u);

const artifact = {
  id: 9001,
  name: "qualified-windows",
  expired: false,
  workflow_run: { id: 101, head_sha: sha },
};
assert.equal(selectQualificationArtifact({ artifacts: [artifact], artifactId: 9001, expectedName: "qualified-windows", runId: 101, expectedSha: sha }), artifact);
rejects(() => selectQualificationArtifact({ artifacts: [artifact], artifactId: 9001, expectedName: "same-name-is-not-identity", runId: 101, expectedSha: sha }), /name mismatch/u);
rejects(() => selectQualificationArtifact({ artifacts: [{ ...artifact, workflow_run: { id: 999, head_sha: sha } }], artifactId: 9001, expectedName: "qualified-windows", runId: 101, expectedSha: sha }), /run identity/u);

const manifest = {
  schemaVersion: 2,
  releaseCreated: false,
  commit: sha,
  contractRawBytesSha256: contractDigest,
  profileRawBytesSha256: profileDigest,
  artifacts: [{ path: "release-bundle/App.exe", rawBytesSha256: digestA }],
  evidence: [
    { path: "run-ledger.json", rawBytesSha256: digestB },
    { path: "release-contract.json", rawBytesSha256: contractDigest },
    { path: "acceptance/signing.json", rawBytesSha256: signingDigest },
  ],
  signing: {
    status: "unsigned",
    validationResult: "signature absent as expected",
    unsignedDistributionImpact: "operating system warning is expected",
    evidencePath: "acceptance/signing.json",
  },
};
const checksumText = `${signingDigest}  acceptance/signing.json\n${digestC}  manifest.json\n${contractDigest}  release-contract.json\n${digestA}  release-bundle/App.exe\n${digestB}  run-ledger.json\n`;
const actualFiles = ["SHA256SUMS.txt", "acceptance/signing.json", "manifest.json", "release-contract.json", "release-bundle/App.exe", "run-ledger.json"];
const actualDigests = new Map([
  ["acceptance/signing.json", signingDigest],
  ["release-bundle/app.exe", digestA],
  ["release-contract.json", contractDigest],
  ["run-ledger.json", digestB],
  ["manifest.json", digestC],
]);
const manifestIndex = verifyManifestIndex({ manifest, checksumText, actualFiles, actualDigests, expectedSha: sha });
const ledger = { contractRawBytesSha256: contractDigest, profileRawBytesSha256: profileDigest };
assert.deepEqual(assertContractBindings({ manifest, manifestRecords: manifestIndex.records, ledger, profileRawBytesSha256: profileDigest }), {
  contractRawBytesSha256: contractDigest,
  profileRawBytesSha256: profileDigest,
});
rejects(() => assertContractBindings({ manifest, manifestRecords: manifestIndex.records, ledger, profileRawBytesSha256: "7".repeat(64) }), /current release profile/u);
rejects(() => assertContractBindings({ manifest, manifestRecords: manifestIndex.records, ledger, profileRawBytesSha256: profileDigest, previousBindings: { contractRawBytesSha256: "8".repeat(64), profileRawBytesSha256: profileDigest } }), /required platforms/u);
assert.deepEqual(assertSigningDisclosure(manifest, { mode: "allow-unsigned-with-disclosure" }, manifestIndex.records), {
  status: "unsigned",
  validationResult: "signature absent as expected",
  unsignedDistributionImpact: "operating system warning is expected",
});
rejects(() => assertSigningDisclosure(manifest, { mode: "required" }), /requires a signed artifact/u);
rejects(() => assertSigningDisclosure({ ...manifest, signing: { ...manifest.signing, evidencePath: "acceptance/missing.json" } }, { mode: "allow-unsigned-with-disclosure" }, manifestIndex.records), /not hash-bound/u);
const receiptObject = { accepted: true, observations: ["direct signature observation"], status: "unsigned", validationResult: "signature absent as expected", unsignedDistributionImpact: "operating system warning is expected" };
assert.equal(assertAcceptanceReceipt(receiptObject, "windows", "acceptance/signing.json"), receiptObject);
rejects(() => assertAcceptanceReceipt({ ...receiptObject, accepted: false }, "windows", "acceptance/signing.json"), /accepted=true/u);
assert.equal(assertSigningReceipt(receiptObject, manifest.signing), receiptObject);
rejects(() => assertSigningReceipt({ ...receiptObject, validationResult: "different" }, manifest.signing), /validationResult/u);
const bom = Buffer.from([0xef, 0xbb, 0xbf]);
const receiptJsonBytes = Buffer.from(JSON.stringify(receiptObject), "utf8");
assert.equal(parseSigningReceiptBytes(Buffer.concat([bom, receiptJsonBytes])).accepted, true);
rejects(() => parseSigningReceiptBytes(Buffer.concat([bom, bom, receiptJsonBytes])), /duplicate or misplaced/u);
const ledgerSigning = { ...manifest.signing };
assert.doesNotThrow(() => assertLedgerSigning(ledgerSigning, manifest.signing));
rejects(() => assertLedgerSigning(undefined, manifest.signing), /binding is missing/u);
rejects(() => assertLedgerSigning({ ...ledgerSigning, status: "signed" }, manifest.signing), /status/u);
rejects(() => verifyManifestIndex({ manifest, checksumText, actualFiles: [...actualFiles, "extra.txt"], actualDigests, expectedSha: sha }), /file set is not exact/u);
rejects(() => verifyManifestIndex({ manifest, checksumText, actualFiles, actualDigests: new Map(actualDigests).set("release-bundle/app.exe", "4".repeat(64)), expectedSha: sha }), /raw byte digest mismatch/u);

const localAssets = new Map([
  ["app.exe", { name: "App.exe", size: 10, sha256: digestA }],
  ["app.dmg", { name: "App.dmg", size: 20, sha256: digestB }],
]);
const title = "v1.0.0";
const body = `Qualified desktop release ${title}`;
assert.deepEqual(
  decideSafeResume({ tagSha: null, expectedSha: sha, expectedTag: title, release: null, expectedTitle: title, expectedBody: body, localAssets }),
  { createTag: true, createDraft: true, upload: ["app.exe", "app.dmg"] },
);
const partialDraft = {
  tag_name: title,
  name: title,
  body,
  draft: true,
  assets: [{ name: "App.exe", size: 10, digest: `sha256:${digestA}`, state: "uploaded" }],
};
assert.deepEqual(
  decideSafeResume({ tagSha: sha, expectedSha: sha, expectedTag: title, release: partialDraft, expectedTitle: title, expectedBody: body, localAssets }),
  { createTag: false, createDraft: false, alreadyPublished: false, upload: ["App.dmg"] },
);
rejects(() => decideSafeResume({ tagSha: "b".repeat(40), expectedSha: sha, expectedTag: title, release: partialDraft, expectedTitle: title, expectedBody: body, localAssets }), /different commit/u);
rejects(() => decideSafeResume({ tagSha: sha, expectedSha: sha, expectedTag: title, release: { ...partialDraft, assets: [{ name: "App.exe", size: 11, digest: `sha256:${digestA}`, state: "uploaded" }] }, expectedTitle: title, expectedBody: body, localAssets }), /does not match local bytes/u);

const published = {
  id: 77,
  tag_name: title,
  name: title,
  body,
  draft: false,
  prerelease: false,
  assets: [
    { name: "App.exe", size: 10, digest: `sha256:${digestA}`, state: "uploaded" },
    { name: "App.dmg", size: 20, digest: `sha256:${digestB}`, state: "uploaded" },
  ],
};
assert.doesNotThrow(() => assertAuthoritativeReadback({
  release: published,
  tagSha: sha,
  expectedSha: sha,
  expectedTitle: title,
  expectedBody: body,
  localAssets,
  channel: { draft: false, prerelease: false, expectedLatest: true },
  latestReleaseId: 77,
}));
rejects(() => assertAuthoritativeReadback({
  release: published,
  tagSha: sha,
  expectedSha: sha,
  expectedTitle: title,
  expectedBody: body,
  localAssets,
  channel: { draft: false, prerelease: false, expectedLatest: false },
  latestReleaseId: 77,
}), /latest-release policy mismatch/u);

let delayedReads = 0;
const delayedValue = await boundedAuthoritativeReadback({
  label: "offline delayed visibility",
  read: async () => ({ visible: ++delayedReads >= 3 }),
  assert: (value) => { if (!value.visible) throw new Error("not visible yet"); },
  sleep: async () => {},
  delays: [1, 2, 3, 4],
});
assert.equal(delayedValue.visible, true);
assert.equal(delayedReads, 3);
await assert.rejects(() => boundedAuthoritativeReadback({
  label: "offline exhausted visibility",
  read: async () => null,
  assert: () => { throw new Error("still absent"); },
  sleep: async () => {},
  delays: [1, 2],
}), /exhausted after 3 attempts/u);
rejects(() => assertUploadedAssetReadback({ assets: [{ name: "App.exe", size: 10, state: "uploaded" }] }, localAssets.get("app.exe")), /digest is missing/u);
assert.deepEqual(completionClaims({ draft: true }), { draftVerified: true, publicationVerified: false });
assert.deepEqual(completionClaims({ draft: false }), { draftVerified: false, publicationVerified: true });

function hashBytes(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

async function writeSyntheticQualification(root, { platform, mapping, assetName, assetBytes, includeBom, receiptAccepted = true, ledgerSigningMode = "valid" }) {
  await mkdir(join(root, "acceptance"), { recursive: true });
  await mkdir(join(root, "release-bundle"), { recursive: true });
  const contractBytes = Buffer.from('{"schemaVersion":2,"scope":"windows+macos"}\n', "utf8");
  const fixtureReceipt = { ...receiptObject, accepted: receiptAccepted, platform };
  const signingBytes = Buffer.concat([includeBom ? bom : Buffer.alloc(0), Buffer.from(JSON.stringify(fixtureReceipt), "utf8")]);
  const signingBinding = {
    status: fixtureReceipt.status,
    validationResult: fixtureReceipt.validationResult,
    unsignedDistributionImpact: fixtureReceipt.unsignedDistributionImpact,
    evidencePath: "acceptance/signing.json",
  };
  const ledgerValue = {
    schemaVersion: 2,
    runId: mapping.runId,
    runAttempt: mapping.attempt,
    qualifiedCommit: sha,
    contractRawBytesSha256: hashBytes(contractBytes),
    profileRawBytesSha256: profileDigest,
  };
  if (ledgerSigningMode === "valid") ledgerValue.signing = signingBinding;
  if (ledgerSigningMode === "conflict") ledgerValue.signing = { ...signingBinding, validationResult: "conflicting ledger value" };
  const ledgerBytes = Buffer.from(`${JSON.stringify(ledgerValue)}\n`, "utf8");
  await writeFile(join(root, "release-contract.json"), contractBytes);
  await writeFile(join(root, "run-ledger.json"), ledgerBytes);
  await writeFile(join(root, "acceptance", "signing.json"), signingBytes);
  await writeFile(join(root, "release-bundle", assetName), assetBytes);
  const manifestValue = {
    schemaVersion: 2,
    releaseCreated: false,
    commit: sha,
    contractRawBytesSha256: hashBytes(contractBytes),
    profileRawBytesSha256: profileDigest,
    artifacts: [{ path: `release-bundle/${assetName}`, rawBytesSha256: hashBytes(assetBytes) }],
    evidence: [
      { path: "release-contract.json", rawBytesSha256: hashBytes(contractBytes) },
      { path: "run-ledger.json", rawBytesSha256: hashBytes(ledgerBytes) },
      { path: "acceptance/signing.json", rawBytesSha256: hashBytes(signingBytes) },
    ],
    signing: signingBinding,
  };
  const manifestBytes = Buffer.from(`${JSON.stringify(manifestValue)}\n`, "utf8");
  await writeFile(join(root, "manifest.json"), manifestBytes);
  const checksumEntries = [
    ["acceptance/signing.json", signingBytes],
    ["manifest.json", manifestBytes],
    ["release-contract.json", contractBytes],
    [`release-bundle/${assetName}`, assetBytes],
    ["run-ledger.json", ledgerBytes],
  ].map(([name, bytes]) => `${hashBytes(bytes)}  ${name}`).sort();
  await writeFile(join(root, "SHA256SUMS.txt"), `${checksumEntries.join("\n")}\n`, "utf8");
}

const integrationRoot = await mkdtemp(join(tmpdir(), "promotion-consumer-test-"));
try {
  const releaseAssetPolicy = [
    { platform: "windows", name: "App-{version}.exe" },
    { platform: "macos", name: "App-{version}.dmg" },
  ];
  const platformCases = [
    { platform: "windows", mapping: { runId: 501, attempt: 2, artifactId: 7001 }, assetName: "App-1.0.0.exe", artifactName: "qualified-windows", bytes: Buffer.from([0x4d, 0x5a, 0x01]), includeBom: true },
    { platform: "macos", mapping: { runId: 502, attempt: 1, artifactId: 7002 }, assetName: "App-1.0.0.dmg", artifactName: "qualified-macos", bytes: Buffer.from([0x78, 0x61, 0x72, 0x21]), includeBom: false },
  ];
  let integrationBindings = null;
  const aggregateAssets = new Map();
  for (const fixture of platformCases) {
    const root = join(integrationRoot, fixture.platform);
    await writeSyntheticQualification(root, { platform: fixture.platform, mapping: fixture.mapping, assetName: fixture.assetName, assetBytes: fixture.bytes, includeBom: fixture.includeBom });
    const verified = await verifyExtractedQualification({
      root,
      platform: fixture.platform,
      policy: { signingPolicy: { mode: "allow-unsigned-with-disclosure" }, acceptanceReceipts: ["acceptance/signing.json"] },
      releaseAssetPolicy,
      version: "1.0.0",
      expectedSha: sha,
      mapping: fixture.mapping,
      artifact: { name: fixture.artifactName },
      profileRawBytesSha256: profileDigest,
      previousBindings: integrationBindings,
    });
    integrationBindings = verified.bindings;
    for (const asset of verified.assets) aggregateAssets.set(asset.name, asset.sha256);
  }
  assert.deepEqual(integrationBindings, { contractRawBytesSha256: hashBytes(Buffer.from('{"schemaVersion":2,"scope":"windows+macos"}\n', "utf8")), profileRawBytesSha256: profileDigest });
  assert.deepEqual([...aggregateAssets.keys()].sort(), ["App-1.0.0.dmg", "App-1.0.0.exe"]);
  const windowsCase = platformCases[0];
  const baseConsumer = {
    platform: "windows",
    releaseAssetPolicy,
    version: "1.0.0",
    expectedSha: sha,
    mapping: windowsCase.mapping,
    artifact: { name: windowsCase.artifactName },
    profileRawBytesSha256: profileDigest,
  };
  await assert.rejects(() => verifyExtractedQualification({
    ...baseConsumer,
    root: join(integrationRoot, "windows"),
    policy: { signingPolicy: { mode: "allow-unsigned-with-disclosure" }, acceptanceReceipts: ["acceptance/signing.json", "acceptance/missing.json"] },
  }), /required receipt is not hash-bound/u);

  for (const negative of [
    { name: "rejected", receiptAccepted: false, ledgerSigningMode: "valid", error: /accepted=true/u },
    { name: "ledger-missing", receiptAccepted: true, ledgerSigningMode: "missing", error: /binding is missing/u },
    { name: "ledger-conflict", receiptAccepted: true, ledgerSigningMode: "conflict", error: /validationResult/u },
  ]) {
    const root = join(integrationRoot, negative.name);
    await writeSyntheticQualification(root, { platform: "windows", mapping: windowsCase.mapping, assetName: windowsCase.assetName, assetBytes: windowsCase.bytes, includeBom: false, receiptAccepted: negative.receiptAccepted, ledgerSigningMode: negative.ledgerSigningMode });
    await assert.rejects(() => verifyExtractedQualification({
      ...baseConsumer,
      root,
      policy: { signingPolicy: { mode: "allow-unsigned-with-disclosure" }, acceptanceReceipts: ["acceptance/signing.json"] },
    }), negative.error);
  }
} finally {
  await rm(integrationRoot, { recursive: true, force: true });
}

const workflow = await readFile(new URL("../assets/github-desktop-release-promotion.yml", import.meta.url), "utf8");
assert.match(workflow, /copy <github-desktop-release-skill-root>\/scripts\/github-desktop-promotion\.mjs/u);
assert.match(workflow, /\.release\/scripts\/github-desktop-promotion\.mjs/u);
assert.match(workflow, /validate-release-profile\.mjs/u);
assert.match(workflow, /Vendor both Skill scripts/u);
assert.match(workflow, /--version "\$RELEASE_VERSION"/u);

process.stdout.write('{"passed":true,"checks":"profile-validator,run-mapping,same-sha,contract-profile-binding,required-receipt-set,receipt-envelope,signing-receipt-consistency,ledger-signing-binding,single-bom,default-branch-ancestry,attempt,artifact-id-name,manifest-exact-set,raw-sha,two-platform-consumer-integration,safe-resume,bounded-readback,digest-required,draft-publication-boundary,channel-readback,vendored-workflow"}\n');
