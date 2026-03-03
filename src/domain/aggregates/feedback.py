from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from domain.value_objects.identifiers import UserId


# Tipos válidos de feedback
VALID_FEEDBACK_TYPES = ("suggestion", "bug", "general")


class Feedback:
    """
    Agregado raíz: Feedback

    Representa un mensaje de retroalimentación enviado por un usuario del sistema.
    Es una entidad de solo escritura (write-only): se crea y se persiste, pero
    no se modifica ni se consulta desde la API.
    """

    def __init__(
        self,
        type: str,
        message: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        user_id: Optional[UserId] = None,
    ):
        """
        Crea una nueva instancia de Feedback.

        Args:
            type: Tipo de feedback ('suggestion', 'bug', 'general')
            message: Contenido del mensaje de feedback
            name: Nombre del usuario (opcional)
            email: Email del usuario (opcional)
            user_id: ID del usuario que envía el feedback

        Raises:
            ValueError: Si el tipo no es válido o el mensaje está vacío
        """
        self._validate_type(type)
        self._validate_message(message)

        self._id: UUID = uuid4()
        self._name: Optional[str] = name.strip() if name else None
        self._email: Optional[str] = email.strip() if email else None
        self._type: str = type
        self._message: str = message.strip()
        self._created_at: datetime = datetime.now(timezone.utc)

        # Multi-usuario
        self._user_id: Optional[UserId] = user_id

    @staticmethod
    def _validate_type(type: str) -> None:
        """Valida que el tipo de feedback sea uno de los valores permitidos."""
        if type not in VALID_FEEDBACK_TYPES:
            raise ValueError(
                f"Tipo de feedback inválido: '{type}'. Valores permitidos: {', '.join(VALID_FEEDBACK_TYPES)}"
            )

    @staticmethod
    def _validate_message(message: str) -> None:
        """Valida que el mensaje no esté vacío."""
        if not message or not message.strip():
            raise ValueError("El mensaje de feedback no puede estar vacío")

    # Properties (Read-only)

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def email(self) -> Optional[str]:
        return self._email

    @property
    def type(self) -> str:
        return self._type

    @property
    def message(self) -> str:
        return self._message

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def user_id(self) -> Optional[UserId]:
        return self._user_id

    def __repr__(self) -> str:
        return f"Feedback(id={self._id}, type={self._type}, name={self._name}, created_at={self._created_at})"
