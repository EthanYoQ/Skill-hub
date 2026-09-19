[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Assert-Condition {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw "Assertion failed: $Message" }
}

function Assert-Throws {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Action,
        [Parameter(Mandatory = $true)][string]$Message
    )
    $threw = $false
    try { & $Action }
    catch { $threw = $true }
    Assert-Condition -Condition $threw -Message $Message
}

function Assert-ExactReceiptSet {
    param(
        [Parameter(Mandatory = $true)][string[]]$Expected,
        [Parameter(Mandatory = $true)][string[]]$Actual
    )
    if ($Expected.Count -eq 0) { throw 'Expected receipt set must be non-empty.' }
    $keys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($receipt in $Expected) {
        if ($receipt -notmatch '^acceptance/(?:[^/]+/)*[^/]+\.json$' -or -not $keys.Add($receipt)) { throw "Invalid or colliding expected receipt: $receipt" }
    }
    if (Compare-Object -CaseSensitive -ReferenceObject @($Expected | Sort-Object -CaseSensitive) -DifferenceObject @($Actual | Sort-Object -CaseSensitive)) {
        throw 'Acceptance JSON set must exactly equal profile acceptanceReceipts.'
    }
}

function Get-PwshRunBlocks {
    param([Parameter(Mandatory = $true)][string]$Path)

    $lines = [System.IO.File]::ReadAllLines($Path)
    $blocks = New-Object System.Collections.Generic.List[object]
    for ($index = 0; $index -lt $lines.Length; $index++) {
        if ($lines[$index] -notmatch '^(?<indent>\s*)shell:\s*pwsh\s*(?:#.*)?$') { continue }
        $shellIndent = $matches.indent.Length
        $foundRun = $false
        for ($cursor = $index + 1; $cursor -lt $lines.Length; $cursor++) {
            $candidate = $lines[$cursor]
            if ($candidate -match '^(?<indent>\s*)-\s+name:') {
                if ($matches.indent.Length -le $shellIndent) { break }
            }
            if ($candidate -match '^(?<indent>\s*)run:\s*[|>][+-]?\s*$') {
                $runIndent = $matches.indent.Length
                $runLines = New-Object System.Collections.Generic.List[string]
                for ($bodyIndex = $cursor + 1; $bodyIndex -lt $lines.Length; $bodyIndex++) {
                    $bodyLine = $lines[$bodyIndex]
                    if (-not [string]::IsNullOrWhiteSpace($bodyLine)) {
                        $bodyIndent = ($bodyLine -replace '^(\s*).*$', '$1').Length
                        if ($bodyIndent -le $runIndent) { break }
                    }
                    $runLines.Add($bodyLine)
                }
                $nonBlankIndents = @($runLines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { ($_ -replace '^(\s*).*$', '$1').Length })
                if ($nonBlankIndents.Count -eq 0) { throw "shell: pwsh run block is empty at line $($index + 1)." }
                $blockIndent = ($nonBlankIndents | Measure-Object -Minimum).Minimum
                $script = @($runLines | ForEach-Object {
                    if ([string]::IsNullOrWhiteSpace($_)) { '' } else { $_.Substring($blockIndent) }
                }) -join [Environment]::NewLine
                $blocks.Add([pscustomobject]@{ shellLine = $index + 1; runLine = $cursor + 1; script = $script })
                $foundRun = $true
                break
            }
        }
        if (-not $foundRun) { throw "shell: pwsh at line $($index + 1) has no literal run block." }
    }
    return $blocks.ToArray()
}

function Assert-PowerShellParses {
    param([Parameter(Mandatory = $true)][object[]]$Blocks)

    foreach ($block in $Blocks) {
        $tokens = $null
        $errors = $null
        $null = [System.Management.Automation.Language.Parser]::ParseInput($block.script, [ref]$tokens, [ref]$errors)
        if ($errors.Count -gt 0) {
            $detail = $errors | ForEach-Object { "line $($_.Extent.StartLineNumber): $($_.Message)" }
            throw "Qualification pwsh run block beginning at YAML line $($block.runLine) does not parse: $($detail -join '; ')"
        }
    }
}

