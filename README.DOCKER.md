# Building and running the project with Docker (local)

This repository includes a `Dockerfile` suitable for building a container image for the Django app.

Build the image locally:

```powershell
# from project root
docker build -t irib-programs:local .
```

Run a container (development, with an ephemeral DB):

```powershell
# map port 8000 from container to host
docker run --rm -p 8000:8000 \
  -e DEBUG=1 \
  -e DJANGO_SETTINGS_MODULE=irib_programs.settings \
  irib-programs:local
```

Run migrations inside the container (recommended before first run):

```powershell
# run a one-off migrations command
docker run --rm -it irib-programs:local python manage.py migrate
```

Create a superuser interactively:

```powershell
docker run --rm -it irib-programs:local python manage.py createsuperuser
```

Notes
- The `Dockerfile` installs system libraries required by optional components such as WeasyPrint. If you don't need PDF generation, you can slim this down.
- The local Docker build requires a running Docker daemon (Docker Desktop on Windows). If you encounter daemon connection errors, start Docker Desktop and retry the `docker build` command.
- For CI, place the `docker build` step in your pipeline or use GitHub Actions `build` job.
