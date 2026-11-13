[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputHtml,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$OutputDocx
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'HTML 转 Word 脚本仅支持安装了 Microsoft Word 的 Windows 环境。'
}

$inputItem = Get-Item -LiteralPath $InputHtml -ErrorAction Stop
if ($inputItem.PSIsContainer) {
    throw "输入必须是 HTML 文件：$InputHtml"
}
$inputPath = $inputItem.FullName
if ([IO.Path]::GetExtension($inputPath) -notin @('.html', '.htm')) {
    throw "输入文件扩展名必须是 .html 或 .htm：$inputPath"
}
if ($inputItem.Length -eq 0) {
    throw "输入 HTML 是空文件：$inputPath"
}

if ([IO.Path]::IsPathRooted($OutputDocx)) {
    $outputPath = [IO.Path]::GetFullPath($OutputDocx)
} else {
    $outputPath = [IO.Path]::GetFullPath((Join-Path -Path (Get-Location).Path -ChildPath $OutputDocx))
}
if ([IO.Path]::GetExtension($outputPath) -ne '.docx') {
    throw "输出文件扩展名必须是 .docx：$outputPath"
}
if (Test-Path -LiteralPath $outputPath) {
    throw "输出文件已存在，请另选文件名，避免覆盖：$outputPath"
}
$outputParent = Split-Path -Path $outputPath -Parent
if (-not (Test-Path -LiteralPath $outputParent -PathType Container)) {
    throw "输出目录不存在，请先创建：$outputParent"
}

$skillRoot = [IO.Path]::GetFullPath((Join-Path -Path $PSScriptRoot -ChildPath '..'))
$skillPrefix = $skillRoot.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if ($outputPath.StartsWith($skillPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'DOCX 必须保存到用户输出目录，不能写回 Skill 目录。'
}

$utf8Strict = New-Object System.Text.UTF8Encoding -ArgumentList @($false, $true)
try {
    $html = [IO.File]::ReadAllText($inputPath, $utf8Strict)
} catch [Text.DecoderFallbackException] {
    throw "输入 HTML 不是有效 UTF-8，请先转换为 UTF-8：$inputPath"
}

# 删除浏览器编辑功能和主动内容；不修改用户的原 HTML。
$html = [regex]::Replace($html, '(?i)<script\b[^>]*>[\s\S]*?</script\s*>', '')
$html = [regex]::Replace($html, '(?i)<div\b[^>]*class="[^"]*resume-toolbar[^"]*"[^>]*>[\s\S]*?</div\s*>', '')
$html = [regex]::Replace($html, "(?i)<div\b[^>]*class='[^']*resume-toolbar[^']*'[^>]*>[\s\S]*?</div\s*>", '')
$html = [regex]::Replace($html, '(?i)<(?:iframe|object|embed)\b[^>]*>[\s\S]*?</(?:iframe|object|embed)\s*>', '')
$html = [regex]::Replace($html, '(?i)<(?:iframe|object|embed)\b[^>]*/?>', '')

# 临时副本位于系统临时目录，通过 base 保持原 HTML 的相对图片和 CSS 路径可用。
if ($html -notmatch '(?i)<base\b') {
    $inputDirectory = Split-Path -Path $inputPath -Parent
    $baseUri = [Uri]::new($inputDirectory.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar)
    $baseTag = '<base href="' + [Security.SecurityElement]::Escape($baseUri.AbsoluteUri) + '">'
    $baseTagForReplacement = $baseTag
    $html = [regex]::Replace(
        $html,
        '(?i)<head\b[^>]*>',
        { param($match) $match.Value + "`r`n  $baseTagForReplacement" },
        1
    )
    if ($html -notmatch '(?i)<base\b') {
        throw 'HTML 缺少 <head>，无法建立资源路径。请先修复 HTML 结构。'
    }
}

$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$tempDirectory = [IO.Path]::GetFullPath((Join-Path -Path $tempRoot -ChildPath ('resume-html-docx-' + [Guid]::NewGuid().ToString('N'))))
$tempHtml = Join-Path -Path $tempDirectory -ChildPath 'resume.html'
$word = $null
$document = $null

try {
    [void][IO.Directory]::CreateDirectory($tempDirectory)
    [IO.File]::WriteAllText($tempHtml, $html, (New-Object System.Text.UTF8Encoding -ArgumentList @($false)))

    try {
        $word = New-Object -ComObject Word.Application
    } catch {
        throw '无法启动 Microsoft Word。请确认已安装桌面版 Word，或改用宿主 DOCX 能力。'
    }

    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $word.Options.UpdateLinksAtOpen = $false

    $document = $word.Documents.Open($tempHtml, $false, $true, $false)
    $document.SaveAs2($outputPath, 16)
    $document.Close(0)
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
    $document = $null

    if (-not (Test-Path -LiteralPath $outputPath -PathType Leaf)) {
        throw "Word 未生成预期文件：$outputPath"
    }
    if ((Get-Item -LiteralPath $outputPath).Length -eq 0) {
        throw "Word 生成了空文件，请检查源 HTML：$outputPath"
    }

    Write-Output "已生成 DOCX：$outputPath"
    Write-Output '请继续检查 A4 页面、分页、字体、链接、图片和 ATS 阅读顺序；HTML 与 Word 的分页可能存在差异。'
} finally {
    if ($null -ne $document) {
        try { $document.Close(0) } catch { Write-Warning "关闭 Word 文档失败：$($_.Exception.Message)" }
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) } catch { }
    }
    if ($null -ne $word) {
        try { $word.Quit() } catch { Write-Warning "退出 Word 失败：$($_.Exception.Message)" }
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) } catch { }
    }

    if (Test-Path -LiteralPath $tempDirectory -PathType Container) {
        $resolvedTemp = (Resolve-Path -LiteralPath $tempDirectory).Path
        $resolvedParent = Split-Path -Path $resolvedTemp -Parent
        if ($resolvedParent.TrimEnd([IO.Path]::DirectorySeparatorChar) -ne $tempRoot.TrimEnd([IO.Path]::DirectorySeparatorChar)) {
            throw "临时目录位置异常，停止清理：$resolvedTemp"
        }
        Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
    }
}
