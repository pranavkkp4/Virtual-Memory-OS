param(
    [string[]]$BenchmarkArgs = @('--experiment', 'all'),
    [string]$PythonExe = 'python',
    [string]$ResultsDir = 'results'
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$resultsRoot = Join-Path $repoRoot $ResultsDir
$metadataDir = Join-Path $resultsRoot 'metadata'
New-Item -ItemType Directory -Force -Path $metadataDir | Out-Null

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$runId = "${timestamp}_$PID"
$metadataPath = Join-Path $metadataDir "run_environment_$runId.json"
$outputPath = Join-Path $metadataDir "run_output_$runId.log"
$stdoutPath = Join-Path $metadataDir "run_output_$runId.stdout.log"
$stderrPath = Join-Path $metadataDir "run_output_$runId.stderr.log"

function Get-HostMetadata {
    $cpuName = $null
    $osCaption = $null
    $ramGb = $null
    try {
        $cpuName = (Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)
        $osCaption = (Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)
        $ramBytes = (Get-CimInstance Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory)
        $ramGb = [math]::Round(([double]$ramBytes / 1GB), 2)
    } catch {
        $cpuName = $env:PROCESSOR_IDENTIFIER
        $osCaption = [System.Environment]::OSVersion.VersionString
        $ramGb = $null
    }

    return [ordered]@{
        hostname = $env:COMPUTERNAME
        os = $osCaption
        cpu = $cpuName
        memory_gb = $ramGb
        powershell_version = $PSVersionTable.PSVersion.ToString()
    }
}

$pythonVersion = & $PythonExe --version 2>&1
$gitCommit = ''
try {
    $gitCommit = (& git rev-parse HEAD 2>$null | Out-String).Trim()
} catch {
    $gitCommit = ''
}

$metadata = [ordered]@{
    timestamp = (Get-Date).ToString('o')
    mode = 'quiet'
    repo_root = $repoRoot
    results_dir = $resultsRoot
    host = Get-HostMetadata
    python_executable = $PythonExe
    python_version = ($pythonVersion -join ' ').Trim()
    git_commit = $gitCommit
    benchmark_args = $BenchmarkArgs
    process_priority = 'BelowNormal'
    command = @($PythonExe, 'experiments\run_all_experiments.py') + $BenchmarkArgs
}

$metadataJson = $metadata | ConvertTo-Json -Depth 6
$metadataJson | Out-File -Encoding utf8 -FilePath $metadataPath

$argList = @('experiments\run_all_experiments.py') + $BenchmarkArgs

$process = Start-Process `
    -FilePath $PythonExe `
    -ArgumentList $argList `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -PassThru

if ($null -eq $process) {
    throw "Failed to start benchmark process."
}

if ($process -ne $null) {
    $process.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
}

$process.WaitForExit()

$stdout = Get-Content $stdoutPath -Raw
$stderr = Get-Content $stderrPath -Raw

Set-Content -Encoding UTF8 -Path $outputPath -Value ($stdout + "`r`n" + $stderr)

if ([int]$process.ExitCode -ne 0) {
    throw "Benchmark run failed with exit code $($process.ExitCode). See $outputPath"
}

Write-Host "Quiet benchmark complete."
Write-Host "Metadata: $metadataPath"
Write-Host "Log: $outputPath"
