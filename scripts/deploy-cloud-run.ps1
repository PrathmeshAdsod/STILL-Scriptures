param(
  [Parameter(Mandatory = $true)][string]$ProjectId,
  [string]$Region = 'us-central1',
  [string]$Service = 'still-api',
  [Parameter(Mandatory = $true)][string]$Image,
  [Parameter(Mandatory = $true)][string]$RunServiceAccount,
  [Parameter(Mandatory = $true)][string]$FirebaseStorageBucket,
  [Parameter(Mandatory = $true)][string]$WorkerBaseUrl,
  [Parameter(Mandatory = $true)][string]$WorkerInvokerServiceAccount,
  [string]$CloudTasksQueue = 'still-analysis',
  [string]$CorsOrigin
)

$ErrorActionPreference = 'Stop'
if (-not $CorsOrigin) { $CorsOrigin = "https://$ProjectId.web.app" }
$envVars = "APP_MODE=production,USE_PROVIDER_FIXTURES=false,LOCAL_WORKER_ENABLED=false,GOOGLE_CLOUD_PROJECT=$ProjectId,FIREBASE_PROJECT_ID=$ProjectId,FIREBASE_STORAGE_BUCKET=$FirebaseStorageBucket,GOOGLE_CLOUD_LOCATION=$Region,CLOUD_TASKS_QUEUE=$CloudTasksQueue,WORKER_BASE_URL=$WorkerBaseUrl,WORKER_INVOKER_SERVICE_ACCOUNT=$WorkerInvokerServiceAccount,CORS_ORIGINS=[`"$CorsOrigin`"]"

gcloud run deploy $Service --project $ProjectId --region $Region --image $Image --service-account $RunServiceAccount --no-allow-unauthenticated --port 8080 --set-env-vars $envVars
Write-Output 'Deploy complete. Attach Gemini, Gloo, and YouVersion secrets; grant Cloud Tasks OIDC and Gemini source-bucket IAM before accepting traffic.'
