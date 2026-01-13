from datetime import datetime
from typing import Optional

from domain.value_objects import FoodId, FoodName


class Food:
    """
    Agregado raíz: Food (Alimento)

    Representa un tipo de alimento para peces con sus propiedades físicas y nutricionales.
    Los alimentos pueden ser asignados a silos y se utilizan en las operaciones de alimentación.
    """

    def __init__(
        self,
        name: FoodName,
        provider: str,
        code: str,
        ppk: float,
        size_mm: float,
        energy: float,
        kg_per_liter: float,
        active: bool = True,
    ):
        """
        Crea una nueva instancia de Food.

        Args:
            name: Nombre del alimento (Value Object)
            provider: Proveedor/fabricante del alimento
            code: Código del producto
            ppk: Pellets por kilo
            size_mm: Tamaño del pellet en milímetros
            energy: Energía en kcal/kg
            kg_per_liter: Densidad del alimento (kg por litro)
            active: Si el alimento está activo/disponible (default: True)
        """
        self._validate_numeric_fields(ppk, size_mm, energy, kg_per_liter)
        self._validate_string_fields(provider, code)

        self._id = FoodId.generate()
        self._name = name
        self._provider = provider.strip()
        self._code = code.strip()
        self._ppk = ppk
        self._size_mm = size_mm
        self._energy = energy
        self._kg_per_liter = kg_per_liter
        self._active = active
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()

    @staticmethod
    def _validate_numeric_fields(
        ppk: float, size_mm: float, energy: float, kg_per_liter: float
    ) -> None:
        """Valida que los campos numéricos sean positivos."""
        if ppk <= 0:
            raise ValueError("PPK (pellets por kilo) debe ser mayor a 0")
        if size_mm <= 0:
            raise ValueError("El tamaño del pellet debe ser mayor a 0 mm")
        if energy <= 0:
            raise ValueError("La energía debe ser mayor a 0 kcal/kg")
        if kg_per_liter <= 0:
            raise ValueError("La densidad (kg/L) debe ser mayor a 0")

    @staticmethod
    def _validate_string_fields(provider: str, code: str) -> None:
        """Valida que los campos de texto no estén vacíos."""
        if not provider or not provider.strip():
            raise ValueError("El proveedor no puede estar vacío")
        if not code or not code.strip():
            raise ValueError("El código del producto no puede estar vacío")

    # Properties (Read-only)

    @property
    def id(self) -> FoodId:
        return self._id

    @property
    def name(self) -> FoodName:
        return self._name

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def code(self) -> str:
        return self._code

    @property
    def ppk(self) -> float:
        """Pellets por kilo."""
        return self._ppk

    @property
    def size_mm(self) -> float:
        """Tamaño del pellet en milímetros."""
        return self._size_mm

    @property
    def energy(self) -> float:
        """Energía en kcal/kg."""
        return self._energy

    @property
    def kg_per_liter(self) -> float:
        """Densidad del alimento: kilogramos por litro."""
        return self._kg_per_liter

    @property
    def active(self) -> bool:
        """Indica si el alimento está activo y disponible para uso."""
        return self._active

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # Business methods

    def update_basic_info(
        self,
        name: Optional[FoodName] = None,
        provider: Optional[str] = None,
        code: Optional[str] = None,
    ) -> None:
        """
        Actualiza información básica del alimento.

        Args:
            name: Nuevo nombre del alimento
            provider: Nuevo proveedor
            code: Nuevo código de producto
        """
        if name is not None:
            self._name = name

        if provider is not None:
            if not provider.strip():
                raise ValueError("El proveedor no puede estar vacío")
            self._provider = provider.strip()

        if code is not None:
            if not code.strip():
                raise ValueError("El código no puede estar vacío")
            self._code = code.strip()

        self._updated_at = datetime.utcnow()

    def update_physical_properties(
        self,
        ppk: Optional[float] = None,
        size_mm: Optional[float] = None,
        kg_per_liter: Optional[float] = None,
    ) -> None:
        """
        Actualiza las propiedades físicas del alimento.

        Args:
            ppk: Nuevos pellets por kilo
            size_mm: Nuevo tamaño del pellet en mm
            kg_per_liter: Nueva densidad en kg/L
        """
        if ppk is not None:
            if ppk <= 0:
                raise ValueError("PPK debe ser mayor a 0")
            self._ppk = ppk

        if size_mm is not None:
            if size_mm <= 0:
                raise ValueError("El tamaño del pellet debe ser mayor a 0 mm")
            self._size_mm = size_mm

        if kg_per_liter is not None:
            if kg_per_liter <= 0:
                raise ValueError("La densidad debe ser mayor a 0 kg/L")
            self._kg_per_liter = kg_per_liter

        self._updated_at = datetime.utcnow()

    def update_energy(self, energy: float) -> None:
        """
        Actualiza el valor energético del alimento.

        Args:
            energy: Nueva energía en kcal/kg
        """
        if energy <= 0:
            raise ValueError("La energía debe ser mayor a 0 kcal/kg")

        self._energy = energy
        self._updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Marca el alimento como activo y disponible para uso."""
        if self._active:
            raise ValueError("El alimento ya está activo")
        self._active = True
        self._updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Marca el alimento como inactivo y no disponible para uso."""
        if not self._active:
            raise ValueError("El alimento ya está inactivo")
        self._active = False
        self._updated_at = datetime.utcnow()

    def get_display_name(self) -> str:
        """
        Retorna el nombre de visualización del alimento.

        Formato: "{name} ({code})"
        Ejemplo: "Elite 5mm (EL-5)"
        """
        return f"{self._name.value} ({self._code})"

    def __repr__(self) -> str:
        return (
            f"Food(id={self._id}, name={self._name}, code={self._code}, "
            f"provider={self._provider}, active={self._active})"
        )
