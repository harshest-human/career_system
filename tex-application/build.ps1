$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $projectDir

try {
    $outputDir = Join-Path $projectDir 'build'
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

    $documents = @('cv-en.tex', 'cover-letter-en.tex', 'cv-de.tex', 'cover-letter-de.tex')
    foreach ($document in $documents) {
        Write-Host "Building $document"
        foreach ($pass in 1..2) {
            & xelatex -interaction=nonstopmode -halt-on-error "-output-directory=$outputDir" $document
            if ($LASTEXITCODE -ne 0) { throw "LaTeX build failed for $document (pass $pass)" }
        }
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($document)
        $pdfPath = Join-Path $outputDir "$stem.pdf"
        $pngPrefix = Join-Path $outputDir $stem
        if (Get-Command pdftoppm -ErrorAction SilentlyContinue) {
            & pdftoppm -png -r 150 $pdfPath $pngPrefix
        }
    }
    Write-Host "PDFs and PNG previews created in $outputDir"
}
finally {
    Pop-Location
}
