from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.database.database import SessionLocal
from app.core.log_confing import Logger
import logging
import json


class AuditService:
    """
    System-wide audit logging service.
    Writes user actions and AI/agent/tool invocations to the audit_log table.
    """

    def __init__(self, db: Optional[Session] = None,
                 log_name="app", log_file="app.log", log_level=logging.INFO,
                 max_bytes=5 * 1024 * 1024, backup_count=7):
        self.db = db or SessionLocal()
        self.logger_class = Logger(log_name=log_name, log_file=log_file, log_level=log_level,
                                   max_bytes=max_bytes, backup_count=backup_count)
        self.logger = self.logger_class.logger

    def record_to_db(
        self,
        user_id: Optional[str],
        action: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """
        Record an audit event in the database.
        If DB insertion fails, raisse an Exception.

        Args:
            user_id: User performing the action
            action: The action name ("create_vm", "delete_bucket", "invoke_agent", etc.)
            resource: Resource or entity acted on (VM name, file, etc.)
            details: Additional context (dict)
            success: True if succeeded, False otherwise
            error_message: Optional error string
        Raises:
            Exception: if db error ocurrs.
        """
        try:
            audit_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                details=details,
                success=success,
                error_message=error_message,
                timestamp=datetime.now(timezone.utc),
            )
            self.db.add(audit_entry)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise Exception(f"[AuditService] DB write failed for {action}: {e}. Fallback log only.")

    def record_to_file(
        self,
        user_id: Optional[str],
        action: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        log_level=logging.INFO
    ):
        """
        Record an audit event in the logging file.

        Args:
            user_id: User performing the action
            action: The action name ("create_vm", "delete_bucket", "invoke_agent", etc.)
            resource: Resource or entity acted on (VM name, file, etc.)
            details: Additional context (dict)
            success: True if succeeded, False otherwise
            error_message: Optional error string
        """
        message = json.dumps({
            "type": "AUDIT",
            "user": user_id,
            "action": action,
            "success": success,
            "resource": resource,
            "details": details,
            "error": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        if log_level == logging.DEBUG:
            self.logger.debug(message)
        elif log_level == logging.INFO:
            self.logger.info(message)
        elif log_level == logging.WARNING:
            self.logger.warning(message)
        elif log_level == logging.ERROR:
            self.logger.error(message)
        elif log_level == logging.FATAL:
            self.logger.fatal(message)
        else:
            self.logger.info(message)

    def close(self):
        """
        Close the database session (for manual instantiation)
        """
        try:
            self.db.close()
        except Exception:
            pass

    def record_action(
        self,
        user_id: Optional[str],
        action: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        output_db: bool = True,
        output_file: bool = True
    ):
        """
        Record an audit event in the logging file.

        Args:
            user_id: User performing the action
            action: The action name ("create_vm", "delete_bucket", "invoke_agent", etc.)
            resource: Resource or entity acted on (VM name, file, etc.)
            details: Additional context (dict)
            success: True if succeeded, False otherwise
            error_message: Optional error string
            output_db: output to db or not
            output_file: output to file or not
        """
        if not self.db:
            self.db = SessionLocal()
        if output_db:
            try:
                self.record_to_db(user_id=user_id, action=action, resource=resource,
                                  details=details, success=success, error_message=error_message)
            except Exception as e:
                if output_file:
                    self.logger.warning(str(e))
            self.close()

        if output_file:
            self.record_to_file(user_id=user_id, action=action, resource=resource,
                                details=details, success=success, error_message=error_message)
