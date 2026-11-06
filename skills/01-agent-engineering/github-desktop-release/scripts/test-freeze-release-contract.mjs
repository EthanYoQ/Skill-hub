#!/usr/bin/env node
// freeze-release-contract.mjs 的离线测试：身份字段、跨平台 contract 逐字节一致、项目 adapter 参数与 fail-closed 分支。
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { freezeReleaseContract, parseArguments, workflowPathFromRef } from './freeze-release-contract.mjs';

const scriptPath = fileURLToPath(new URL('./freeze-release-contract.mjs', import.meta.url));
const sha = 'a'.repeat(40);
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');

function sampleProfile() {
  const receipts = ['acceptance/packaged-smoke.json', 'acceptance/signing.json'];
  const signingPolicy = { mode: 'allow-unsigned-with-disclosure', disclosureRequired: true };
  return {
    schemaVersion: 1,
    provider: 'github-actions',
    platforms: {
      windows: { qualificationWorkflow: '.github/workflows/qualify-windows.yml', artifactName: 'qualified-windows', architectures: ['x64'], retentionDays: 14, acceptanceReceipts: receipts, signingPolicy },
      'macos-arm64': { qualificationWorkflow: '.github/workflows/qualify-macos-arm64.yml', artifactName: 'qualified-macos-arm64', architectures: ['arm64'], retentionDays: 14, acceptanceReceipts: receipts, signingPolicy },
      'macos-x64': { qualificationWorkflow: '.github/workflows/qualify-macos-x64.yml', artifactName: 'qualified-macos-x64', architectures: ['x64'], retentionDays: 14, acceptanceReceipts: receipts, signingPolicy },
    },
    releaseAssets: [
      { name: 'App-Setup-{version}.exe', platform: 'windows', role: 'installer' },
      { name: 'latest.yml', platform: 'windows', role: 'update-metadata' },
      { name: 'App-mac-arm64-{version}.dmg', platform: 'macos-arm64', role: 'installer' },
      { name: 'App-mac-x64-{version}.dmg', platform: 'macos-x64', role: 'installer' },
    ],
    promotion: { workflow: '.github/workflows/publish-verified-release.yml', finalState: 'published' },
    artifactSelection: 'workflow-run-attempt-artifact-id',
    releaseChannel: { draft: false, prerelease: false, expectedLatest: true },
    retryPolicy: { maxConsecutiveFailuresPerStage: 2 },
    hashPolicy: { binary: 'raw-sha256', text: 'raw-plus-newline-canonical-sha256' },
  };
}

