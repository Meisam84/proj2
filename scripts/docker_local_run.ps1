# docker_local_run.ps1
# Helper script to build and run the Django project image locally on Windows PowerShell.
# - Checks Docker availability
# - Builds image
# - Finds a free host port (starting from 8000)
# - Runs container mapping hostPort:8000

Param(
    [switch]$RunTests  # if set, run `python manage.py test` inside the built image instead of running the server
)

function ExitWith($msg, $code=1) {
    Write-Host $msg -ForegroundColor Red
    exit $code
}

# Check Docker
try {
    docker version > $null 2>&1
} catch {
    ExitWith "Docker daemon not reachable. Please start Docker Desktop (Windows) or ensure the Docker daemon is running."
}

# Build image
Write-Host "Building Docker image 'irib-programs:local'..."
$build = docker build -t irib-programs:local .
if ($LASTEXITCODE -ne 0) { ExitWith "Docker build failed." }

if ($RunTests) {
    Write-Host "Running Django tests inside container..."
    docker run --rm -it irib-programs:local python manage.py test
    exit $LASTEXITCODE
}

# Find free port starting at 8000
$hostPort = 8000
function PortInUse($p) {
    $res = Test-NetConnection -ComputerName 127.0.0.1 -Port $p -WarningAction SilentlyContinue
    return $res.TcpTestSucceeded
}
while (PortInUse $hostPort) {
    $hostPort++
    if ($hostPort -gt 9000) { ExitWith "Could not find free port between 8000 and 9000." }
}

Write-Host "Starting container, mapping host port $hostPort -> container:8000"
Write-Host "Run 'docker logs -f <container-id>' to stream logs, or visit http://localhost:$hostPort/"

# Run in interactive detached mode
$containerId = docker run -d -p $hostPort`:8000 irib-programs:local
if ($LASTEXITCODE -ne 0) { ExitWith "Failed to start container." }

Write-Host "Container started (ID: $containerId). Application should be available at http://localhost:$hostPort/" -ForegroundColor Green
Write-Host "To stop the container: docker stop $containerId"

exit 0
