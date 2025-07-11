#!/bin/bash

# Run the FastAPI app using gunicorn with uvicorn workers
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT