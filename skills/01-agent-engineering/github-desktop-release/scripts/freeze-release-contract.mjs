#!/usr/bin/env node
// 在 install、build、acceptance 之前冻结公共 release contract 与本平台 run ledger。
// contract 只含跨平台一致的字段（含 frozen.qualificationEntities），各平台用同一输入应得到逐字节相同的文件；
// ledger 写入本资格实体的 platform 与 architecture（取自 profile，validate-release-profile 已固定每个实体的唯一架构）。
// 与 github-desktop-promotion.mjs、validate-release-profile.mjs 一起原样复制到项目的 .release/scripts/。
// 项目约定（tag 格式、版本号来源）不写死在这里，由可选参数 --tag-format、--version-file 提供。
import { createHash } from 'node:crypto';
import { lstatSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { validateReleaseProfile } from './validate-release-profile.mjs';

export const QUALIFICATION_ENTITIES = Object.freeze(['windows', 'macos-arm64', 'macos-x64']);
const REQUIRED_OPTIONS = ['repository', 'expected-sha', 'tag', 'version', 'profile', 'output-root', 'platform', 'run-id', 'run-attempt', 'actor', 'event'];
const KNOWN_OPTIONS = new Set([...REQUIRED_OPTIONS, 'workflow', 'workflow-ref', 'workspace', 'tag-format', 'version-file', 'started-at']);

const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

export function parseArguments(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    assert(typeof key === 'string' && key.startsWith('--') && value !== undefined, `Invalid argument: ${key}`);
    const name = key.slice(2);
    assert(KNOWN_OPTIONS.has(name), `Unknown argument: ${key}`);
    assert(!Object.hasOwn(options, name), `Duplicate argument: ${key}`);
    options[name] = value;
  }
  return options;
}

function strictJson(raw, label) {
  assert(!(raw.length >= 3 && raw[0] === 0xef && raw[1] === 0xbb && raw[2] === 0xbf), `${label} must be UTF-8 without BOM`);
  return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(raw));
}

// 仓库内相对路径：正斜杠、无盘符、无空段/./..、无尾点尾空格、无通配符，且逐段不经过 symlink 或 reparse point。
function resolveWorkspaceFile(workspace, candidate, label) {
  assert(typeof candidate === 'string' && candidate.length > 0, `${label} must be non-empty`);
  assert(!path.isAbsolute(candidate) && !/^[A-Za-z]:/.test(candidate) && !candidate.includes('\\') && !candidate.includes(':') && !candidate.includes('\0'), `${label} must be a repository-relative forward-slash path`);
  const segments = candidate.split('/');
  assert(segments.every((segment) => segment !== '' && segment !== '.' && segment !== '..' && !/[. ]$/.test(segment) && !/[*?[\]]/.test(segment)), `${label} contains an unsafe segment`);
  let cursor = workspace;
  for (const segment of segments) {
    cursor = path.join(cursor, segment);
    assert(!lstatSync(cursor).isSymbolicLink(), `${label} must not traverse a symbolic link or reparse point`);
  }
  const relation = path.relative(realpathSync(workspace), realpathSync(cursor));
  assert(relation && !relation.startsWith('..') && !path.isAbsolute(relation), `${label} resolves outside the workspace`);
  return { absolute: cursor, relative: segments.join('/') };
}

// GITHUB_WORKFLOW_REF 形如 owner/repo/.github/workflows/x.yml@refs/heads/main。
export function workflowPathFromRef(workflowRef, repository) {
  const prefix = `${repository}/`;
  assert(typeof workflowRef === 'string' && workflowRef.startsWith(prefix) && workflowRef.includes('@'), 'workflow ref must start with <repository>/ and contain @<ref>');
  return workflowRef.slice(prefix.length, workflowRef.indexOf('@'));
}

