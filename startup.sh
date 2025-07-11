#!/bin/bash
cd app
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --chdir app --bind 0.0.0.0:$PORT

