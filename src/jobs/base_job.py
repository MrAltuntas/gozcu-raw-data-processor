"""Base job class for all scheduled jobs."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.config.logging_config import setup_logging
from src.config.settings import settings
from src.core.database import db_manager


class BaseJob(ABC):
    """
    Abstract base class for all scheduled jobs.
    
    Provides common functionality:
    - Database connection management
    - Logging setup
    - Error handling
    - Execution time tracking
    """
    
    def __init__(self, job_name: str):
        """Initialize base job with name."""
        self.job_name = job_name
        self.logger = logging.getLogger(f"jobs.{job_name}")
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    async def setup(self) -> None:
        """Setup job infrastructure (database connections, etc.)."""
        self.logger.info(f"Setting up job: {self.job_name}")
        
        # Setup logging
        setup_logging()
        
        # Connect to database
        await db_manager.connect()
        self.logger.info("Database connected successfully")
    
    async def cleanup(self) -> None:
        """Cleanup job resources."""
        self.logger.info(f"Cleaning up job: {self.job_name}")
        
        # Disconnect database
        if db_manager.is_connected:
            await db_manager.disconnect()
            self.logger.info("Database disconnected")
    
    @abstractmethod
    async def execute(self) -> None:
        """Main job execution logic. Must be implemented by subclasses."""
        pass
    
    async def run(self) -> None:
        """
        Run the complete job lifecycle:
        1. Setup infrastructure
        2. Execute job logic
        3. Cleanup resources
        """
        self.start_time = datetime.now()
        
        try:
            await self.setup()
            await self.execute()
            
        except Exception as e:
            self.logger.error(f"Job {self.job_name} failed: {e}", exc_info=True)
            raise
        finally:
            await self.cleanup()
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            self.logger.info(f"Job {self.job_name} completed in {duration:.2f} seconds")


async def run_job(job_class, *args, **kwargs) -> None:
    """Utility function to run any job class."""
    # TODO: Implement job runner utility
    pass