function Assert-GitHubExpressionDelimiters {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$AssetName
    )

    if ($Content -match '\$\{\{\{') {
        throw "$AssetName contains an invalid GitHub expression opener."
    }
    $openers = [regex]::Matches($Content, '\$\{\{')
    $expressions = [regex]::Matches($Content, '\$\{\{\s*(?<body>[^{}\r\n]+?)\s*\}\}')
    if ($openers.Count -ne $expressions.Count) {
        throw "$AssetName has an unterminated or malformed GitHub expression delimiter."
    }
    foreach ($expression in $expressions) {
        if ([string]::IsNullOrWhiteSpace($expression.Groups['body'].Value)) {
            throw "$AssetName has an empty GitHub expression."
        }
    }
}

function Assert-WorkflowHeaderIsClean {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$AssetName
    )

    $lines = [regex]::Split($Content, "\r?\n")
    foreach ($prefix in @('Exit code:', 'Wall time:', 'Output:')) {
        if ($Content -match ('(?m)^' + [regex]::Escape($prefix))) {
            throw "$AssetName contains tool-output header pollution: $prefix"
        }
    }
    $meaningfulLines = @($lines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch '^\s*#' })
    if ($meaningfulLines.Count -eq 0 -or $meaningfulLines[0] -notmatch '^name:\s+\S') {
        throw "$AssetName must begin with a name top-level key after comments."
    }
    $allowedTopLevelKeys = @('name', 'on', 'permissions', 'concurrency', 'jobs')
    foreach ($line in $meaningfulLines) {
        if ($line -match '^(?<key>[A-Za-z][A-Za-z0-9_-]*):') {
            if ($allowedTopLevelKeys -notcontains $matches.key) {
                throw "$AssetName contains an unexpected top-level key: $($matches.key)"
            }
        }
    }
}

function Get-StepLine {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $match = [regex]::Match($Content, '(?m)^\s*-\s+name:\s*' + [regex]::Escape($Name) + '\s*$')
    if (-not $match.Success) { throw "Missing workflow step: $Name" }
    return $match.Index
}

function Get-FunctionDefinition {
    param(
        [Parameter(Mandatory = $true)][string]$Script,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseInput($Script, [ref]$tokens, [ref]$errors)
    if ($errors.Count -gt 0) { throw "Cannot extract helper $Name from unparsable script." }
    $function = $ast.Find({
        param($node)
        $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $Name
    }, $true) | Select-Object -First 1
    if ($null -eq $function) { throw "Missing helper function: $Name" }
    return $function.Extent.Text
}

function Get-ByteArrayWithoutNewlineBytes {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)
    return [byte[]]@($Bytes | Where-Object { $_ -ne 10 -and $_ -ne 13 })
}

function Test-ByteArraysEqual {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Actual,
        [Parameter(Mandatory = $true)][byte[]]$Expected
    )

    if ($Actual.Length -ne $Expected.Length) { return $false }
    for ($index = 0; $index -lt $Actual.Length; $index++) {
        if ($Actual[$index] -ne $Expected[$index]) { return $false }
    }
    return $true
}

$scriptRoot = [System.IO.Path]::GetDirectoryName($PSCommandPath)
$skillRoot = Split-Path -Parent $scriptRoot
$skillPath = Join-Path $skillRoot 'SKILL.md'
$qualificationPath = Join-Path $skillRoot 'assets\electron-nsis-qualification.yml'
$macosQualificationPath = Join-Path $skillRoot 'assets\macos-qualification.yml'
$promotionPath = Join-Path $skillRoot 'assets\github-desktop-release-promotion.yml'
$promotionEnginePath = Join-Path $scriptRoot 'github-desktop-promotion.mjs'
$preflightPath = Join-Path $scriptRoot 'preflight-windows-release.ps1'
$preflightTestPath = Join-Path $scriptRoot 'test-preflight.ps1'
$evidenceReferencePath = Join-Path $skillRoot 'references\evidence-contract.md'
$contractReferencePath = Join-Path $skillRoot 'references\release-contract.md'
$adapterReferencePath = Join-Path $skillRoot 'references\stack-adapters.md'