const root = await mkdtemp(path.join(os.tmpdir(), 'freeze-release-contract-'));
try {
  const workspace = path.join(root, 'workspace');
  await mkdir(path.join(workspace, '.release'), { recursive: true });
  const profileText = `${JSON.stringify(sampleProfile(), null, 2)}\n`;
  await writeFile(path.join(workspace, '.release', 'release-profile.json'), profileText, 'utf8');
  await writeFile(path.join(workspace, 'package.json'), '{"name":"app","version":"1.2.3"}\n', 'utf8');

  const base = (platform, output, overrides = {}) => ({
    repository: 'owner/app',
    'expected-sha': sha,
    tag: 'v1.2.3',
    version: '1.2.3',
    workspace,
    profile: '.release/release-profile.json',
    'output-root': path.join(root, output),
    platform,
    'run-id': '41',
    'run-attempt': '2',
    workflow: sampleProfile().platforms[platform].qualificationWorkflow,
    actor: 'octocat',
    event: 'workflow_dispatch',
    'started-at': '2026-01-01T00:00:00.000Z',
    ...overrides,
  });

  // 正向：三个资格实体各自的 ledger 身份，contract 逐字节相同并列出排序后的全部实体。
  const contractBytes = [];
  for (const [platform, architecture] of [['windows', 'x64'], ['macos-arm64', 'arm64'], ['macos-x64', 'x64']]) {
    const result = freezeReleaseContract(base(platform, platform));
    const contractRaw = await readFile(result.contractPath);
    const contract = JSON.parse(contractRaw.toString('utf8'));
    const ledger = JSON.parse(await readFile(result.ledgerPath, 'utf8'));
    assert.deepEqual(contract.frozen.qualificationEntities, ['macos-arm64', 'macos-x64', 'windows']);
    assert.equal(contract.repository, 'owner/app');
    assert.equal(contract.frozen.profilePath, '.release/release-profile.json');
    assert.equal(contract.frozen.profileRawBytesSha256, sha256(Buffer.from(profileText, 'utf8')));
    assert.equal(ledger.platform, platform);
    assert.equal(ledger.architecture, architecture);
    assert.equal(ledger.runId, 41);
    assert.equal(ledger.runAttempt, 2);
    assert.equal(ledger.workflow, sampleProfile().platforms[platform].qualificationWorkflow);
    assert.equal(ledger.repository, 'owner/app');
    assert.equal(ledger.releaseCreated, false);
    assert.equal(ledger.contractRawBytesSha256, sha256(contractRaw));
    assert.equal(ledger.profileRawBytesSha256, contract.frozen.profileRawBytesSha256);
    contractBytes.push(contractRaw.toString('hex'));
  }
  assert.equal(new Set(contractBytes).size, 1, 'every entity must freeze a byte-identical common contract');

  // GITHUB_WORKFLOW_REF 推导 workflow 路径，模板不必写死自身路径。
  assert.equal(workflowPathFromRef('owner/app/.github/workflows/qualify-windows.yml@refs/heads/main', 'owner/app'), '.github/workflows/qualify-windows.yml');
  const viaRef = base('windows', 'via-ref', { workflow: undefined, 'workflow-ref': 'owner/app/.github/workflows/qualify-windows.yml@refs/tags/v1.2.3' });
  delete viaRef.workflow;
  assert.equal(freezeReleaseContract(viaRef).ledger.workflow, '.github/workflows/qualify-windows.yml');
  assert.throws(() => workflowPathFromRef('other/app/.github/workflows/qualify-windows.yml@refs/heads/main', 'owner/app'), /must start with <repository>/);

  // 项目 adapter：tag 格式与版本号来源都是可选参数，给了就必须一致。
  assert.equal(freezeReleaseContract(base('windows', 'adapters', { 'tag-format': 'v{version}', 'version-file': 'package.json' })).contract.frozen.tag, 'v1.2.3');
  assert.equal(freezeReleaseContract(base('windows', 'free-tag', { tag: 'release-1.2.3' })).contract.frozen.tag, 'release-1.2.3');
  assert.throws(() => freezeReleaseContract(base('windows', 'bad-tag', { tag: 'release-1.2.3', 'tag-format': 'v{version}' })), /tag does not match --tag-format/);
  assert.throws(() => freezeReleaseContract(base('windows', 'bad-format', { 'tag-format': 'v1' })), /must contain \{version\}/);
  assert.throws(() => freezeReleaseContract(base('windows', 'bad-version', { version: '1.2.4', tag: 'v1.2.4', 'version-file': 'package.json' })), /does not match --version-file/);

  // fail closed：实体、workflow、事件、SHA、run 身份、参数形状、profile 路径与内容。
  const negatives = [
    [{ platform: 'macos' }, /supported qualification entity/],
    [{ platform: 'linux' }, /supported qualification entity/],
    [{ workflow: '.github/workflows/other.yml' }, /workflow does not match release profile/],
    [{ event: 'push' }, /workflow_dispatch/],
    [{ 'expected-sha': 'A'.repeat(40) }, /lowercase and full length/],
    [{ 'expected-sha': 'a'.repeat(39) }, /lowercase and full length/],
    [{ 'run-id': '0' }, /positive integers/],
    [{ 'run-attempt': '1.5' }, /positive integers/],
    [{ repository: 'owner' }, /owner\/name/],
    [{ 'workflow-ref': 'owner/app/.github/workflows/qualify-windows.yml@refs/heads/main' }, /exactly one of --workflow or --workflow-ref/],
    [{ profile: '../outside.json' }, /unsafe segment/],
    [{ profile: '.release\\release-profile.json' }, /repository-relative/],
    [{ profile: path.join(workspace, '.release', 'release-profile.json') }, /repository-relative/],
  ];
  for (const [overrides, pattern] of negatives) {
    assert.throws(() => freezeReleaseContract(base('windows', 'negative', overrides)), pattern);
  }
  const missingActor = base('windows', 'missing');
  delete missingActor.actor;
  assert.throws(() => freezeReleaseContract(missingActor), /--actor is required/);

  // profile 未配置该实体、profile 不合法、带 BOM：都拒绝。
  const windowsOnly = sampleProfile();
  delete windowsOnly.platforms['macos-arm64'];
  delete windowsOnly.platforms['macos-x64'];
  windowsOnly.releaseAssets = windowsOnly.releaseAssets.filter((asset) => asset.platform === 'windows');
  await writeFile(path.join(workspace, '.release', 'windows-only.json'), JSON.stringify(windowsOnly), 'utf8');
  assert.throws(() => freezeReleaseContract(base('macos-arm64', 'unconfigured', { profile: '.release/windows-only.json' })), /not configured in the release profile/);
  const invalid = sampleProfile();
  invalid.platforms['macos-arm64'].architectures = ['x64'];
  await writeFile(path.join(workspace, '.release', 'invalid.json'), JSON.stringify(invalid), 'utf8');
  assert.throws(() => freezeReleaseContract(base('windows', 'invalid', { profile: '.release/invalid.json' })), /release profile is invalid/);
  const wrongMacAsset = sampleProfile();
  wrongMacAsset.releaseAssets[2].name = 'App-{version}-arm64.dmg';
  await writeFile(path.join(workspace, '.release', 'wrong-mac-asset.json'), JSON.stringify(wrongMacAsset), 'utf8');
  assert.throws(() => freezeReleaseContract(base('macos-arm64', 'wrong-mac-asset', { profile: '.release/wrong-mac-asset.json' })), /must encode the arm64 macOS architecture/);
  await writeFile(path.join(workspace, '.release', 'bom.json'), Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf]), Buffer.from(profileText, 'utf8')]));
  assert.throws(() => freezeReleaseContract(base('windows', 'bom', { profile: '.release/bom.json' })), /without BOM/);

  // profile 路径经过 symlink/junction 时拒绝（权限不足无法建链接时跳过这一项，其余断言照常）。
  const outside = path.join(root, 'outside');
  await mkdir(outside, { recursive: true });
  await writeFile(path.join(outside, 'release-profile.json'), profileText, 'utf8');
  let linked = false;
  try {
    await symlink(outside, path.join(workspace, 'linked'), process.platform === 'win32' ? 'junction' : 'dir');
    linked = true;
  } catch {}
  if (linked) assert.throws(() => freezeReleaseContract(base('windows', 'linked', { profile: 'linked/release-profile.json' })), /symbolic link or reparse point/);

  // 参数解析：未知、重复、缺值都拒绝。
  assert.throws(() => parseArguments(['--unknown', 'x']), /Unknown argument/);
  assert.throws(() => parseArguments(['--tag', 'v1', '--tag', 'v2']), /Duplicate argument/);
  assert.throws(() => parseArguments(['--tag']), /Invalid argument/);

  // CLI 入口：成功退出 0 并写出文件；失败退出 1 且不留 contract。
  const cliArgs = (output, platform) => ['--repository', 'owner/app', '--expected-sha', sha, '--tag', 'v1.2.3', '--version', '1.2.3', '--workspace', workspace, '--profile', '.release/release-profile.json', '--output-root', path.join(root, output), '--platform', platform, '--run-id', '7', '--run-attempt', '1', '--workflow-ref', `owner/app/${sampleProfile().platforms[platform]?.qualificationWorkflow ?? ".github/workflows/qualify-macos.yml"}@refs/heads/main`, '--actor', 'octocat', '--event', 'workflow_dispatch', '--tag-format', 'v{version}', '--version-file', 'package.json'];
  const ok = spawnSync(process.execPath, [scriptPath, ...cliArgs('cli-ok', 'macos-x64')], { encoding: 'utf8' });
  assert.equal(ok.status, 0, ok.stderr);
  assert.deepEqual(JSON.parse(ok.stdout).architecture, 'x64');
  assert.equal(JSON.parse(await readFile(path.join(root, 'cli-ok', 'run-ledger.json'), 'utf8')).platform, 'macos-x64');
  const failed = spawnSync(process.execPath, [scriptPath, ...cliArgs('cli-fail', 'macos')], { encoding: 'utf8' });
  assert.equal(failed.status, 1);
  assert.match(failed.stderr, /supported qualification entity/);
  await assert.rejects(() => readFile(path.join(root, 'cli-fail', 'release-contract.json')), /ENOENT/);
} finally {
  await rm(root, { recursive: true, force: true });
}

process.stdout.write('{"passed":true,"checks":"entity-ledger-identity,byte-identical-contract,sorted-qualification-entities,workflow-ref,tag-format-adapter,version-file-adapter,entity-workflow-event-sha-run-guards,profile-path-safety,profile-validation,mac-asset-architecture,bom,reparse-guard,argument-parsing,cli-exit-codes"}\n');
