#!/usr/bin/env node
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { readJsonFile } from './validate-release-profile.mjs';

const SURFACES = {
  'source-product-behavior': { classification: 'product', rebuildDefault: true },
  'toolchain-or-package': { classification: 'build', rebuildDefault: true },
  'installed-artifact-behavior': { classification: 'acceptance', rebuildDefault: 'evidence-dependent' },
  'verifier-rejected-known-good': { classification: 'gate-false-positive', rebuildDefault: false },
  'promotion-or-readback': { classification: 'promotion', rebuildDefault: false }
};

export function classifyFailure(record) {
  const errors = [];
  if (record === null || typeof record !== 'object' || Array.isArray(record)) {
    return { ok: false, errors: ['Failure record must be an object.'] };
  }
  const mapping = SURFACES[record.failureSurface];
  if (!mapping) errors.push(`Unknown failureSurface: ${record.failureSurface}`);
  if (typeof record.stage !== 'string' || record.stage.trim() === '') errors.push('stage must be non-empty.');
  if (!Array.isArray(record.evidenceBasis) || record.evidenceBasis.length === 0 || record.evidenceBasis.some((item) => typeof item !== 'string' || item.trim() === '')) {
    errors.push('evidenceBasis must contain at least one non-empty evidence item.');
  }
  if (!Number.isInteger(record.sameStageConsecutiveFailures) || record.sameStageConsecutiveFailures < 1) {
    errors.push('sameStageConsecutiveFailures must be a positive integer.');
  }
  if (errors.length > 0) return { ok: false, errors };

  const mustStop = record.sameStageConsecutiveFailures >= 2;
  return {
    ok: true,
    classification: mapping.classification,
    rebuildDefault: mapping.rebuildDefault,
    dispatchAllowed: !mustStop,
    mustStop,
    requiredBeforeNextDispatch: mustStop
      ? ['unified-root-cause', 'ranked-alternatives', 'raw-evidence-capture', 'local-red-green-replay', 'independent-read-only-review']
      : []
  };
}
function parseArgs(argv) {
  if (argv.length !== 2 || argv[0] !== '--record') throw new Error('Usage: classify-actions-failure.mjs --record <failure.json>');
  return argv[1];
}

async function main() {
  const record = await readJsonFile(path.resolve(parseArgs(process.argv.slice(2))));
  const result = classifyFailure(record);
  process.stdout.write(`${JSON.stringify(result)}\n`);
  if (!result.ok) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