foreach ($path in @($qualificationPath, $macosQualificationPath, $promotionPath)) {
    Assert-Condition -Condition (Test-Path -LiteralPath $path -PathType Leaf) -Message "Workflow asset is missing: $path"
    $content = Get-Content -LiteralPath $path -Raw
    Assert-WorkflowHeaderIsClean -Content $content -AssetName $path
    Assert-Condition -Condition ($content -notmatch "`t") -Message "Workflow asset uses tabs instead of YAML indentation: $path"
    foreach ($rootKey in @('name:', 'on:', 'permissions:', 'jobs:')) {
        Assert-Condition -Condition ($content -match ('(?m)^' + [regex]::Escape($rootKey))) -Message "Workflow asset is missing root key ${rootKey}: $path"
    }
    foreach ($line in @($content -split [Environment]::NewLine | Where-Object { $_ -match '^\s+\S' })) {
        $indent = ($line -replace '^(\s*).*$', '$1').Length
        Assert-Condition -Condition (($indent % 2) -eq 0) -Message "Workflow asset has uneven YAML indentation: $path"
    }
}

$qualification = Get-Content -LiteralPath $qualificationPath -Raw
$macosQualification = Get-Content -LiteralPath $macosQualificationPath -Raw
$promotion = Get-Content -LiteralPath $promotionPath -Raw
$promotionEngine = Get-Content -LiteralPath $promotionEnginePath -Raw
$qualificationBlocks = Get-PwshRunBlocks -Path $qualificationPath
Assert-Condition -Condition ($qualificationBlocks.Count -gt 0) -Message 'Qualification must contain shell: pwsh run blocks.'
Assert-PowerShellParses -Blocks $qualificationBlocks
Assert-GitHubExpressionDelimiters -Content $qualification -AssetName 'qualification workflow'
Assert-GitHubExpressionDelimiters -Content $macosQualification -AssetName 'macOS qualification workflow'
Assert-GitHubExpressionDelimiters -Content $promotion -AssetName 'promotion workflow'
Assert-Throws -Action { Assert-GitHubExpressionDelimiters -Content '${{{ github.sha }}' -AssetName 'invalid fixture' } -Message 'GitHub expression validation must reject a triple-open delimiter.'
Assert-Throws -Action { Assert-WorkflowHeaderIsClean -Content 'Exit code: 0' -AssetName 'invalid fixture' } -Message 'Workflow header validation must reject Exit code tool output.'
Assert-Throws -Action { Assert-WorkflowHeaderIsClean -Content 'Wall time: 0.8 seconds' -AssetName 'invalid fixture' } -Message 'Workflow header validation must reject Wall time tool output.'
Assert-Throws -Action { Assert-WorkflowHeaderIsClean -Content 'Output:' -AssetName 'invalid fixture' } -Message 'Workflow header validation must reject Output tool output.'
Assert-Throws -Action { Assert-WorkflowHeaderIsClean -Content ('name: fixture' + [Environment]::NewLine + 'unexpected: value') -AssetName 'invalid fixture' } -Message 'Workflow header validation must reject unknown top-level keys.'