export function freezeReleaseContract(options) {
  for (const key of REQUIRED_OPTIONS) assert(typeof options[key] === 'string' && options[key].length > 0, `--${key} is required`);
  assert((options.workflow === undefined) !== (options['workflow-ref'] === undefined), 'exactly one of --workflow or --workflow-ref is required');
  assert(/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(options.repository), 'repository must be owner/name');
  assert(/^[a-f0-9]{40}$/.test(options['expected-sha']), 'expected SHA must be lowercase and full length');
  assert(QUALIFICATION_ENTITIES.includes(options.platform), 'platform must name a supported qualification entity');
  assert(options.event === 'workflow_dispatch', 'event must equal workflow_dispatch');
  if (options['tag-format'] !== undefined) {
    assert(options['tag-format'].includes('{version}'), '--tag-format must contain {version}');
    assert(options.tag === options['tag-format'].replaceAll('{version}', options.version), 'tag does not match --tag-format');
  }
  const runId = Number(options['run-id']);
  const runAttempt = Number(options['run-attempt']);
  assert(/^[1-9][0-9]*$/.test(options['run-id']) && /^[1-9][0-9]*$/.test(options['run-attempt']) && Number.isSafeInteger(runId) && Number.isSafeInteger(runAttempt), 'run identity must use positive integers');

  const workspace = path.resolve(options.workspace ?? '.');
  const profileFile = resolveWorkspaceFile(workspace, options.profile, 'release profile');
  const profileRaw = readFileSync(profileFile.absolute);
  const profile = strictJson(profileRaw, 'release profile');
  const validation = validateReleaseProfile(profile);
  assert(validation.ok, `release profile is invalid: ${validation.errors.join('; ')}`);
  const policy = profile.platforms[options.platform];
  assert(policy, 'qualification entity is not configured in the release profile');
  const workflow = options.workflow ?? workflowPathFromRef(options['workflow-ref'], options.repository);
  assert(policy.qualificationWorkflow === workflow, 'workflow does not match release profile');
  if (options['version-file'] !== undefined) {
    const versionFile = resolveWorkspaceFile(workspace, options['version-file'], 'version file');
    const metadata = strictJson(readFileSync(versionFile.absolute), 'version file');
    assert(metadata?.version === options.version, 'release version does not match --version-file');
  }

  const profileRawBytesSha256 = sha256(profileRaw);
  const contract = {
    schemaVersion: 2,
    stage: 'qualification',
    repository: options.repository,
    frozen: {
      commit: options['expected-sha'],
      tag: options.tag,
      version: options.version,
      profilePath: profileFile.relative,
      profileRawBytesSha256,
      qualificationEntities: Object.keys(profile.platforms).sort(),
    },
  };
  const outputRoot = path.resolve(options['output-root']);
  mkdirSync(outputRoot, { recursive: true });
  const contractPath = path.join(outputRoot, 'release-contract.json');
  writeFileSync(contractPath, `${JSON.stringify(contract, null, 2)}\n`, 'utf8');
  const contractRawBytesSha256 = sha256(readFileSync(contractPath));
  const ledger = {
    schemaVersion: 2,
    platform: options.platform,
    architecture: policy.architectures[0],
    workflow,
    runId,
    runAttempt,
    repository: options.repository,
    actor: options.actor,
    event: options.event,
    startedAtUtc: options['started-at'] ?? new Date().toISOString(),
    qualifiedCommit: options['expected-sha'],
    releaseTag: options.tag,
    releaseVersion: options.version,
    releaseCreated: false,
    contractRawBytesSha256,
    profileRawBytesSha256,
  };
  const ledgerPath = path.join(outputRoot, 'run-ledger.json');
  writeFileSync(ledgerPath, `${JSON.stringify(ledger, null, 2)}\n`, 'utf8');
  return { contractPath, ledgerPath, contract, ledger };
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    const result = freezeReleaseContract(parseArguments(process.argv.slice(2)));
    process.stdout.write(`${JSON.stringify({ platform: result.ledger.platform, architecture: result.ledger.architecture, contractRawBytesSha256: result.ledger.contractRawBytesSha256, profileRawBytesSha256: result.ledger.profileRawBytesSha256 })}\n`);
  } catch (error) {
    process.stderr.write(`${error instanceof Error ? error.message : error}\n`);
    process.exitCode = 1;
  }
}
