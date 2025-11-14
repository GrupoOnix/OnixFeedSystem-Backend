from abc import ABC, abstractmethod
from typing import List, Optional

from domain.aggregates.cage import Cage
from domain.aggregates.silo import Silo

from .aggregates.feeding_line.feeding_line import FeedingLine
from .value_objects import CageId, CageName, LineId, LineName, SiloId, SiloName


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
    async def get_all(self) -> List[Cage]: ...

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
    