$expectedPins = @{
    'checkout' = '11bd71901bbe5b1630ceea73d27597364c9af683'
    'setup-node' = '49933ea5288caeca8642d1e84afbd3f7d6820020'
    'upload-artifact' = 'ea165f8d65b6e75b540449e92b4886f43607fa02'
    'download-artifact' = 'd3f86a106a0bac45b974a628896c90dbdf5c8093'
}
foreach ($asset in @($qualification, $macosQualification, $promotion)) {
    $uses = [regex]::Matches($asset, '(?m)^\s*uses:\s*actions/(?<action>[a-z0-9-]+)@(?<ref>[^\s#]+)\s*$')
    Assert-Condition -Condition ($uses.Count -gt 0) -Message 'Workflow assets must use immutable actions pins.'
    foreach ($use in $uses) {
        $action = $use.Groups['action'].Value
        $reference = $use.Groups['ref'].Value
        Assert-Condition -Condition ($reference -match '^[0-9a-f]{40}$') -Message "actions/$action must use a 40-character SHA."
        Assert-Condition -Condition ($expectedPins.ContainsKey($action)) -Message "Unexpected actions/$action reference is not approved by this template."
        Assert-Condition -Condition ($reference -eq $expectedPins[$action]) -Message "actions/$action does not use its verified SHA."
    }
    Assert-Condition -Condition ($asset -notmatch 'actions/[^\s@]+@v4') -Message 'Mutable actions/*@v4 reference is forbidden.'
}

$freezeLine = Get-StepLine -Content $qualification -Name 'Freeze qualification contract before execution'
$configureLine = Get-StepLine -Content $qualification -Name 'Configure the project toolchain declared by the frozen contract'
$verifyLine = Get-StepLine -Content $qualification -Name 'Verify frozen contract and actual execution environment'
$installLine = Get-StepLine -Content $qualification -Name 'Install locked dependencies'
$buildLine = Get-StepLine -Content $qualification -Name 'Build the frozen Windows installer'
$acceptanceLine = Get-StepLine -Content $qualification -Name 'Execute real Windows installer acceptance'
Assert-Condition -Condition ($freezeLine -lt $configureLine -and $configureLine -lt $verifyLine -and $verifyLine -lt $installLine -and $installLine -lt $buildLine -and $buildLine -lt $acceptanceLine) -Message 'Contract, actual execution verification, install, build, and acceptance must remain ordered.'
Assert-Condition -Condition ($qualification -match 'WCR_CONTRACT_SHA256' -and $qualification -match 'windows-release-toolchain\.json') -Message 'Qualification must freeze a contract and validate a committed app toolchain before execution.'
Assert-Condition -Condition ($qualification -notmatch 'acceptance\\summary\.json') -Message 'Boolean acceptance summary self-attestation is forbidden.'
$skillContent = Get-Content -LiteralPath $skillPath -Raw
$skillFreezeIndex = $skillContent.IndexOf('在 install、build 或 acceptance 前冻结并 hash contract')
$skillInstallIndex = $skillContent.IndexOf('执行 stack 专属的 locked install')
$skillAcceptanceIndex = $skillContent.IndexOf('对 installer 做真实安装')
Assert-Condition -Condition ($skillFreezeIndex -ge 0 -and $skillFreezeIndex -lt $skillInstallIndex -and $skillInstallIndex -lt $skillAcceptanceIndex) -Message 'SKILL.md must freeze/hash the contract before install, build, and acceptance.'

