param(
  [string]$ProjectId = 'still-scriptures',
  [string]$Region = 'asia-south1',
  [string]$Service = 'still-api',
  [string]$Queue = 'still-analysis',
  [string]$ImageTag = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$envPath = Join-Path $repoRoot '.env'
if (-not (Test-Path -LiteralPath $envPath)) { throw 'The ignored root .env is required.' }

function Invoke-Gcloud {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $output = & gcloud @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $output | ForEach-Object { Write-Host $_ }
  } finally {
    $ErrorActionPreference = $previousPreference
  }
  if ($exitCode -ne 0) { throw "gcloud failed: $($Arguments[0..([Math]::Min(2, $Arguments.Count - 1))] -join ' ')" }
}

function Test-GcloudResource {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    & gcloud @Arguments *> $null
    $succeeded = $LASTEXITCODE -eq 0
  } finally {
    $ErrorActionPreference = $previousPreference
  }
  return $succeeded
}

function Read-DotEnv {
  $values = @{}
  foreach ($raw in Get-Content -LiteralPath $envPath) {
    if ($raw -match '^\s*([^#][^=]*)=(.*)$') {
      $name = $matches[1].Trim()
      $value = $matches[2].Trim().Trim('"').Trim("'")
      $values[$name] = $value
    }
  }
  return $values
}

function Add-SecretVersion {
  param([string]$Name, [string]$Value, [string]$RuntimeServiceAccount)
  if ([string]::IsNullOrWhiteSpace($Value)) { throw "Missing value for Secret Manager secret $Name." }
  if (-not (Test-GcloudResource secrets describe $Name --project $ProjectId --format='value(name)')) {
    Invoke-Gcloud secrets create $Name --project $ProjectId --replication-policy=automatic --quiet
  }
  $stagingRoot = Join-Path $repoRoot 'tmp'
  [System.IO.Directory]::CreateDirectory($stagingRoot) | Out-Null
  $stagingPath = Join-Path $stagingRoot ("secret-{0}.txt" -f [guid]::NewGuid().ToString('N'))
  try {
    [System.IO.File]::WriteAllText($stagingPath, $Value, [System.Text.UTF8Encoding]::new($false))
    Invoke-Gcloud secrets versions add $Name --project $ProjectId --data-file=$stagingPath --quiet
  } finally {
    if (Test-Path -LiteralPath $stagingPath) { Remove-Item -LiteralPath $stagingPath -Force }
  }
  Invoke-Gcloud secrets add-iam-policy-binding $Name --project $ProjectId --member="serviceAccount:$RuntimeServiceAccount" --role=roles/secretmanager.secretAccessor --quiet
}

function Set-FirebaseEmailAuthentication {
  $accessToken = (& gcloud auth print-access-token --project $ProjectId).Trim()
  if (-not $accessToken) { throw 'Could not obtain a Google access token for Firebase Authentication configuration.' }
  $headers = @{
    Authorization = "Bearer $accessToken"
    'X-Goog-User-Project' = $ProjectId
  }
  $body = @{
    signIn = @{
      email = @{ enabled = $true; passwordRequired = $true }
      anonymous = @{ enabled = $false }
    }
    emailPrivacyConfig = @{ enableImprovedEmailPrivacy = $true }
    passwordPolicyConfig = @{
      passwordPolicyEnforcementState = 'ENFORCE'
      forceUpgradeOnSignin = $false
      passwordPolicyVersions = @(
        @{ customStrengthOptions = @{ minPasswordLength = 12; maxPasswordLength = 128 } }
      )
    }
  } | ConvertTo-Json -Depth 8 -Compress
  $mask = 'signIn.email,signIn.anonymous,emailPrivacyConfig,passwordPolicyConfig'
  $uri = "https://identitytoolkit.googleapis.com/admin/v2/projects/$ProjectId/config?updateMask=$mask"
  Invoke-RestMethod -Method Patch -Uri $uri -Headers $headers -ContentType 'application/json' -Body $body | Out-Null
}

