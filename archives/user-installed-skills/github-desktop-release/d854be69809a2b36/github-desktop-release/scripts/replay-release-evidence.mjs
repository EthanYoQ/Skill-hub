#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { readFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseStrictUtf8Json, readJsonFile, validateReleaseProfile } from './validate-release-profile.mjs';

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

async function resolveInside(root, relativePath) {
  const resolvedRoot = path.resolve(root);
  const resolved = path.resolve(resolvedRoot, relativePath);
  const rootKey = `${resolvedRoot}${path.sep}`.toLocaleLowerCase('en-US');
  const resolvedKey = resolved.toLocaleLowerCase('en-US');
  if (!resolvedKey.startsWith(rootKey)) throw new Error(`Receipt escapes evidence root: ${relativePath}`);

  const [realRoot, realTarget] = await Promise.all([realpath(resolvedRoot), realpath(resolved)]);
  const realRelative = path.relative(realRoot, realTarget);
  if (realRelative === '' || realRelative === '..' || realRelative.startsWith(`..${path.sep}`) || path.isAbsolute(realRelative)) {
    throw new Error(`Receipt resolves outside evidence root through a symlink or junction: ${relativePath}`);
  }
  return realTarget;
}

function newlineStyle(text) {
  const crlf = (text.match(/\r\n/g) || []).length;
  const withoutCrlf = text.replaceAll('\r\n', '');
  const cr = (withoutCrlf.match(/\r/g) || []).length;
  const lf = (withoutCrlf.match(/\n/g) || []).length;
  const present = [crlf > 0 && 'crlf', cr > 0 && 'cr', lf > 0 && 'lf'].filter(Boolean);
  return present.length === 0 ? 'none' : present.length === 1 ? present[0] : 'mixed';
}

function validateReceiptEnvelope(receipt, relativePath, platform, errors) {
  if (receipt === null || typeof receipt !== 'object' || Array.isArray(receipt)) {
    errors.push(`${platform}:${relativePath} must contain a JSON object.`);
    return;
  }
  if (receipt.accepted !== true) errors.push(`${platform}:${relativePath} must have accepted=true.`);
  if (!Array.isArray(receipt.observations) || receipt.observations.length === 0 || receipt.observations.some((value) => typeof value !== 'string' || value.trim() === '')) {
    errors.push(`${platform}:${relativePath} must have non-empty string observations.`);
  }
  if (receipt.platform !== undefined && receipt.platform !== platform) {
    errors.push(`${platform}:${relativePath} declares platform=${receipt.platform}.`);
  }
  const directFields = Object.keys(receipt).filter((key) => !['schemaVersion', 'accepted', 'observations', 'platform'].includes(key));
  if (directFields.length === 0) errors.push(`${platform}:${relativePath} has no direct observation field.`);

  if (relativePath.replaceAll('\\', '/').endsWith('/signing.json')) {
    if (!['signed', 'unsigned'].includes(receipt.status)) errors.push(`${platform}:${relativePath} must declare signed or unsigned status.`);
    if (typeof receipt.validationResult !== 'string' || receipt.validationResult.trim() === '') {
      errors.push(`${platform}:${relativePath} must declare validationResult.`);
    }
    if (receipt.status === 'unsigned' && (typeof receipt.unsignedDistributionImpact !== 'string' || receipt.unsignedDistributionImpact.trim() === '')) {
      errors.push(`${platform}:${relativePath} must disclose unsignedDistributionImpact.`);
    }
  }
}

export async function replayReleaseEvidence(profile, evidenceRoot) {
  const profileValidation = validateReleaseProfile(profile);
  if (!profileValidation.ok) return { ok: false, errors: profileValidation.errors.map((error) => `profile: ${error}`), receipts: [] };

  const errors = [];
  const receipts = [];
  const decoder = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });
  for (const platform of profileValidation.platforms) {
    for (const relativePath of profile.platforms[platform].acceptanceReceipts) {
      let bytes;
      let text;
      let receipt;
      try {
        const fullPath = await resolveInside(evidenceRoot, path.join(platform, relativePath));
        bytes = await readFile(fullPath);
        text = decoder.decode(bytes);
        receipt = parseStrictUtf8Json(bytes, `${platform}:${relativePath}`);
      } catch (error) {
        errors.push(`${platform}:${relativePath} could not be read as strict UTF-8 JSON: ${error.message}`);
        continue;
      }
      validateReceiptEnvelope(receipt, relativePath, platform, errors);
      receipts.push({
        platform,
        path: relativePath.replaceAll('\\', '/'),
        rawBytesSha256: sha256(bytes),
        utf8Bom: bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf,
        newlineStyle: newlineStyle(text),
        accepted: receipt.accepted === true
      });
    }
  }
  return { ok: errors.length === 0, errors, receipts };
}

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith('--') || index + 1 >= argv.length) throw new Error(`Invalid argument: ${key}`);
    result[key.slice(2)] = argv[index + 1];
    index += 1;
  }
  return result;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.profile || !args['evidence-root']) {
    throw new Error('Usage: replay-release-evidence.mjs --profile <profile.json> --evidence-root <directory>');
  }
  const profile = await readJsonFile(path.resolve(args.profile));
  const evidenceRoot = path.resolve(args['evidence-root']);
  const result = await replayReleaseEvidence(profile, evidenceRoot);
  process.stdout.write(`${JSON.stringify({ ...result, evidenceRoot })}\n`);
  if (!result.ok) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