Assert-Condition -Condition ($qualification -match '\$profile\.platforms\.windows\.acceptanceReceipts') -Message 'Windows receipt set must come from the frozen profile.'
Assert-Condition -Condition ($macosQualification -match 'profile\.platforms\.macos\.acceptanceReceipts') -Message 'macOS receipt set must come from the frozen profile.'
foreach ($producer in @($qualification, $macosQualification)) {
    Assert-Condition -Condition ($producer -match 'acceptance JSON set must exactly equal profile acceptanceReceipts') -Message 'Producer must fail closed when on-disk acceptance JSON differs from profile.'
    Assert-Condition -Condition ($producer -match 'exactly one signing\.json receipt') -Message 'Producer must require exactly one profile-declared signing receipt.'
    Assert-Condition -Condition ($producer -match 'acceptance evidence root cannot be a (?:reparse point|symlink)') -Message 'Producer must reject a reparse/symlink acceptance root.'
}
$receiptFixture = @('acceptance/launch.json', 'acceptance/signing.json')
Assert-ExactReceiptSet -Expected $receiptFixture -Actual @('acceptance/signing.json', 'acceptance/launch.json')
Assert-Throws -Action { Assert-ExactReceiptSet -Expected $receiptFixture -Actual @('acceptance/launch.json') } -Message 'Receipt set fixture must reject a missing profile receipt.'
Assert-Throws -Action { Assert-ExactReceiptSet -Expected $receiptFixture -Actual @('acceptance/launch.json', 'acceptance/signing.json', 'acceptance/extra.json') } -Message 'Receipt set fixture must reject an undeclared extra receipt.'
Assert-Throws -Action { Assert-ExactReceiptSet -Expected @('acceptance/launch.json', 'ACCEPTANCE/launch.json') -Actual @('acceptance/launch.json', 'ACCEPTANCE/launch.json') } -Message 'Receipt set fixture must reject case-insensitive profile collisions.'
foreach ($field in @('accepted', 'observations', 'status', 'validationResult', 'unsignedDistributionImpact')) {
    Assert-Condition -Condition ($qualification -match [regex]::Escape($field)) -Message "Qualification signing/evidence validation is missing $field."
}
Assert-Condition -Condition ($qualification -match 'signing = \$signingEnvelope' -and $qualification -match 'NotePropertyName signing -NotePropertyValue \$signingEnvelope') -Message 'Windows ledger and manifest must reuse the same four-field signing envelope.'
Assert-Condition -Condition ($macosQualification -match 'ledger\.signing = \{ status: signing\.status, validationResult: signing\.validationResult, unsignedDistributionImpact: signing\.unsignedDistributionImpact, evidencePath: signing\.evidencePath \}' -and $macosQualification -match 'artifacts, evidence, signing') -Message 'macOS ledger signing must match the manifest signing envelope including evidencePath.'
Assert-Condition -Condition ($qualification -match 'Get-AcceptanceRecord' -and $qualification -match 'Get-RawRecord' -and $qualification -match 'SHA256SUMS\.txt') -Message 'Independent evidence must be raw-byte recorded in manifest and checksums.'
Assert-Condition -Condition ($qualification -match 'id:\s*upload-qualified' -and $qualification -match 'artifact-id' -and $qualification -match 'artifact-digest' -and $qualification -match 'artifact-url') -Message 'Qualification upload must persist immutable artifact attestation metadata.'
Assert-Condition -Condition ($qualification -match 'Collect sanitized failure diagnostics') -Message 'Qualification must have an explicit sanitized diagnostics collector.'
$diagnosticSection = [regex]::Match($qualification, '(?ms)^\s*-\s+name:\s*Collect sanitized failure diagnostics.*?(?=^\s*-\s+name:|\z)').Value
Assert-Condition -Condition ($diagnosticSection -notmatch '\*\.log|github\.workspace') -Message 'Failure diagnostics must not glob repository logs or upload the workspace.'
Assert-Condition -Condition ($diagnosticSection -match 'allowlist') -Message 'Failure diagnostics must be copied from an explicit allowlist.'

Assert-Condition -Condition ($qualification -match 'rawBytesSha256' -and $qualification -match 'newlineCanonicalSha256' -and $qualification -match 'Get-NewlineCanonicalBytes') -Message 'Lockfile evidence must record raw and newline-canonical SHA-256 values.'
Assert-Condition -Condition ($qualification -match 'UTF8Encoding\(\$false, \$true\)' -and $qualification -match 'Lockfile encoding is not UTF-8') -Message 'Lockfile newline canonicalization must fail closed for non-UTF-8 data.'
Assert-Condition -Condition ($qualification -match 'Resolve-ContractArtifactPath' -and $qualification -match 'Assert-ArtifactSourceIsInsideWorkspace' -and $qualification -match 'Artifact source path contains a reparse point' -and $qualification -match 'OrdinalIgnoreCase' -and $qualification -match 'Windows-colliding trailing dot or space' -and $qualification -match 'ADS or drive separator') -Message 'Artifact path validation must canonicalize within the workspace and reject Windows collisions/ADS.'
Assert-Condition -Condition ($qualification -match 'Get-CanonicalArtifactInputPaths' -and $qualification -notmatch 'ARTIFACT_PATHS\.Split\('';''\) \| ForEach-Object \{ \$_\.Trim\(\) \}') -Message 'Artifact input must be validated before any trimming.'
Assert-Condition -Condition ($qualification -match 'artifacts = \$records\.ToArray\(\)' -and $qualification -notmatch 'artifacts = @\(\$records\)') -Message 'Manifest must materialize List[object] artifacts with ToArray().'

