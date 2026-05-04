param(
    [Parameter(Mandatory = $true)]
    [string]$branchName
)

Write-Host "========================================="
Write-Host "🚀 Iniciando script de troca de branch"
Write-Host "========================================="
Write-Host ""

# Verifica se estamos em um repositório git
if (-not (Test-Path ".git")) {
    Write-Host "❌ Este diretório não é um repositório Git."
    exit 1
}

# 1. Checkout main
Write-Host "🔄 Fazendo checkout para main..."
git checkout main

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao fazer checkout da main."
    exit 1
}

# 2. Pull main
Write-Host "⬇️ Atualizando main (git pull)..."
git pull origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao dar pull na main."
    exit 1
}

Write-Host ""
Write-Host "⏸️ Pressione qualquer tecla para continuar..."
[void][System.Console]::ReadKey($true)

Write-Host ""

# 3. Checkout para branch informada
Write-Host "🔀 Criando a branch: $branchName"

git checkout -b $branchName

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Não foi possível fazer checkout da branch."
    exit 1
}

Write-Host ""
Write-Host "✅ Pronto! Agora você está na branch: $branchName"
Write-Host "========================================="