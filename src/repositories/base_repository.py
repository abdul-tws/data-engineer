"""
Base Repository
Abstract base class for data repositories
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class BaseRepository(ABC):
    """
    Abstract base repository
    Defines interface for data access
    """
    
    @abstractmethod
    async def create(self, **kwargs) -> Any:
        """Create new entity"""
        pass
    
    @abstractmethod
    async def read(self, id: any) -> Optional[Any]:
        """Read entity by ID"""
        pass
    
    @abstractmethod
    async def read_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Read all entities"""
        pass
    
    @abstractmethod
    async def update(self, id: any, **kwargs) -> Optional[Any]:
        """Update entity"""
        pass
    
    @abstractmethod
    async def delete(self, id: any) -> bool:
        """Delete entity"""
        pass