# Qualification producer contract must exactly match the promotion consumer contract.
Assert-Condition -Condition ($qualification -match '(?m)^\s+profile_path:' -and $macosQualification -match '(?m)^\s+profile_path:') -Message 'Both qualification templates must receive profile_path.'
Assert-Condition -Condition ($qualification -match 'profileRawBytesSha256' -and $macosQualification -match 'profileRawBytesSha256') -Message 'Both qualification templates must raw-byte bind the profile.'
Assert-Condition -Condition ($qualification -match 'contractRawBytesSha256' -and $macosQualification -match 'contractRawBytesSha256') -Message 'Both qualification ledgers/manifests must carry the common contract hash.'
$windowsCommonContract = [regex]::Match($qualification, '(?m)^\s*const contract = \{ schemaVersion: 2, stage: ''qualification''.*$').Value.Trim()
$macosCommonContract = [regex]::Match($macosQualification, '(?m)^\s*const contract = \{ schemaVersion: 2, stage: ''qualification''.*$').Value.Trim()
Assert-Condition -Condition (-not [string]::IsNullOrWhiteSpace($windowsCommonContract) -and $windowsCommonContract -eq $macosCommonContract) -Message 'Windows and macOS must generate byte-identical common release contract shapes.'

$producerContracts = @(
    [pscustomobject]@{ platform = 'windows'; content = $qualification; artifactName = 'qualified-windows' },
    [pscustomobject]@{ platform = 'macos'; content = $macosQualification; artifactName = 'qualified-macos' }
)
foreach ($producer in $producerContracts) {
    Assert-Condition -Condition ($producer.content -match ('(?m)^\s+name:\s*' + [regex]::Escape($producer.artifactName) + '\s*$')) -Message "$($producer.platform) upload artifact name must exactly equal profile artifactName."
    Assert-Condition -Condition ($producer.content -notmatch ('name:\s*' + [regex]::Escape($producer.artifactName) + '-\$\{\{')) -Message "$($producer.platform) qualification artifact name must not drift dynamically."
    foreach ($required in @('release-bundle', 'schemaVersion', 'releaseCreated', 'contractRawBytesSha256', 'profileRawBytesSha256', 'artifacts', 'evidence', 'signing', 'release-contract.json', 'run-ledger.json', 'signing.json', 'SHA256SUMS.txt')) {
        Assert-Condition -Condition ($producer.content -match [regex]::Escape($required)) -Message "$($producer.platform) producer contract is missing $required."
    }
}
foreach ($consumerToken in @('manifest.schemaVersion !== 2', 'manifest.releaseCreated !== false', 'manifest.contractRawBytesSha256', 'manifest.profileRawBytesSha256', 'release-contract.json', 'run-ledger.json', 'release-bundle/', 'manifest.signing', 'SHA256SUMS.txt')) {
    Assert-Condition -Condition ($promotionEngine -match [regex]::Escape($consumerToken)) -Message "Promotion engine consumer contract is missing $consumerToken."
}
Assert-Condition -Condition ($macosQualification -match 'macos-assets\.json' -and $macosQualification -match 'qualification artifact file set is not exact') -Message 'macOS generic finalizer must consume only the platform asset map and fail closed on the exact output set.'

Assert-Condition -Condition ($promotion -notmatch 'promotion_node_version') -Message 'Promotion must not expose a user-controlled verifier Node input.'
Assert-Condition -Condition ($promotion -match "node-version: '22\.23\.1'" -and $promotion -match 'node --version.*v22\.23\.1') -Message 'Promotion must use and verify exact fixed Node 22.23.1.'
Assert-Condition -Condition ($promotion -match 'not the application toolchain') -Message 'Promotion must distinguish verifier Node from the app toolchain.'
Assert-Condition -Condition ($promotion -match 'id:\s*upload-verified' -and $promotion -match 'verified_artifact_digest') -Message 'Promotion upload must persist immutable artifact attestation metadata.'

