$owner = "zhjxahsc0120-sys"
$repo = "ESG-project"
$logPath = Join-Path $PSScriptRoot "pr-checker.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logPath -Append
}

function Check-PR {
    param([int]$PRNumber)
    $apiUrl = "https://api.github.com/repos/$owner/$repo/issues/$PRNumber/comments"

    try {
        $response = Invoke-RestMethod -Uri $apiUrl -Method Get -ErrorAction Stop
        $codexComments = $response | Where-Object { $_.user.login -eq "codex" -or $_.body -match "review" }

        if ($codexComments) {
            $latestComment = $codexComments[-1]
            $message = "🚨 PR #$PRNumber 有新的 Codex 审查意见！`n`n$($latestComment.body.Substring(0, [Math]::Min(200, $latestComment.body.Length)))"
            Write-Log $message
            Write-Host $message
            Add-Type -AssemblyName System.Windows.Forms
            $null = [System.Windows.Forms.MessageBox]::Show($message, "PR 审查通知", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        } else {
            Write-Log "✓ PR #$PRNumber 暂无新审查意见"
            Write-Host "✓ PR #$PRNumber 暂无新审查意见"
        }
    } catch {
        Write-Log "⚠️ 检查 PR #$PRNumber 失败: $_"
        Write-Host "⚠️ 检查 PR #$PRNumber 失败: $_"
    }
}

function Check-AllPRs {
    $apiUrl = "https://api.github.com/repos/$owner/$repo/pulls?state=open"

    try {
        $response = Invoke-RestMethod -Uri $apiUrl -Method Get -ErrorAction Stop

        if (-not $response) {
            Write-Log "✓ 暂无开放的 PR"
            Write-Host "✓ 暂无开放的 PR"
            return
        }

        foreach ($pr in $response) {
            Check-PR -PRNumber $pr.number
        }
    } catch {
        Write-Log "⚠️ 获取 PR 列表失败: $_"
        Write-Host "⚠️ 获取 PR 列表失败: $_"
    }
}

if ($args[0] -eq "--all") {
    Check-AllPRs
} elseif ($args[0] -match '^\d+$') {
    Check-PR -PRNumber ([int]$args[0])
} else {
    Write-Host "Usage: check-pr.ps1 <pr-number> | --all"
    Write-Log "Usage: check-pr.ps1 <pr-number> | --all"
    exit 1
}
