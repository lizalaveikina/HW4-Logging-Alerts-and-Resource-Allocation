from fastapi import FastAPI, Header, HTTPException
import requests
import logging
import os
import re
from datetime import datetime
from celery_worker import process_data

APP_TOKEN = "Secret123"

if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Client Service: connects all services"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
def run(authorization: str = Header(None)):
    logging.info("Received request at /run endpoint")

    if authorization != f"Bearer {APP_TOKEN}":
        logging.warning("Unauthorized access attempt")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logging.info("Authorization successful.")

    # test
    to_process = {"name": "Test User", "email": "test@example.com", "phone": "+380961234567"}
    logging.info(f"Data to process: {to_process}")

    if not os.path.exists("error_reports"):
        os.makedirs("error_reports")

    to_process_str = str(to_process)
    alert_type = None

    if re.search(r"\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b", to_process_str):
        alert_type = "email"
    if re.search(r"\+?380\d{9}|\b0\d{9}\b", to_process_str):
        alert_type = "phone" if not alert_type else "email and phone"

    if alert_type:
        report_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_name = f"error_reports/alert_{report_time}.txt"
        with open(report_name, "w") as report_file:
            report_file.write(f"ALERT TYPE: {alert_type}\n")
            report_file.write(f"TIME: {report_time}\n")
            report_file.write(f"DATA: {to_process_str}\n")
        logging.warning(f"ALERT triggered: {alert_type} — report saved.")

    try:
        task = process_data.delay(to_process)
        processed = task.get(timeout=10)
    except Exception as e:
        logging.error(f"Failed to contact Business service: {e}")
        return {"error": "Business service not responding"}

    logging.info(f"Processed data: {processed}")

    try:
        requests.post("http://localhost:8002/save", json=processed, timeout=2)
    except Exception as e:
        logging.error(f"Failed to save data to DB: {e}")
        return {"error": "DB save operation failed"}

    logging.info("Data saved to DB. Returning result.")
    return {"result": processed}