Push-Location $repoRoot
try {
  $billingJson = & gcloud billing projects describe $ProjectId --format=json 2>$null
  $billing = if ($billingJson) { $billingJson | ConvertFrom-Json } else { $null }
  if (-not $billing -or $billing.billingEnabled -ne $true) {
    throw 'Firebase Blaze billing is not linked. Link billing in the Firebase console, then rerun this script.'
  }

  $values = Read-DotEnv
  foreach ($required in @('GEMINI_API_KEY', 'GLOO_CLIENT_ID', 'GLOO_CLIENT_SECRET', 'YVP_APP_KEY', 'ACCESS_COUPON_CODE')) {
    if ([string]::IsNullOrWhiteSpace($values[$required])) { throw "The ignored .env is missing $required." }
  }

  $apis = @(
    'artifactregistry.googleapis.com', 'cloudbuild.googleapis.com', 'run.googleapis.com',
    'cloudtasks.googleapis.com', 'secretmanager.googleapis.com', 'firestore.googleapis.com',
    'youtube.googleapis.com', 'apikeys.googleapis.com', 'identitytoolkit.googleapis.com'
  )
  Invoke-Gcloud services enable @apis --project $ProjectId --quiet
  Set-FirebaseEmailAuthentication

  $runtimeName = 'still-api-runtime'
  $invokerName = 'still-task-invoker'
  $runtimeAccount = "$runtimeName@$ProjectId.iam.gserviceaccount.com"
  $invokerAccount = "$invokerName@$ProjectId.iam.gserviceaccount.com"
  foreach ($account in @(@{ Name = $runtimeName; Display = 'STILL API runtime' }, @{ Name = $invokerName; Display = 'STILL Cloud Tasks invoker' })) {
    if (-not (Test-GcloudResource iam service-accounts describe "$($account.Name)@$ProjectId.iam.gserviceaccount.com" --project $ProjectId --format='value(email)')) { Invoke-Gcloud iam service-accounts create $account.Name --project $ProjectId --display-name=$account.Display --quiet }
  }

  Invoke-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$runtimeAccount" --role=roles/datastore.user --condition=None --quiet
  Invoke-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$runtimeAccount" --role=roles/cloudtasks.enqueuer --condition=None --quiet
  Invoke-Gcloud iam service-accounts add-iam-policy-binding $invokerAccount --project $ProjectId --member="serviceAccount:$runtimeAccount" --role=roles/iam.serviceAccountUser --quiet

  $buildAccount = (& gcloud builds get-default-service-account --project $ProjectId).Trim()
  if (-not $buildAccount) { throw 'Cloud Build did not return its default service account.' }
  Invoke-Gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:$buildAccount" --role=roles/artifactregistry.writer --condition=None --quiet

  $projectNumber = (& gcloud projects describe $ProjectId --format='value(projectNumber)').Trim()
  $tasksAgent = "service-$projectNumber@gcp-sa-cloudtasks.iam.gserviceaccount.com"
  Invoke-Gcloud iam service-accounts add-iam-policy-binding $invokerAccount --project $ProjectId --member="serviceAccount:$tasksAgent" --role=roles/iam.serviceAccountTokenCreator --quiet

  $youtubeKey = (& gcloud services api-keys list --project $ProjectId --filter='displayName=still-youtube-metadata' --format='value(name)' | Select-Object -First 1).Trim()
  if (-not $youtubeKey) { throw 'The restricted still-youtube-metadata API key is missing.' }
  $youtubeKeyPayload = & gcloud services api-keys get-key-string $youtubeKey --project $ProjectId --format=json | ConvertFrom-Json

  Add-SecretVersion 'still-gemini-api-key' $values['GEMINI_API_KEY'] $runtimeAccount
  Add-SecretVersion 'still-gloo-client-id' $values['GLOO_CLIENT_ID'] $runtimeAccount
  Add-SecretVersion 'still-gloo-client-secret' $values['GLOO_CLIENT_SECRET'] $runtimeAccount
  Add-SecretVersion 'still-yvp-app-key' $values['YVP_APP_KEY'] $runtimeAccount
  Add-SecretVersion 'still-youtube-api-key' $youtubeKeyPayload.keyString $runtimeAccount
  Add-SecretVersion 'still-access-coupon-code' $values['ACCESS_COUPON_CODE'] $runtimeAccount

  if (-not (Test-GcloudResource artifacts repositories describe still --project $ProjectId --location $Region --format='value(name)')) { Invoke-Gcloud artifacts repositories create still --project $ProjectId --location $Region --repository-format=docker --description='STILL production images' --quiet }

  $tag = if ($ImageTag) { $ImageTag } else { (& git rev-parse --short=12 HEAD).Trim() }
  if ($tag -notmatch '^[a-zA-Z0-9._-]+$') { throw 'ImageTag contains unsupported characters.' }
  $image = "$Region-docker.pkg.dev/$ProjectId/still/still-api:$tag"
  if (-not (Test-GcloudResource artifacts docker images describe $image --project $ProjectId --format='value(image_summary.digest)')) {
    Invoke-Gcloud builds submit . --project $ProjectId --config cloudbuild.yaml --substitutions="_REGION=$Region,_TAG=$tag" --quiet
  }

  if (-not (Test-GcloudResource tasks queues describe $Queue --project $ProjectId --location $Region --format='value(name)')) {
    Invoke-Gcloud tasks queues create $Queue --project $ProjectId --location $Region --max-dispatches-per-second=1 --max-concurrent-dispatches=1 --max-attempts=2 --quiet
  } else {
    Invoke-Gcloud tasks queues update $Queue --project $ProjectId --location $Region --max-dispatches-per-second=1 --max-concurrent-dispatches=1 --max-attempts=2 --quiet
  }

  $hostingOrigin = "https://$ProjectId.web.app"
  $environmentValues = [ordered]@{
    APP_MODE = 'production'; USE_PROVIDER_FIXTURES = 'false'; LOCAL_WORKER_ENABLED = 'false'
    GOOGLE_CLOUD_PROJECT = $ProjectId; FIREBASE_PROJECT_ID = $ProjectId; GOOGLE_CLOUD_LOCATION = $Region
    CLOUD_TASKS_QUEUE = $Queue; WORKER_BASE_URL = 'https://pending.invalid'; WORKER_INVOKER_SERVICE_ACCOUNT = $invokerAccount
    CORS_ORIGINS = "[`"$hostingOrigin`"]"; GLOO_ENDPOINT_MODE = 'completions_v2'; GLOO_MAX_CANDIDATES_PER_PROJECT = '1'
    YVP_ALLOWED_BIBLE_IDS = '[3034]'; MAX_VIDEO_DURATION_SECONDS = '360'; FREE_ANALYSIS_LIFETIME_LIMIT = '1'
    ACCESS_ANALYSIS_DAILY_LIMIT = '2'; MAX_ANALYSIS_GLOBAL_PER_DAY = '20'; DAILY_ESCALATION_BUDGET = '0'
  }
  $environmentPath = Join-Path $repoRoot 'tmp/runtime-environment.json'
  [System.IO.File]::WriteAllText($environmentPath, ($environmentValues | ConvertTo-Json -Compress), [System.Text.UTF8Encoding]::new($false))
  $secrets = 'GEMINI_API_KEY=still-gemini-api-key:latest,GLOO_CLIENT_ID=still-gloo-client-id:latest,GLOO_CLIENT_SECRET=still-gloo-client-secret:latest,YVP_APP_KEY=still-yvp-app-key:latest,YOUTUBE_API_KEY=still-youtube-api-key:latest,ACCESS_COUPON_CODE=still-access-coupon-code:latest'
  try {
    Invoke-Gcloud run deploy $Service --project $ProjectId --region $Region --image $image --service-account $runtimeAccount --allow-unauthenticated --port=8080 --cpu=1 --memory=1Gi --min=0 --max=1 --concurrency=20 --timeout=1800 --env-vars-file=$environmentPath --set-secrets=$secrets --quiet
  } finally {
    if (Test-Path -LiteralPath $environmentPath) { Remove-Item -LiteralPath $environmentPath -Force }
  }

  $serviceUrl = (& gcloud run services describe $Service --project $ProjectId --region $Region --format='value(status.url)').Trim()
  if (-not $serviceUrl) { throw 'Cloud Run deployed but did not return a service URL.' }
  Invoke-Gcloud run services update $Service --project $ProjectId --region $Region --update-env-vars="WORKER_BASE_URL=$serviceUrl" --quiet

  $productionEnv = Join-Path $repoRoot 'apps/web/.env.production.local'
  $existingWebEnv = if (Test-Path -LiteralPath $productionEnv) { Get-Content -LiteralPath $productionEnv } else { @() }
  $webValues = @{}
  foreach ($line in $existingWebEnv) { if ($line -match '^([^#][^=]*)=(.*)$') { $webValues[$matches[1].Trim()] = $matches[2].Trim() } }
  $webValues['VITE_APP_MODE'] = 'production'
  $webValues['VITE_USE_PROVIDER_FIXTURES'] = 'false'
  $webValues['VITE_API_BASE_URL'] = '/api'
  $requiredWebValues = @('VITE_FIREBASE_API_KEY', 'VITE_FIREBASE_AUTH_DOMAIN', 'VITE_FIREBASE_PROJECT_ID', 'VITE_FIREBASE_STORAGE_BUCKET', 'VITE_FIREBASE_APP_ID')
  foreach ($required in $requiredWebValues) { if ([string]::IsNullOrWhiteSpace($webValues[$required])) { throw "$productionEnv is missing $required." } }
  $orderedWebKeys = @('VITE_APP_MODE', 'VITE_USE_PROVIDER_FIXTURES', 'VITE_API_BASE_URL', 'VITE_GITHUB_URL') + $requiredWebValues
  [System.IO.File]::WriteAllLines($productionEnv, @($orderedWebKeys | Where-Object { $webValues.ContainsKey($_) } | ForEach-Object { "$_=$($webValues[$_])" }), [System.Text.UTF8Encoding]::new($false))

  & npm run build
  if ($LASTEXITCODE -ne 0) { throw 'The production web build failed.' }
  & firebase deploy --project $ProjectId --only hosting,firestore:rules,firestore:indexes --non-interactive
  if ($LASTEXITCODE -ne 0) { throw 'Firebase deployment failed.' }

  $health = Invoke-RestMethod -Method Get -Uri "$serviceUrl/health" -TimeoutSec 30
  if ($health.status -ne 'ok') { throw 'Cloud Run health check did not return ok.' }
  Write-Output "STILL production deployment is healthy: $hostingOrigin"
} finally {
  Pop-Location
}
