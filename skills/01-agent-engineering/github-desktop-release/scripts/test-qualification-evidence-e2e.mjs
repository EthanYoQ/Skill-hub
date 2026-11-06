#!/usr/bin/env node
// 端到端：真实执行 assets/ 下三个资格模板的证据生成代码（Windows 的 pwsh 步骤、macOS 的 Node 步骤，
// 冻结脚本按模板里的原样参数调用），再把产出的证据目录交给 github-desktop-promotion.mjs 的
// verifyExtractedQualification。三个资格实体都应被接受；删掉任一身份字段、或拿错实体的证据时应被拒。
// 依赖：node、git、pwsh（与 test-workflow-assets.ps1 相同）。
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { cp, mkdir, mkdtemp, readFile, readdir, rename, rm, stat, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { validatePromotionProfile, verifyExtractedQualification } from './github-desktop-promotion.mjs';

const scriptsRoot = path.dirname(fileURLToPath(import.meta.url));
const assetsRoot = path.join(scriptsRoot, '..', 'assets');
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const repository = 'owner/app';
const version = '1.2.3';
const tag = `v${version}`;

function run(command, args, options) {
  const result = spawnSync(command, args, { encoding: 'utf8', ...options });
  if (result.error) throw result.error;
  return result;
}

function mustRun(command, args, options) {
  const result = run(command, args, options);
  assert.equal(result.status, 0, `${command} ${args.join(' ')} failed:\n${result.stdout}\n${result.stderr}`);
  return result;
}

// 取出某个 workflow step 的 run: | 文本块并去掉公共缩进，与 Actions 交给 shell 的内容一致。
function stepRun(yamlText, stepName) {
  const lines = yamlText.split(/\r?\n/u);
  const start = lines.findIndex((line) => new RegExp(`^\\s*- name: ${stepName.replace(/[.*+?^${}()|[\]\\]/gu, '\\$&')}\\s*$`, 'u').test(line));
  assert.ok(start >= 0, `missing step: ${stepName}`);
  const stepIndent = lines[start].indexOf('-');
  let runIndex = -1;
  for (let index = start + 1; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.trim() && line.search(/\S/u) <= stepIndent) break;
    if (/^\s*run: \|\s*$/u.test(line)) { runIndex = index; break; }
  }
  assert.ok(runIndex > 0, `step has no run block: ${stepName}`);
  const runIndent = lines[runIndex].search(/\S/u);
  const body = [];
  for (let index = runIndex + 1; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.trim() && line.search(/\S/u) <= runIndent) break;
    body.push(line);
  }
  while (body.length && !body.at(-1).trim()) body.pop();
  const indent = Math.min(...body.filter((line) => line.trim()).map((line) => line.search(/\S/u)));
  return body.map((line) => (line.trim() ? line.slice(indent) : '')).join('\n');
}

function nodeHeredocs(script) {
  return [...script.matchAll(/node <<'NODE'\n([\s\S]*?)\nNODE(?:\n|$)/gu)].map((match) => match[1]);
}

function jobEnv(yamlText) {
  return Object.fromEntries([...yamlText.matchAll(/^ {6}(QUALIFICATION_[A-Z_]+): (\S+)\s*$/gmu)].map((match) => [match[1], match[2]]));
}

// 把模板 bash 里的冻结脚本调用拆成参数并代入环境变量，保证测试用的就是模板写的那组参数。
function freezeInvocation(script, env) {
  const line = script.split('\n').find((candidate) => candidate.startsWith('node .release/scripts/freeze-release-contract.mjs '));
  assert.ok(line, 'template must invoke .release/scripts/freeze-release-contract.mjs');
  return line.match(/"[^"]*"|'[^']*'|\S+/gu).slice(1).map((token) => {
    if (token.startsWith("'")) return token.slice(1, -1);
    const unquoted = token.startsWith('"') ? token.slice(1, -1) : token;
    return unquoted.replace(/\$([A-Z_]+)/gu, (_, name) => {
      assert.ok(env[name] !== undefined, `freeze invocation uses unset ${name}`);
      return env[name];
    });
  });
}

async function listFiles(root, current = root) {
  const files = [];
  for (const entry of await readdir(current, { withFileTypes: true })) {
    const full = path.join(current, entry.name);
    if (entry.isDirectory()) files.push(...await listFiles(root, full));
    else files.push(path.relative(root, full).split(path.sep).join('/'));
  }
  return files.sort();
}

