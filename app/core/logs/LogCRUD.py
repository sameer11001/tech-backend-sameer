from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from app.core.logs.loggers import Logger
from app.core.repository.MongoRepository import MongoCRUD
from app.utils.enums.LogLevel import LogLevel


class LogCRUD(MongoCRUD[Logger]):
    
    def __init__(self):
        super().__init__(Logger)
    
    async def create_log_entry(
        self,
        level: LogLevel,
        message: str,
        service: str = "whatsapp-service",
        context: Dict[str, Any] = None,
        **kwargs
    ) -> Logger:
        log_data = Logger(
            level=level,
            message=message,
            service=service,
            context=context or {},
            **kwargs
        )
        return await self.create(log_data)
    
    async def get_logs_by_level(
        self,
        level: LogLevel,
        hours_back: int = 24,
        skip: int = 0,
        limit: int = 100
    ) -> List[Logger]:
        """Get logs by level within time range"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        query = {
            "level": level.value,
            "timestamp": {"$gte": since}
        }
        return await self.find_many(query, skip, limit, [("timestamp", -1)])
    
    async def get_logs_by_user(
        self,
        user_id: str,
        hours_back: int = 24,
        skip: int = 0,
        limit: int = 100
    ) -> List[Logger]:
        """Get logs for specific user"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        query = {
            "user_id": user_id,
            "timestamp": {"$gte": since}
        }
        return await self.find_many(query, skip, limit, [("timestamp", -1)])
    
    async def get_logs_by_request(self, request_id: str) -> List[Logger]:
        """Get all logs for a specific request"""
        query = {"request_id": request_id}
        return await self.find_many(query, sort=[("timestamp", 1)])
    
    async def get_error_logs(
        self,
        hours_back: int = 24,
        skip: int = 0,
        limit: int = 100
    ) -> List[Logger]:
        """Get error and fatal logs"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        query = {
            "level": {"$in": [LogLevel.ERROR.value, LogLevel.FATAL.value]},
            "timestamp": {"$gte": since}
        }
        return await self.find_many(query, skip, limit, [("timestamp", -1)])
    
    async def get_security_events(
        self,
        hours_back: int = 24,
        skip: int = 0,
        limit: int = 100
    ) -> List[Logger]:
        """Get security-related events"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        query = {
            "event_type": "security_event",
            "timestamp": {"$gte": since}
        }
        return await self.find_many(query, skip, limit, [("timestamp", -1)])
    
    async def search_logs(
        self,
        search_text: str,
        level: Optional[LogLevel] = None,
        service: Optional[str] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        hours_back: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Logger]:
        query = {}
        
        if hours_back:
            since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            query["timestamp"] = {"$gte": since}
        
        # Level filter
        if level:
            query["level"] = level.value
        
        if service:
            query["service"] = service
        
        if event_type:
            query["event_type"] = event_type
        
        if user_id:
            query["user_id"] = user_id
        
        if search_text:
            search_fields = ["message"]
            return await self.search(search_text, search_fields, query, skip, limit)
        
        return await self.find_many(query, skip, limit, [("timestamp", -1)])
    
    async def get_log_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get aggregated log statistics"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        # Count by level
        pipeline = [
            {"$match": {"timestamp": {"$gte": since}}},
            {"$group": {
                "_id": "$level",
                "count": {"$sum": 1}
            }}
        ]
        
        level_counts = await Logger.aggregate(pipeline).to_list()
        
        # Count by service
        service_pipeline = [
            {"$match": {"timestamp": {"$gte": since}}},
            {"$group": {
                "_id": "$service",
                "count": {"$sum": 1}
            }}
        ]
        
        service_counts = await Logger.aggregate(service_pipeline).to_list()
        
        # Error trends by hour
        error_trends_pipeline = [
            {"$match": {
                "timestamp": {"$gte": since},
                "level": {"$in": ["error", "fatal"]}
            }},
            {"$group": {
                "_id": {
                    "hour": {"$hour": "$timestamp"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.hour": 1}}
        ]
        
        error_trends = await Logger.aggregate(error_trends_pipeline).to_list()
        
        # Total counts
        total_logs = await self.count({"timestamp": {"$gte": since}})
        error_count = await self.count({
            "timestamp": {"$gte": since},
            "level": {"$in": ["error", "fatal"]}
        })
        
        return {
            "total_logs": total_logs,
            "error_count": error_count,
            "by_level": level_counts,
            "by_service": service_counts,
            "error_trends": error_trends,
            "time_range_hours": hours_back
        }
    
    async def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """Clean up old logs based on retention policy"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        # Archive old logs first (optional)
        await self.bulk_update(
            {"timestamp": {"$lt": cutoff_date}, "archived": False},
            {"archived": True}
        )
        
        # Delete very old archived logs
        very_old = datetime.now(timezone.utc) - timedelta(days=days_to_keep * 2)
        deleted_count = await self.bulk_delete({
            "timestamp": {"$lt": very_old},
            "archived": True
        })
        
        return deleted_count
    
    async def get_logs_by_correlation(
        self,
        correlation_id: str,
        trace_id: Optional[str] = None
    ) -> List[Logger]:
        """Get logs by correlation ID and optionally trace ID"""
        query = {"correlation_id": correlation_id}
        if trace_id:
            query["trace_id"] = trace_id
        
        return await self.find_many(query, sort=[("timestamp", 1)])
    
    async def get_critical_alerts(self, hours_back: int = 1) -> List[Dict[str, Any]]:
        """Get critical alerts that need immediate attention"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        alerts = []
        
        # High error rate
        error_count = await self.count({
            "level": {"$in": ["error", "fatal"]},
            "timestamp": {"$gte": since}
        })
        
        if error_count > 10:  # Configurable threshold
            alerts.append({
                "type": "high_error_rate",
                "severity": "critical",
                "message": f"{error_count} errors in the last {hours_back} hour(s)",
                "count": error_count,
                "threshold": 10
            })
        
        # Security events
        security_count = await self.count({
            "event_type": "security_event",
            "timestamp": {"$gte": since}
        })
        
        if security_count > 5:  # Configurable threshold
            alerts.append({
                "type": "security_events",
                "severity": "warning",
                "message": f"{security_count} security events in the last {hours_back} hour(s)",
                "count": security_count,
                "threshold": 5
            })
        
        # System failures
        fatal_count = await self.count({
            "level": "fatal",
            "timestamp": {"$gte": since}
        })
        
        if fatal_count > 0:
            alerts.append({
                "type": "system_failure",
                "severity": "critical",
                "message": f"{fatal_count} fatal errors detected",
                "count": fatal_count,
                "threshold": 0
            })
        
        return alerts