$allPwsh = $qualificationBlocks | ForEach-Object { $_.script }
$helperScript = $allPwsh -join [Environment]::NewLine
$artifactFunction = Get-FunctionDefinition -Script $helperScript -Name 'Resolve-ContractArtifactPath'
$artifactInputFunction = Get-FunctionDefinition -Script $helperScript -Name 'Get-CanonicalArtifactInputPaths'
$newlineFunction = Get-FunctionDefinition -Script $helperScript -Name 'Get-NewlineCanonicalBytes'
$temporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('windows-cloud-release-workflow-assets-' + [Guid]::NewGuid().ToString('N'))
try {
    [System.IO.Directory]::CreateDirectory($temporaryRoot) | Out-Null
    . ([scriptblock]::Create($artifactFunction))
    . ([scriptblock]::Create($artifactInputFunction))
    $canonical = Resolve-ContractArtifactPath -Workspace $temporaryRoot -Candidate 'release\App.exe'
    Assert-Condition -Condition ($canonical -eq 'release/App.exe') -Message 'Artifact helper must return a workspace-relative canonical path.'
    foreach ($invalidPath in @('..\outside.exe', 'C:\outside.exe', 'release\asset.exe:stream', 'release\asset.exe.', 'release\asset.exe ', 'release\\asset.exe')) {
        Assert-Throws -Action { Resolve-ContractArtifactPath -Workspace $temporaryRoot -Candidate $invalidPath | Out-Null } -Message "Artifact helper must reject $invalidPath"
    }
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
    Assert-Condition -Condition $seen.Add((Resolve-ContractArtifactPath -Workspace $temporaryRoot -Candidate 'release\App.exe')) -Message 'First artifact path must be accepted.'
    Assert-Condition -Condition (-not $seen.Add((Resolve-ContractArtifactPath -Workspace $temporaryRoot -Candidate 'release\app.exe'))) -Message 'Case-insensitive artifact collision must be rejected.'
    $validInputPaths = @(Get-CanonicalArtifactInputPaths -Workspace $temporaryRoot -ArtifactPaths 'release\App.exe;release\latest.yml')
    Assert-Condition -Condition ($validInputPaths.Count -eq 2 -and $validInputPaths[0] -eq 'release/App.exe' -and $validInputPaths[1] -eq 'release/latest.yml') -Message 'Artifact input helper must preserve and canonicalize exact paths.'
    foreach ($invalidArtifactInput in @('release\asset.exe ', 'release\asset.exe.', 'release\asset.exe;   ', 'release\asset.exe;', ('release\asset.exe;' + [Environment]::NewLine))) {
        Assert-Throws -Action { Get-CanonicalArtifactInputPaths -Workspace $temporaryRoot -ArtifactPaths $invalidArtifactInput | Out-Null } -Message "Artifact input helper must fail closed for $invalidArtifactInput"
    }

    $manifestRecords = New-Object System.Collections.Generic.List[object]
    $manifestRecords.Add([pscustomobject]@{ path = 'release/app.exe'; rawBytesSha256 = '00' }) | Out-Null
    $manifestConstruction = [ordered]@{
        schemaVersion = 2
        artifacts = $manifestRecords.ToArray()
        evidence = @()
    }
    $manifestRoundTrip = ($manifestConstruction | ConvertTo-Json -Depth 8 | ConvertFrom-Json)
    $manifestArtifacts = @($manifestRoundTrip.artifacts)
    Assert-Condition -Condition ($manifestArtifacts.Count -eq 1 -and $manifestArtifacts[0].path -eq 'release/app.exe') -Message 'Manifest construction must execute with List[object].ToArray().'

    . ([scriptblock]::Create($newlineFunction))
    $newlineFixture = [byte[]]@(0xef, 0xbb, 0xbf, 0x41, 0x0d, 0x0a, 0xc3, 0xa9, 0x0d, 0x5a, 0x0a, 0x7f)
    $expectedCanonical = [byte[]]@(0xef, 0xbb, 0xbf, 0x41, 0x0a, 0xc3, 0xa9, 0x0a, 0x5a, 0x0a, 0x7f)
    $actualCanonical = Get-NewlineCanonicalBytes -Bytes $newlineFixture
    Assert-Condition -Condition (Test-ByteArraysEqual -Actual ([byte[]]$actualCanonical) -Expected $expectedCanonical) -Message 'BOM-bearing UTF-8 lockfile canonicalization must change only CRLF/CR to LF.'
    Assert-Condition -Condition (Test-ByteArraysEqual -Actual (Get-ByteArrayWithoutNewlineBytes -Bytes ([byte[]]$actualCanonical)) -Expected (Get-ByteArrayWithoutNewlineBytes -Bytes $newlineFixture)) -Message 'Lockfile canonicalization must preserve every non-newline byte.'
    Assert-Throws -Action { Get-NewlineCanonicalBytes -Bytes ([byte[]]@(0xff, 0xfe, 0x41, 0x00)) | Out-Null } -Message 'Non-UTF-8 lockfile bytes must fail closed.'
}
finally {
    if (Test-Path -LiteralPath $temporaryRoot) {
        Remove-Item -LiteralPath $temporaryRoot -Recurse -Force
    }
}

