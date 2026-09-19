#!/usr/bin/env node
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { validateReleaseProfile } from './validate-release-profile.mjs';
import { replayReleaseEvidence } from './replay-release-evidence.mjs';
import { classifyFailure } from './classify-actions-failure.mjs';

const profile = {
  schemaVersion: 1,
  provider: 'github-actions',
  platforms: {
    windows: {
      qualificationWorkflow: '.github/workflows/qualify-windows.yml',
      artifactName: 'qualified-windows',
      architectures: ['x64'],
      retentionDays: 14,
      acceptanceReceipts: ['acceptance/launch.json', 'acceptance/signing.json'],
      signingPolicy: { mode: 'allow-unsigned-with-disclosure', disclosureRequired: true }
    },
    macos: {
      qualificationWorkflow: '.github/workflows/qualify-macos.yml',
      artifactName: 'qualified-macos',
      architectures: ['arm64', 'x64'],
      retentionDays: 14,
      acceptanceReceipts: ['acceptance/launch.json', 'acceptance/signing.json'],
      signingPolicy: { mode: 'required', disclosureRequired: true }
    }
  },
  releaseAssets: [
    { name: 'App-Setup-{version}.exe', platform: 'windows', role: 'installer' },
    { name: 'App-{version}-arm64.dmg', platform: 'macos', role: 'installer' }
  ],
  promotion: { workflow: '.github/workflows/publish-release.yml', finalState: 'published' },
  artifactSelection: 'workflow-run-attempt-artifact-id',
  releaseChannel: { draft: false, prerelease: false, expectedLatest: true },
  retryPolicy: { maxConsecutiveFailuresPerStage: 2 },
  hashPolicy: { binary: 'raw-sha256', text: 'raw-plus-newline-canonical-sha256' }
};

assert.equal(validateReleaseProfile(profile).ok, true);
const draftProfile = structuredClone(profile);
draftProfile.promotion.finalState = 'draft';
draftProfile.releaseChannel.draft = true;
draftProfile.releaseChannel.expectedLatest = false;
assert.equal(validateReleaseProfile(draftProfile).ok, true);

const unsafe = structuredClone(profile);
unsafe.releaseAssets[0].name = '*.exe';
assert.equal(validateReleaseProfile(unsafe).ok, false);
const duplicate = structuredClone(profile);
duplicate.platforms.windows.acceptanceReceipts.push('ACCEPTANCE/launch.json');
assert.equal(validateReleaseProfile(duplicate).ok, false);
const trailingSegment = structuredClone(profile);
trailingSegment.platforms.windows.acceptanceReceipts[0] = 'acceptance./launch.json';
assert.equal(validateReleaseProfile(trailingSegment).ok, false);
assert.match(validateReleaseProfile(trailingSegment).errors.join('\n'), /trailing dot\/space/);

const unsafeArchitecture = structuredClone(profile);
unsafeArchitecture.platforms.windows.architectures = ['x64/../../escape'];
assert.equal(validateReleaseProfile(unsafeArchitecture).ok, false);
const duplicateArchitecture = structuredClone(profile);
duplicateArchitecture.platforms.macos.architectures.push('ARM64');
assert.equal(validateReleaseProfile(duplicateArchitecture).ok, false);

const unknownFieldCases = [
  ['profile', (candidate) => { candidate.providre = 'github-actions'; }],
  ['platform', (candidate) => { candidate.platforms.windows.artificatName = 'typo'; }],
  ['signing policy', (candidate) => { candidate.platforms.windows.signingPolicy.disclosureRequire = true; }],
  ['release asset', (candidate) => { candidate.releaseAssets[0].filename = 'typo'; }],
  ['promotion', (candidate) => { candidate.promotion.state = 'published'; }],
  ['release channel', (candidate) => { candidate.releaseChannel.latest = true; }],
  ['retry policy', (candidate) => { candidate.retryPolicy.maxFailures = 2; }],
  ['hash policy', (candidate) => { candidate.hashPolicy.binaryHash = 'raw-sha256'; }]
];
for (const [label, mutate] of unknownFieldCases) {
  const candidate = structuredClone(profile);
  mutate(candidate);
  const result = validateReleaseProfile(candidate);
  assert.equal(result.ok, false, `${label} unknown field must be rejected`);
  assert.match(result.errors.join('\n'), /unknown field/, `${label} must report unknown field`);
}

