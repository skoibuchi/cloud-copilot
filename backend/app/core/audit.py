from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.database.database import SessionLocal
from app.core.log_config import Logger
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

    def _record_to_db(
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

    def _record_to_file(
        self,
        user_id: Optional[str],
        action: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        log_level: Optional[int] = logging.INFO
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
        elif log_level == logging.CRITICAL:
            self.logger.critical(message)
        else:
            self.logger.info(message)

    def _connect(self, db: Optional[Session] = None):
        """
        Connect to the database session (for manual instantiation)
        """
        try:
            self.db = db or SessionLocal()
        except Exception:
            pass

    def _close(self):
        """
        Close the database session (for manual instantiation)
        """
        try:
            self.db.close()
        except Exception:
            pass

    def _get_log_level(self, log_level: Optional[int] | Optional[str]) -> int:
        """
        Convert log level string to log level of logging module, and undefined log level numbers.
        Args:
            log_level: log level string or integer
        Returns:
            int: log level
        """
        if isinstance(log_level, str):
            log_level_upper = log_level.upper()
            if log_level_upper == "CRITICAL":
                return logging.CRITICAL
            elif log_level_upper == "ERROR":
                return logging.ERROR
            elif log_level_upper == "WARNING":
                return logging.WARNING
            elif log_level_upper == "INFO":
                return logging.INFO
            elif log_level_upper == "DEBUG":
                return logging.DEBUG
            else:
                return logging.DEBUG
        elif isinstance(log_level, int):
            if log_level not in (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG):
                return logging.DEBUG
        else:
            return logging.DEBUG

    def log(
        self,
        user_id: Optional[str],
        action: str,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        log_level: Optional[int] | Optional[str] = None,
        db: Optional[Session] = None,
        output_db: bool = True,
        output_file: bool = True,
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
        if output_db:
            if not self.db:
                self._connect(db=db)
            try:
                self._record_to_db(user_id=user_id, action=action, resource=resource,
                                   details=details, success=success, error_message=error_message)
            except Exception as e:
                if output_file:
                    self._record_to_file(user_id=user_id, action="AuditService.log", resource=resource,
                                         details=e, success=False, error_message="record to db error",
                                         log_level=logging.ERROR)
            self._close()

        if output_file:
            self._record_to_file(user_id=user_id, action=action, resource=resource,
                                 details=details, success=success, error_message=error_message,
                                 log_level=self._get_log_level(log_level))
