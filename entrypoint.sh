#!/bin/sh

uv run alembic upgrade head

uv run uvicorn --host 0.0.0.0 --port 8000 --reload app.main:app