const contradictoryDraft = structuredClone(profile);
contradictoryDraft.releaseChannel.draft = true;
contradictoryDraft.releaseChannel.expectedLatest = false;
assert.equal(validateReleaseProfile(contradictoryDraft).ok, false);
assert.match(validateReleaseProfile(contradictoryDraft).errors.join('\n'), /finalState must equal draft/);
const contradictoryPublished = structuredClone(draftProfile);
contradictoryPublished.releaseChannel.draft = false;
assert.equal(validateReleaseProfile(contradictoryPublished).ok, false);
assert.match(validateReleaseProfile(contradictoryPublished).errors.join('\n'), /finalState must equal published/);
const latestPrerelease = structuredClone(profile);
latestPrerelease.releaseChannel.prerelease = true;
assert.equal(validateReleaseProfile(latestPrerelease).ok, false);
assert.match(validateReleaseProfile(latestPrerelease).errors.join('\n'), /expectedLatest must be false/);
const gateFailure = classifyFailure({
  stage: 'promotion-verify',
  failureSurface: 'verifier-rejected-known-good',
  evidenceBasis: ['Windows raw receipt and canonical hash match the frozen contract'],
  sameStageConsecutiveFailures: 2
});
assert.equal(gateFailure.classification, 'gate-false-positive');
assert.equal(gateFailure.rebuildDefault, false);
assert.equal(gateFailure.mustStop, true);
assert.equal(gateFailure.dispatchAllowed, false);

const container = await mkdtemp(path.join(os.tmpdir(), 'github-desktop-release-tools-'));
const root = path.join(container, 'evidence');
try {
  await mkdir(root, { recursive: true });
  for (const platform of ['windows', 'macos']) {
    const acceptanceRoot = path.join(root, platform, 'acceptance');
    await mkdir(acceptanceRoot, { recursive: true });
    const launch = JSON.stringify({ schemaVersion: 1, platform, accepted: true, observations: ['packaged app launched'], processObserved: true }, null, 2);
    const signing = JSON.stringify({
      schemaVersion: 1,
      platform,
      accepted: true,
      observations: ['signature policy evaluated'],
      status: platform === 'windows' ? 'unsigned' : 'signed',
      validationResult: platform === 'windows' ? 'signature absent as declared' : 'Developer ID verified',
      unsignedDistributionImpact: platform === 'windows' ? 'SmartScreen reputation warning may appear' : ''
    }, null, 2);
    const launchBytes = platform === 'windows' ? Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf]), Buffer.from(launch.replaceAll('\n', '\r\n'))]) : Buffer.from(launch);
    await writeFile(path.join(acceptanceRoot, 'launch.json'), launchBytes);
    await writeFile(path.join(acceptanceRoot, 'signing.json'), signing);
  }

  const replay = await replayReleaseEvidence(profile, root);
  assert.equal(replay.ok, true, JSON.stringify(replay.errors));
  assert.equal(replay.receipts.length, 4);
  assert.equal(replay.receipts.find((receipt) => receipt.platform === 'windows' && receipt.path.endsWith('launch.json')).utf8Bom, true);

  const rejectedPath = path.join(root, 'macos', 'acceptance', 'launch.json');
  await writeFile(rejectedPath, JSON.stringify({ platform: 'macos', accepted: false, observations: ['crash'], processObserved: false }));
  const rejected = await replayReleaseEvidence(profile, root);
  assert.equal(rejected.ok, false);
  assert.match(rejected.errors.join('\n'), /accepted=true/);

  const duplicateBomPath = path.join(root, 'windows', 'acceptance', 'launch.json');
  const duplicateBom = Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf, 0xef, 0xbb, 0xbf]), Buffer.from('{"accepted":true}')]);
  await writeFile(duplicateBomPath, duplicateBom);
  const duplicateBomReplay = await replayReleaseEvidence(profile, root);
  assert.equal(duplicateBomReplay.ok, false);
  assert.match(duplicateBomReplay.errors.join('\n'), /duplicate or misplaced UTF-8 BOM/);

  const outsideAcceptance = path.join(container, 'outside-acceptance');
  await mkdir(outsideAcceptance, { recursive: true });
  await writeFile(path.join(outsideAcceptance, 'launch.json'), JSON.stringify({
    platform: 'macos', accepted: true, observations: ['outside launch'], processObserved: true
  }));
  await writeFile(path.join(outsideAcceptance, 'signing.json'), JSON.stringify({
    platform: 'macos', accepted: true, observations: ['outside signature'], status: 'signed', validationResult: 'outside'
  }));
  const reparsePath = path.join(root, 'macos', 'acceptance');
  await rm(reparsePath, { recursive: true, force: true });
  let reparseCreated = false;
  try {
    await symlink(outsideAcceptance, reparsePath, process.platform === 'win32' ? 'junction' : 'dir');
    reparseCreated = true;
    const escapedReplay = await replayReleaseEvidence(profile, root);
    assert.equal(escapedReplay.ok, false);
    assert.match(escapedReplay.errors.join('\n'), /resolves outside evidence root through a symlink or junction/);
  } finally {
    if (reparseCreated) await rm(reparsePath, { recursive: true, force: true });
  }
  assert.equal((await readFile(path.join(outsideAcceptance, 'launch.json'), 'utf8')).includes('outside launch'), true);
} finally {
  await rm(container, { recursive: true, force: true });
}

process.stdout.write('{"passed":true,"checks":"profile-validation,unknown-fields,channel-consistency,architectures,path-safety,reparse-escape,case-collision,bom-crlf-replay,strict-single-bom,signing-envelope,negative-receipt,failure-classification,two-failure-stop"}\n');
