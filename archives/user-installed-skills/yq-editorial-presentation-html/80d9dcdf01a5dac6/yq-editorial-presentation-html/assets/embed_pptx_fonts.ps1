[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$InputPath,
  [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = "Stop"
$inputFile = (Resolve-Path -LiteralPath $InputPath).Path
$outputFile = [IO.Path]::GetFullPath($OutputPath)
if ([IO.Path]::GetExtension($inputFile) -ne ".pptx" -or [IO.Path]::GetExtension($outputFile) -ne ".pptx") {
  throw "InputPath and OutputPath must both be .pptx files."
}
if ($inputFile -eq $outputFile) {
  throw "OutputPath must differ from InputPath."
}
if (Test-Path -LiteralPath $outputFile) {
  Remove-Item -LiteralPath $outputFile -Force
}

$powerPoint = $null
$presentation = $null
try {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $sourceArchive = [IO.Compression.ZipFile]::OpenRead($inputFile)
  try {
    $fontNames = @(
      $sourceArchive.Entries |
        Where-Object { $_.FullName -like "ppt/slides/*.xml" } |
        ForEach-Object {
          $reader = New-Object IO.StreamReader($_.Open())
          try {
            [regex]::Matches($reader.ReadToEnd(), 'typeface="([^"]+)"') |
              ForEach-Object { $_.Groups[1].Value }
          }
          finally {
            $reader.Dispose()
          }
        } |
        Where-Object { $_ -and $_ -notlike "+*" } |
        Sort-Object -Unique
    )
  }
  finally {
    $sourceArchive.Dispose()
  }

  $powerPoint = New-Object -ComObject PowerPoint.Application
  $powerPointExe = Join-Path ([string]$powerPoint.Path) "POWERPNT.EXE"
  if (-not (Test-Path -LiteralPath $powerPointExe)) {
    throw "Font embedding requires desktop Microsoft PowerPoint. The registered PowerPoint.Application COM server is '$($powerPoint.Path)' (often WPS Office), which ignores the EmbedFonts flag."
  }
  # ReadOnly = 0 is required: PowerPoint silently skips font embedding when
  # SaveAs starts from a read-only presentation.
  $presentation = $powerPoint.Presentations.Open($inputFile, 0, 0, 0)

  # ppSaveAsOpenXMLPresentation = 24, msoTrue = -1.
  $presentation.SaveAs($outputFile, 24, -1)
  $presentation.Close()
  $presentation = $null
  $powerPoint.Quit()
  $powerPoint = $null

  $archive = [IO.Compression.ZipFile]::OpenRead($outputFile)
  try {
    $fontEntries = @($archive.Entries | Where-Object { $_.FullName -like "ppt/fonts/*" })
    $presentationEntry = $archive.GetEntry("ppt/presentation.xml")
    if ($fontEntries.Count -eq 0 -or $null -eq $presentationEntry) {
      throw "PowerPoint completed SaveAs but no embedded font parts were found."
    }
    $reader = New-Object IO.StreamReader($presentationEntry.Open())
    try {
      $presentationXml = $reader.ReadToEnd()
    }
    finally {
      $reader.Dispose()
    }
    if ($presentationXml -notmatch "embeddedFontLst") {
      throw "PowerPoint output has font parts but no embeddedFontLst declaration."
    }
    [xml]$presentationDocument = $presentationXml
    $embeddedFontNames = @(
      $presentationDocument.SelectNodes("//*[local-name()='embeddedFont']/*[local-name()='font']") |
        ForEach-Object { [string]$_.typeface } |
        Where-Object { $_ } |
        Sort-Object -Unique
    )
    $missingFonts = @(
      $fontNames | Where-Object {
        $requested = $_
        -not ($embeddedFontNames | Where-Object { $_ -ieq $requested })
      }
    )
    if ($missingFonts.Count -gt 0) {
      throw "PowerPoint did not embed every requested font. Missing: $($missingFonts -join ', ')"
    }
  }
  finally {
    $archive.Dispose()
  }

  [pscustomobject]@{
    embedded = $true
    output = $outputFile
    requested_fonts = $fontNames
    embedded_fonts = $embeddedFontNames
    font_part_count = $fontEntries.Count
  } | ConvertTo-Json -Depth 5 -Compress
}
finally {
  if ($null -ne $presentation) {
    try { $presentation.Close() } catch {}
  }
  if ($null -ne $powerPoint) {
    try { $powerPoint.Quit() } catch {}
  }
  foreach ($comObject in @($presentation, $powerPoint)) {
    if ($null -ne $comObject) {
      try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($comObject) } catch {}
    }
  }
}
