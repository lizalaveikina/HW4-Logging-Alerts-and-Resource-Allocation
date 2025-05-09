# Homework 4: Logging, Alerts, and Resource Allocation

## Project Overview

This FastAPI-based system handles user input, logs events, detects sensitive information, and delegates background processing to Celery. Redis is used as the message broker. The app is container-ready and extensible.

---

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## How to Run Locally

### 1. Run Redis
```bash
redis-server
```

### 2. Start Celery worker
```bash
celery -A celery_worker.celery_app worker --loglevel=info
```

### 3. Start FastAPI server
```bash
uvicorn client_service:app --reload
```

---

## Example Test

Send a test request:

```bash
curl -X POST http://127.0.0.1:8000/run -H "Authorization: Bearer Secret123"
```

If input includes personal data like email/phone, an alert report will be generated in `error_reports/`.

---

## Logs and Reports

- All logs are saved in: `logs/app.log`
- Alerts are saved in: `error_reports/alert_<timestamp>.txt`
- Example alert file: `error_reports/alert_2025-05-09_13-58-40.txt`

Example content of alert file:

```
ALERT TYPE: email and phone
TIME: 2025-05-09_13-58-40
DATA: {'name': 'Test User', 'email': 'test@example.com', 'phone': '+380961234567'}
```

---

## System Architecture

### Components

- **Client Service (FastAPI)**  
  Exposes an HTTP endpoint `/run` that performs authorization, logs each request, analyzes the input for personal data, and submits tasks to a Celery worker.

- **Celery Worker**  
  Processes tasks asynchronously. Each task simulates a business process (e.g., transforming input data) and returns a result back to the API.

- **Redis**  
  Acts as a broker between FastAPI and the Celery worker, queuing tasks and managing asynchronous communication.

- **Logging System**  
  Built using Python’s `logging` module. All request events, warnings, and errors are written to `logs/app.log`.

- **Alert Engine**  
  A sub-module inside `client_service.py` that inspects incoming data for sensitive patterns such as emails or Ukrainian phone numbers. If detected, it writes a mini-report into `error_reports/` with timestamp, alert type, and input context.

### Workflow (with execution types)

1. **[Synchronous]** The user sends a `POST` request to `/run` with a bearer token.  
2. **[Synchronous]** FastAPI verifies the token and logs the request using `logging`.  
3. **[Synchronous]** The input is inspected by the alert engine. If email or phone is detected, a `.txt` alert report is created.  
4. **[Asynchronous]** The validated input is sent to a Celery worker via Redis as a background task.  
5. **[Asynchronous]** Celery processes the task and returns the result.  
6. **[Synchronous]** The processed result is logged and returned to the user.    

---

## Resource Scaling Estimation

#### 10 simultaneous users
- The current setup is sufficient: 1 FastAPI instance, 1 Celery worker, and Redis.
- No additional scaling needed.
- Response time remains low, and the system handles input and alerting smoothly.

#### 50 simultaneous users
- **FastAPI**: Run using a process manager like `gunicorn` with 2–4 worker processes.
- **Celery**: Add 1–2 more Celery workers to process background tasks in parallel.
- **Redis**: Monitor usage; single-node Redis is still sufficient at this level.

#### 100+ simultaneous users
- **FastAPI**:
  - Deploy multiple FastAPI instances (containers or processes).
  - Use a load balancer (e.g., Nginx or Traefik) to distribute traffic.
- **Celery**:
  - Add 4–6 Celery workers or deploy workers across multiple machines.
  - Group tasks by queues if needed.
- **Redis**:
  - Consider Redis cluster or hosted solution (e.g., AWS ElastiCache).
  - Monitor latency and memory usage.
- **Logging and Alerts**:
  - Offload logging to ELK stack or cloud logging services for performance.
  - Store alerts in a database or queue for later review if file I/O becomes a bottleneck.

---

### Summary

| Component     | 10 users            | 50 users                        | 100+ users                                   |
|---------------|---------------------|----------------------------------|----------------------------------------------|
| FastAPI       | 1 instance           | Gunicorn 2–4 workers             | Load-balanced API instances                  |
| Celery        | 1 worker             | 2–3 workers                      | 4–6+ workers across machines                 |
| Redis         | Single node         | Single node (monitored)          | Redis cluster / managed Redis                |
| Logging       | Local file          | Local file                       | External service (ELK, cloud logging)        |
| Alert Engine  | Local file reports  | Local file reports               | Queue-based or DB logging of alerts          |

---

## Author

Created by **Yelyzaveta Laveikina**  
Course: *Architecture of IT Solutions*  
University: Ukrainian Catholic University (UCU)