function receiptsFor(entity) {
  return entity === 'windows' ? ['acceptance/install.json', 'acceptance/signing.json'] : ['acceptance/dmg-mount.json', 'acceptance/signing.json'];
}

async function writeReceipts(evidenceRoot, entity) {
  await mkdir(path.join(evidenceRoot, 'acceptance'), { recursive: true });
  await writeFile(path.join(evidenceRoot, receiptsFor(entity)[0]), `${JSON.stringify({ platform: entity, accepted: true, observations: ['package observed'], processObserved: true }, null, 2)}\n`, 'utf8');
  await writeFile(path.join(evidenceRoot, 'acceptance', 'signing.json'), `${JSON.stringify({ platform: entity, accepted: true, observations: ['signature inspected'], status: 'unsigned', validationResult: 'no signature present', unsignedDistributionImpact: 'operating system may warn on first launch' }, null, 2)}\n`, 'utf8');
}

// 改动证据后重新绑定 manifest 记录与 SHA256SUMS，使拒收只能来自身份字段本身。
async function rebind(root, { contractChanged = false } = {}) {
  const manifestPath = path.join(root, 'manifest.json');
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  if (contractChanged) {
    const contractHash = sha256(await readFile(path.join(root, 'release-contract.json')));
    const ledgerPath = path.join(root, 'run-ledger.json');
    const ledger = JSON.parse(await readFile(ledgerPath, 'utf8'));
    ledger.contractRawBytesSha256 = contractHash;
    await writeFile(ledgerPath, `${JSON.stringify(ledger, null, 2)}\n`, 'utf8');
    manifest.contractRawBytesSha256 = contractHash;
  }
  for (const record of [...manifest.artifacts, ...manifest.evidence]) {
    const bytes = await readFile(path.join(root, ...record.path.split('/')));
    record.rawBytesSha256 = sha256(bytes);
    record.sizeBytes = bytes.length;
  }
  await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  const paths = [...manifest.artifacts, ...manifest.evidence].map((record) => record.path).concat('manifest.json').sort();
  const lines = await Promise.all(paths.map(async (relativePath) => `${sha256(await readFile(path.join(root, ...relativePath.split('/'))))}  ${relativePath}`));
  await writeFile(path.join(root, 'SHA256SUMS.txt'), `${lines.join('\n')}\n`, 'utf8');
}

async function mutateJson(file, mutate) {
  const value = JSON.parse(await readFile(file, 'utf8'));
  mutate(value);
  await writeFile(file, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

const temp = await mkdtemp(path.join(os.tmpdir(), 'qualification-evidence-e2e-'));
try {
  const workspace = path.join(temp, 'workspace');
  await mkdir(path.join(workspace, '.release', 'scripts'), { recursive: true });
  await mkdir(path.join(workspace, '.github'), { recursive: true });
  const signingPolicy = { mode: 'allow-unsigned-with-disclosure', disclosureRequired: true };
  const profile = {
    schemaVersion: 1,
    provider: 'github-actions',
    platforms: {
      windows: { qualificationWorkflow: '.github/workflows/qualify-windows.yml', artifactName: 'qualified-windows', architectures: ['x64'], retentionDays: 14, acceptanceReceipts: receiptsFor('windows'), signingPolicy },
      'macos-arm64': { qualificationWorkflow: '.github/workflows/qualify-macos-arm64.yml', artifactName: 'qualified-macos-arm64', architectures: ['arm64'], retentionDays: 14, acceptanceReceipts: receiptsFor('macos-arm64'), signingPolicy },
      'macos-x64': { qualificationWorkflow: '.github/workflows/qualify-macos-x64.yml', artifactName: 'qualified-macos-x64', architectures: ['x64'], retentionDays: 14, acceptanceReceipts: receiptsFor('macos-x64'), signingPolicy },
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
  validatePromotionProfile(profile);
  const profilePath = '.release/release-profile.json';
  await writeFile(path.join(workspace, profilePath), `${JSON.stringify(profile, null, 2)}\n`, 'utf8');
  await writeFile(path.join(workspace, 'package.json'), `${JSON.stringify({ name: 'app', version }, null, 2)}\n`, 'utf8');
  await writeFile(path.join(workspace, '.github', 'windows-release-toolchain.json'), `${JSON.stringify({ runnerLabel: 'windows-2022', imageOS: 'win22', nodeVersion: '0.0.0', packageManagerCommand: 'pnpm', packageManagerVersion: '0.0.0' }, null, 2)}\n`, 'utf8');
  // 冻结脚本与它依赖的 profile 校验脚本按文档原样复制到项目 .release/scripts/。
  for (const name of ['freeze-release-contract.mjs', 'validate-release-profile.mjs']) await cp(path.join(scriptsRoot, name), path.join(workspace, '.release', 'scripts', name));
  const gitEnv = { ...process.env, GIT_CONFIG_NOSYSTEM: '1', GIT_AUTHOR_NAME: 't', GIT_AUTHOR_EMAIL: 't@example.invalid', GIT_COMMITTER_NAME: 't', GIT_COMMITTER_EMAIL: 't@example.invalid' };
  mustRun('git', ['init', '-q'], { cwd: workspace, env: gitEnv });
  mustRun('git', ['add', '-A'], { cwd: workspace, env: gitEnv });
  mustRun('git', ['-c', 'commit.gpgsign=false', 'commit', '-q', '-m', 'fixture'], { cwd: workspace, env: gitEnv });
  const expectedSha = mustRun('git', ['rev-parse', 'HEAD'], { cwd: workspace }).stdout.trim();
  await mkdir(path.join(workspace, 'dist'), { recursive: true });
  const profileRawBytesSha256 = sha256(await readFile(path.join(workspace, profilePath)));
  const evidenceRoots = {};

  // Windows：执行模板的冻结步骤与 manifest 步骤（真实 pwsh 代码），中间的工具链、构建与验收由夹具代替。
  {
    const template = await readFile(path.join(assetsRoot, 'electron-nsis-qualification.yml'), 'utf8');
    const runnerTemp = path.join(temp, 'windows-runner');
    const githubEnvFile = path.join(temp, 'windows-github-env.txt');
    await mkdir(runnerTemp, { recursive: true });
    await writeFile(path.join(workspace, 'dist', `App-Setup-${version}.exe`), Buffer.from([0x4d, 0x5a, 0x00, 0x01]));
    await writeFile(path.join(workspace, 'dist', 'latest.yml'), `version: ${version}\n`, 'utf8');
    const env = {
      ...process.env,
      EXPECTED_SHA: expectedSha, RELEASE_TAG: tag, RELEASE_VERSION: version, PROFILE_PATH: profilePath,
      ARTIFACT_PATHS: `dist/App-Setup-${version}.exe;dist/latest.yml`,
      RUNNER_TEMP: runnerTemp, GITHUB_ENV: githubEnvFile, GITHUB_WORKSPACE: workspace, GITHUB_REPOSITORY: repository,
      GITHUB_RUN_ID: '101', GITHUB_RUN_ATTEMPT: '1', GITHUB_WORKFLOW_REF: `${repository}/.github/workflows/qualify-windows.yml@refs/heads/main`,
      GITHUB_ACTOR: 'octocat', GITHUB_EVENT_NAME: 'workflow_dispatch', ImageOS: 'win22', ImageVersion: '20260101.1',
    };
    const runPwsh = async (name) => {
      const file = path.join(temp, `${name.replace(/\W+/gu, '-')}.ps1`);
      await writeFile(file, stepRun(template, name), 'utf8');
      return run('pwsh', ['-NoProfile', '-NonInteractive', '-File', file], { cwd: workspace, env });
    };
    const frozen = await runPwsh('Freeze qualification contract before execution');
    assert.equal(frozen.status, 0, `Windows freeze step failed:\n${frozen.stdout}\n${frozen.stderr}`);
    for (const line of (await readFile(githubEnvFile, 'utf8')).split(/\r?\n/u).filter(Boolean)) {
      const separator = line.indexOf('=');
      env[line.slice(0, separator).replace(/^﻿/u, '')] = line.slice(separator + 1);
    }
    const evidenceRoot = env.WCR_EVIDENCE_ROOT;
    assert.ok(evidenceRoot && env.WCR_CONTRACT_SHA256 && env.WCR_PROFILE_SHA256, 'Windows freeze step must export WCR_* bindings');
    await writeFile(path.join(evidenceRoot, 'runtime-verification.json'), `${JSON.stringify({ accepted: true, observations: ['fixture'], checkoutCommit: expectedSha }, null, 2)}\n`, 'utf8');
    await writeReceipts(evidenceRoot, 'windows');
    const finalized = await runPwsh('Generate manifest and raw-byte hash evidence');
    assert.equal(finalized.status, 0, `Windows manifest step failed:\n${finalized.stdout}\n${finalized.stderr}`);
    evidenceRoots.windows = { root: evidenceRoot, runId: 101 };
  }

  // macOS：两个模板各执行一次；冻结脚本按模板参数调用，随后执行模板内的 Node 校验与收尾代码。
  for (const [entity, runId] of [['macos-arm64', 201], ['macos-x64', 301]]) {
    const template = await readFile(path.join(assetsRoot, `${entity}-qualification.yml`), 'utf8');
    const arch = entity === 'macos-arm64' ? 'arm64' : 'x64';
    await writeFile(path.join(workspace, 'dist', `App-mac-${arch}-${version}.dmg`), Buffer.from(`dmg-${arch}`, 'utf8'));
    await mkdir(path.join(workspace, '.release', 'out'), { recursive: true });
    await writeFile(path.join(workspace, '.release', 'out', `${entity}-assets.json`), `${JSON.stringify([{ name: `App-mac-${arch}-${version}.dmg`, sourcePath: `dist/App-mac-${arch}-${version}.dmg` }], null, 2)}\n`, 'utf8');
    const env = {
      ...process.env,
      ...jobEnv(template),
      EXPECTED_SHA: expectedSha, RELEASE_TAG: tag, RELEASE_VERSION: version, PROFILE_PATH: profilePath,
      GITHUB_WORKSPACE: workspace, GITHUB_REPOSITORY: repository, GITHUB_RUN_ID: String(runId), GITHUB_RUN_ATTEMPT: '1',
      GITHUB_WORKFLOW_REF: `${repository}/.github/workflows/qualify-${entity}.yml@refs/heads/main`, GITHUB_ACTOR: 'octocat', GITHUB_EVENT_NAME: 'workflow_dispatch',
    };
    assert.equal(env.QUALIFICATION_ENTITY, entity);
    assert.equal(env.QUALIFICATION_ARCH, arch);
    const freezeStep = stepRun(template, 'Freeze common contract and entity ledger');
    await rm(path.join(workspace, 'release-evidence'), { recursive: true, force: true });
    mustRun(process.execPath, freezeInvocation(freezeStep, env), { cwd: workspace, env });
    const [identityCheck] = nodeHeredocs(freezeStep);
    mustRun(process.execPath, ['-'], { cwd: workspace, env: { ...env, QUALIFICATION_PROFILE_ABSOLUTE: path.join(workspace, profilePath) }, input: identityCheck });
    await writeReceipts(path.join(workspace, 'release-evidence'), entity);
    const [finalize] = nodeHeredocs(stepRun(template, 'Finalize promotion-compatible exact bundle'));
    if (entity === 'macos-arm64') {
      // 另一个架构的模板收尾代码不得接受这份证据。
      const otherEnv = jobEnv(await readFile(path.join(assetsRoot, 'macos-x64-qualification.yml'), 'utf8'));
      const crossed = run(process.execPath, ['-'], { cwd: workspace, env: { ...env, ...otherEnv }, input: finalize });
      assert.notEqual(crossed.status, 0, 'x64 finalize must reject arm64 frozen evidence');
    }
    mustRun(process.execPath, ['-'], { cwd: workspace, env, input: finalize });
    const destination = path.join(temp, `evidence-${entity}`);
    await rename(path.join(workspace, 'release-evidence'), destination);
    evidenceRoots[entity] = { root: destination, runId };
  }

  // 三份模板产出的公共 contract 必须逐字节相同。
  const contracts = await Promise.all(Object.values(evidenceRoots).map(({ root }) => readFile(path.join(root, 'release-contract.json'))));
  assert.equal(new Set(contracts.map((bytes) => bytes.toString('hex'))).size, 1, 'templates must emit a byte-identical common contract');

  const verify = (entity, root, previousBindings = null, policyEntity = entity) => verifyExtractedQualification({
    root,
    platform: policyEntity,
    policy: profile.platforms[policyEntity],
    releaseAssetPolicy: profile.releaseAssets,
    version,
    expectedSha,
    mapping: { runId: evidenceRoots[entity].runId, attempt: 1, artifactId: evidenceRoots[entity].runId + 1000 },
    artifact: { name: profile.platforms[policyEntity].artifactName },
    profileRawBytesSha256,
    qualificationRepository: repository,
    previousBindings,
  });

  // 正向：promotion 校验路径按顺序接受三个实体，且共享同一 contract/profile 绑定。
  let bindings = null;
  for (const entity of ['macos-arm64', 'macos-x64', 'windows']) {
    const manifest = JSON.parse(await readFile(path.join(evidenceRoots[entity].root, 'manifest.json'), 'utf8'));
    const ledger = JSON.parse(await readFile(path.join(evidenceRoots[entity].root, 'run-ledger.json'), 'utf8'));
    assert.equal(manifest.platform, entity);
    assert.equal(manifest.architecture, profile.platforms[entity].architectures[0]);
    assert.equal(ledger.platform, entity);
    assert.equal(ledger.architecture, profile.platforms[entity].architectures[0]);
    const verified = await verify(entity, evidenceRoots[entity].root, bindings);
    bindings = verified.bindings;
    assert.deepEqual(verified.assets.map((asset) => asset.name).sort(), profile.releaseAssets.filter((asset) => asset.platform === entity).map((asset) => asset.name.replaceAll('{version}', version)).sort());
  }

  // 反向：删除身份字段、或把一个实体的证据当作另一个实体，都必须被拒。
  const cases = [
    { name: 'control-rebind', entity: 'windows', mutate: async () => {}, error: null },
    { name: 'manifest-platform', entity: 'windows', mutate: (root) => mutateJson(path.join(root, 'manifest.json'), (value) => { delete value.platform; }), error: /qualification manifest entity mismatch/u },
    { name: 'manifest-architecture', entity: 'macos-arm64', mutate: (root) => mutateJson(path.join(root, 'manifest.json'), (value) => { delete value.architecture; }), error: /qualification manifest entity mismatch/u },
    { name: 'ledger-platform', entity: 'macos-x64', mutate: (root) => mutateJson(path.join(root, 'run-ledger.json'), (value) => { delete value.platform; }), error: /run ledger entity mismatch/u },
    { name: 'ledger-architecture', entity: 'windows', mutate: (root) => mutateJson(path.join(root, 'run-ledger.json'), (value) => { delete value.architecture; }), error: /run ledger entity mismatch/u },
    { name: 'contract-entities', entity: 'macos-arm64', contractChanged: true, mutate: (root) => mutateJson(path.join(root, 'release-contract.json'), (value) => { delete value.frozen.qualificationEntities; }), error: /does not declare the qualification entity/u },
  ];
  for (const testCase of cases) {
    const root = path.join(temp, `negative-${testCase.name}`);
    await cp(evidenceRoots[testCase.entity].root, root, { recursive: true });
    await testCase.mutate(root);
    await rebind(root, { contractChanged: testCase.contractChanged });
    if (testCase.error) await assert.rejects(() => verify(testCase.entity, root), testCase.error, testCase.name);
    else await verify(testCase.entity, root);
  }
  await assert.rejects(() => verify('macos-arm64', evidenceRoots['macos-arm64'].root, null, 'macos-x64'), /qualification manifest entity mismatch/u);

  // 证据目录只含 manifest 索引的文件加 manifest.json 与 SHA256SUMS.txt。
  for (const { root } of Object.values(evidenceRoots)) {
    const manifest = JSON.parse(await readFile(path.join(root, 'manifest.json'), 'utf8'));
    const expected = [...manifest.artifacts, ...manifest.evidence].map((record) => record.path).concat('manifest.json', 'SHA256SUMS.txt').sort();
    assert.deepEqual(await listFiles(root), expected);
    assert.ok((await stat(path.join(root, 'SHA256SUMS.txt'))).size > 0);
  }
} finally {
  await rm(temp, { recursive: true, force: true });
}

process.stdout.write('{"passed":true,"checks":"windows-template-pwsh-freeze-and-manifest,macos-arm64-template,macos-x64-template,template-freeze-invocation,cross-architecture-finalize-rejected,byte-identical-contract,promotion-accepts-three-entities,shared-bindings,missing-manifest-platform,missing-manifest-architecture,missing-ledger-platform,missing-ledger-architecture,missing-contract-entities,wrong-entity,exact-file-set"}\n');
