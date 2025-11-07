"""
Base domain exception classes for the Feeding System.

This module defines the hierarchy of domain exceptions that represent
business rule violations and domain-specific error conditions.
"""


class DomainException(Exception):
    """Base class for all domain exceptions.
    
    Domain exceptions represent violations of business rules or
    domain-specific error conditions that should be handled by
    the application layer.
    """
    pass


class InvalidLineNameException(DomainException):
    """Raised when a feeding line name is invalid.
    
    This includes violations such as:
    - Name too short (< 3 characters)
    - Name too long (> 100 characters)
    - Invalid characters (non-alphanumeric or spaces)
    """
    pass


class DuplicateLineNameException(DomainException):
    """Raised when attempting to create a feeding line with a name that already exists.
    
    Line names must be unique across the entire system.
    """
    pass


class InvalidComponentSequenceException(DomainException):
    """Raised when components are not arranged in the correct linear sequence.
    
    The required sequence is: Blower → [Sensors] → Doser(s) → Selector
    """
    pass


class InsufficientComponentsException(DomainException):
    """Raised when a feeding line doesn't have the minimum required components.
    
    Minimum requirements:
    - Exactly one Blower
    - At least one Doser
    - Exactly one Selector
    """
    pass


class InvalidComponentConfigurationException(DomainException):
    """Raised when a component's configuration is invalid.
    
    This includes violations such as:
    - Invalid parameter values (negative pressure, out-of-range rates, etc.)
    - Missing required configuration properties
    - Incompatible component settings
    """
    pass


class DuplicateSlotAssignmentException(DomainException):
    """Raised when attempting to assign a slot or cage that is already assigned.
    
    Business rules:
    - Each slot can only be assigned to one cage
    - Each cage can only be assigned to one slot within the same line
    """
    pass


class InvalidSlotAssignmentException(DomainException):
    """Raised when attempting to assign a cage to an invalid or unavailable slot.
    
    This includes:
    - Slot number doesn't exist on the selector
    - Slot is not available for assignment
    - Invalid slot number (non-positive)
    """
    pass


class SlotNotFoundException(DomainException):
    """Raised when a specified slot is not found in the feeding line.
    
    This occurs when attempting to access or modify a slot that does not exist.
    """
    pass


class CageNotFoundException(DomainException):
    """Raised when a specified cage is not found in the feeding line.
    
    This occurs when attempting to access or modify a cage that does not exist.
    """
    pass


class CageNotAvailableException(DomainException):
    """Raised when a cage is not available.
    
    Business rule:
    - A cage must be in 'available' status to be assigned to a feeding line.
    """
    pass


class AggregateInvariantViolationException(DomainException):
    """Raised when an operation would violate a FeedingLine aggregate invariant.
    
    Aggregate invariants are business rules that must always be maintained
    to ensure the aggregate remains in a valid state.
    """
    pass