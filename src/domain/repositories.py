from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from domain.aggregates.cage import Cage
from domain.aggregates.silo import Silo

from .aggregates.feeding_line.feeding_line import FeedingLine
from .value_objects import CageId, CageName, LineId, LineName, SiloId, SiloName

# Para type hints de los logs
from uuid import UUID
from datetime import date


class IFeedingLineRepository(ABC):

    @abstractmethod
    async def save(self, feeding_line: FeedingLine) -> None: ...

    @abstractmethod
    async def find_by_id(self, line_id: LineId) -> Optional[FeedingLine]: ...

    @abstractmethod
    async def find_by_name(self, name: LineName) -> Optional[FeedingLine]: ...

    @abstractmethod
    async def get_all(self) -> list[FeedingLine]: ...

    @abstractmethod
    async def delete(self, line_id: LineId) -> None: ...


class ICageRepository(ABC):

    @abstractmethod
    async def save(self, cage: Cage) -> None: ...

    @abstractmethod
    async def find_by_id(self, cage_id: CageId) -> Optional[Cage]: ...
    
    @abstractmethod
    async def find_by_name(self, name: CageName) -> Optional[Cage]: ...
    
    @abstractmethod
    async def list(self) -> List[Cage]: ...

    @abstractmethod
    async def list_with_line_info(self, line_id: Optional['LineId'] = None) -> List[Tuple[Cage, Optional[str]]]: ...

    @abstractmethod
    async def delete(self, cage_id: CageId) -> None: ...


class ISiloRepository(ABC):

    @abstractmethod
    async def save(self, silo: Silo) -> None: ...

    @abstractmethod
    async def find_by_id(self, silo_id: SiloId) -> Optional[Silo]: ...
    
    @abstractmethod
    async def find_by_name(self, name: SiloName) -> Optional[Silo]: ...

    @abstractmethod
    async def get_all(self) -> List[Silo]: ...

    @abstractmethod
    async def delete(self, silo_id: SiloId) -> None: ...


class IBiometryLogRepository(ABC):
    """Repositorio para logs de biometría de jaulas."""

    @abstractmethod
    async def save(self, log_entry: 'BiometryLogEntry') -> None:
        """Guarda un registro de biometría."""
        ...

    @abstractmethod
    async def list_by_cage(self, cage_id: CageId, limit: int = 50, offset: int = 0) -> List['BiometryLogEntry']:
        """Lista registros de biometría de una jaula, ordenados por fecha DESC."""
        ...

    @abstractmethod
    async def count_by_cage(self, cage_id: CageId) -> int:
        """Cuenta total de registros de biometría de una jaula."""
        ...


class IMortalityLogRepository(ABC):
    """Repositorio para logs de mortalidad de jaulas."""

    @abstractmethod
    async def save(self, log_entry: 'MortalityLogEntry') -> None:
        """Guarda un registro de mortalidad."""
        ...

    @abstractmethod
    async def list_by_cage(self, cage_id: CageId, limit: int = 50, offset: int = 0) -> List['MortalityLogEntry']:
        """Lista registros de mortalidad de una jaula, ordenados por fecha DESC."""
        ...

    @abstractmethod
    async def count_by_cage(self, cage_id: CageId) -> int:
        """Cuenta total de registros de mortalidad de una jaula."""
        ...

    @abstractmethod
    async def get_total_mortality(self, cage_id: CageId) -> int:
        """Calcula la mortalidad acumulada total de una jaula."""
        ...


class IConfigChangeLogRepository(ABC):
    """Repositorio para logs de cambios de configuración de jaulas."""

    @abstractmethod
    async def save_batch(self, log_entries: List['ConfigChangeLogEntry']) -> None:
        """Guarda múltiples registros de cambios en una sola transacción."""
        ...

    @abstractmethod
    async def list_by_cage(self, cage_id: CageId, limit: int = 50, offset: int = 0) -> List['ConfigChangeLogEntry']:
        """Lista registros de cambios de configuración de una jaula, ordenados por fecha DESC."""
        ...

    @abstractmethod
    async def count_by_cage(self, cage_id: CageId) -> int:
        """Cuenta total de registros de cambios de configuración de una jaula."""
        ...
    