$preflight = Get-Content -LiteralPath $preflightPath -Raw
$preflightTest = Get-Content -LiteralPath $preflightTestPath -Raw
foreach ($required in @('--no-optional-locks', 'GIT_OPTIONAL_LOCKS', 'core.fsmonitor=false', 'ReparsePoint', 'visitedDirectories')) {
    Assert-Condition -Condition ($preflight -match [regex]::Escape($required)) -Message "Preflight is missing required read-only/reparse guard: $required"
}
foreach ($required in @('Initialize-TestGitRepository', 'Get-TreeFingerprint', 'WCR_TEST_HOOK_SENTINEL', 'Junction', 'electron-win-only', 'dotnet-plain')) {
    Assert-Condition -Condition ($preflightTest -match [regex]::Escape($required)) -Message "Preflight test is missing required regression coverage: $required"
}

foreach ($referencePath in @($evidenceReferencePath, $contractReferencePath, $adapterReferencePath)) {
    $reference = Get-Content -LiteralPath $referencePath -Raw
    Assert-Condition -Condition ($reference -match '(?i)signing') -Message "Reference must define signing evidence for every stack: $referencePath"
    Assert-Condition -Condition ($reference -match '(?i)unsigned') -Message "Reference must disclose unsigned distribution impact: $referencePath"
}
$evidenceReference = Get-Content -LiteralPath $evidenceReferencePath -Raw
Assert-Condition -Condition ($evidenceReference -match '(?m)^\s+signing\.json$') -Message 'Evidence artifact tree must include acceptance/signing.json.'
$ledgerDescription = ([regex]::Match($evidenceReference, '(?m)^`run-ledger\.json`.*$')).Value
Assert-Condition -Condition ($ledgerDescription -match '上传前可知' -and $ledgerDescription -match '只能在上传后' -and $ledgerDescription -match '不要回写') -Message 'Run ledger documentation must place upload-after artifact metadata outside the ledger.'
Assert-Condition -Condition ($evidenceReference -match 'job outputs' -and $evidenceReference -match 'step summary' -and $evidenceReference -match '不回写') -Message 'Upload-after artifact metadata must be documented as outer attestation.'

[Console]::Out.WriteLine('{"passed":true,"checks":"pwsh-parser,yaml-basics,workflow-header-pollution,github-expression-delimiters,immutable-actions,contract-order,independent-evidence,manifest-list-materialization,qualification-promotion-contract,exact-bundle-set,profile-binding,artifact-attestation,lockfile-canonicalization,artifact-path-inputs,diagnostics,preflight-guards,signing-references"}')
