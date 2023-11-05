from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
import time

router = APIRouter(
    prefix="/audit_trails",
    tags=['AuditTrails']
)

@router.get('/add_log')
async def add_log(db:Session = Depends(get_db)):
    log_file_path = "app/files/log_file.log"
    with open(log_file_path, 'r') as log_file:
        log_data = log_file.read()
    log_entries = [line for line in log_data.split('\n') if line]
    if log_entries:
        logs = []
        for log in log_entries:
            log_info = log.split(" - ")
            if len(log_info) >= 5:
                timestamp = log_info[0]
                action = log_info[3]
                details = log_info[4]
                logs.append({'user_id':1,'timestamp': timestamp, 'action': action, 'details': details})
        for log in logs:
            new_log = models.AuditTrail(**log)
            retry_count = 0
            while retry_count < 3:
                try:
                    # Attempt to insert the log
                    db.add(new_log)
                    db.commit()
                    db.refresh(new_log)
                    break  # Success, exit the retry loop
                except Exception as e:
                    db.rollback()
                    print(f"Failed to insert log: {log}")
                    print(f"Error: {e}")
                    retry_count += 1
                    time.sleep(5)  # Wait before the next retry
        # Empty the log file
        with open(log_file_path, 'w') as log_file:
            log_file.truncate(0)
    return {"add_log_status":True}