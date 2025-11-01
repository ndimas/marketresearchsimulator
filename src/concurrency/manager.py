"""Unified concurrency management with logging and monitoring."""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class ConcurrencyLevel(Enum):
    """Concurrency logging levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ConcurrencyMetrics:
    """Metrics for concurrency tracking."""
    current_active: int = 0
    peak_active: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    start_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)


class ConcurrencyManager:
    """Unified manager for MAX_CONCURRENT across all components."""
    
    def __init__(self, max_concurrent: int = 100):
        """Initialize concurrency manager."""
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.metrics = ConcurrencyMetrics()
        self.active_requests: Dict[int, Dict[str, Any]] = {}
        self.request_id_counter = 0
        self.logger = self._setup_logger()
        
        # Log initialization
        self.logger.info(f"🚀 ConcurrencyManager initialized with MAX_CONCURRENT={max_concurrent}")
        self._log_concurrency_level()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup dedicated concurrency logger."""
        logger = logging.getLogger("concurrency")
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _log_concurrency_level(self):
        """Log current concurrency level."""
        current = self.metrics.current_active
        peak = self.metrics.peak_active
        max_allowed = self.max_concurrent
        
        # Determine level
        if current >= max_allowed * 0.9:
            level = ConcurrencyLevel.CRITICAL
        elif current >= max_allowed * 0.7:
            level = ConcurrencyLevel.HIGH
        elif current >= max_allowed * 0.5:
            level = ConcurrencyLevel.MEDIUM
        else:
            level = ConcurrencyLevel.LOW
        
        self.logger.info(
            f"📊 Concurrency: {current}/{max_allowed} "
            f"(Peak: {peak}) - Level: {level.value}"
        )
    
    def _update_peak(self):
        """Update peak active requests."""
        if self.metrics.current_active > self.metrics.peak_active:
            self.metrics.peak_active = self.metrics.current_active
            self.logger.info(f"🔥 New peak concurrency: {self.metrics.peak_active}")
    
    async def acquire(self, request_type: str = "unknown", metadata: Optional[Dict] = None) -> int:
        """Acquire concurrency slot with logging."""
        request_id = self.request_id_counter
        self.request_id_counter += 1
        
        # Log acquisition attempt
        self.logger.debug(f"🔄 Request {request_id} ({request_type}) waiting for slot...")
        
        # Update metrics before acquisition
        self.metrics.last_activity = time.time()
        
        # Acquire semaphore
        await self.semaphore.acquire()
        
        # Update metrics after acquisition
        self.metrics.current_active += 1
        self.metrics.total_requests += 1
        self._update_peak()
        
        # Track active request
        self.active_requests[request_id] = {
            "type": request_type,
            "start_time": time.time(),
            "metadata": metadata or {}
        }
        
        # Log successful acquisition
        self.logger.info(
            f"✅ Request {request_id} ({request_type}) acquired slot "
            f"[Active: {self.metrics.current_active}/{self.max_concurrent}]"
        )
        
        self._log_concurrency_level()
        
        return request_id
    
    def release(self, request_id: int, success: bool = True, 
               response_time: float = 0.0, error: Optional[str] = None):
        """Release concurrency slot with logging and metrics update."""
        if request_id not in self.active_requests:
            self.logger.warning(f"⚠️ Request {request_id} not found in active requests")
            return
        
        request_info = self.active_requests.pop(request_id)
        request_type = request_info["type"]
        start_time = request_info["start_time"]
        duration = time.time() - start_time
        
        # Update metrics
        self.metrics.current_active -= 1
        self.metrics.last_activity = time.time()
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # Update average response time
        total_completed = self.metrics.successful_requests + self.metrics.failed_requests
        if total_completed > 0:
            total_time = self.metrics.avg_response_time * (total_completed - 1) + duration
            self.metrics.avg_response_time = total_time / total_completed
        
        # Release semaphore
        self.semaphore.release()
        
        # Log release
        if success:
            self.logger.info(
                f"✅ Request {request_id} ({request_type}) completed in {duration:.2f}s "
                f"[Active: {self.metrics.current_active}/{self.max_concurrent}]"
            )
        else:
            self.logger.error(
                f"❌ Request {request_id} ({request_type}) failed after {duration:.2f}s "
                f"[Active: {self.metrics.current_active}/{self.max_concurrent}] "
                f"Error: {error}"
            )
        
        self._log_concurrency_level()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current concurrency metrics."""
        uptime = time.time() - self.metrics.start_time
        success_rate = 0.0
        if self.metrics.total_requests > 0:
            success_rate = (self.metrics.successful_requests / self.metrics.total_requests) * 100
        
        return {
            "max_concurrent": self.max_concurrent,
            "current_active": self.metrics.current_active,
            "peak_active": self.metrics.peak_active,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": success_rate,
            "avg_response_time": self.metrics.avg_response_time,
            "uptime_seconds": uptime,
            "last_activity": self.metrics.last_activity,
            "active_requests": dict(self.active_requests)
        }
    
    def print_summary(self):
        """Print concurrency summary."""
        metrics = self.get_metrics()
        
        print(f"\n{'='*60}")
        print("📊 CONCURRENCY SUMMARY")
        print(f"{'='*60}")
        print(f"⚡ MAX_CONCURRENT: {metrics['max_concurrent']}")
        print(f"🔄 Current Active: {metrics['current_active']}")
        print(f"🔥 Peak Active: {metrics['peak_active']}")
        print(f"📈 Total Requests: {metrics['total_requests']}")
        print(f"✅ Successful: {metrics['successful_requests']}")
        print(f"❌ Failed: {metrics['failed_requests']}")
        print(f"📊 Success Rate: {metrics['success_rate']:.1f}%")
        print(f"⏱️ Avg Response Time: {metrics['avg_response_time']:.2f}s")
        print(f"⏰ Uptime: {metrics['uptime_seconds']:.1f}s")
        print(f"{'='*60}")
    
    async def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """Wait for all active requests to complete."""
        start_time = time.time()
        
        while self.metrics.current_active > 0:
            if time.time() - start_time > timeout:
                self.logger.warning(f"⏰ Timeout waiting for requests to complete")
                return False
            
            await asyncio.sleep(0.1)
        
        self.logger.info(f"✅ All requests completed")
        return True
    
    def get_utilization(self) -> float:
        """Get current utilization percentage."""
        return (self.metrics.current_active / self.max_concurrent) * 100 if self.max_concurrent > 0 else 0.0
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.wait_for_completion()


# Global instance for easy access
_global_manager: Optional[ConcurrencyManager] = None


def get_concurrency_manager(max_concurrent: int = 100) -> ConcurrencyManager:
    """Get or create global concurrency manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ConcurrencyManager(max_concurrent)
    return _global_manager


def set_max_concurrent(max_concurrent: int):
    """Update MAX_CONCURRENT for the global manager."""
    global _global_manager
    if _global_manager is not None:
        _global_manager.logger.info(f"🔄 Updating MAX_CONCURRENT: {_global_manager.max_concurrent} -> {max_concurrent}")
        _global_manager.max_concurrent = max_concurrent
        
        # Create new semaphore with updated limit
        current_active = _global_manager.metrics.current_active
        _global_manager.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Restore current active count
        for _ in range(current_active):
            _global_manager.semaphore.acquire()
        
        _global_manager.logger.info(f"✅ MAX_CONCURRENT updated to {max_concurrent}")
    else:
        _global_manager = ConcurrencyManager(max_concurrent)
