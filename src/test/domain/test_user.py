"""Tests para el aggregate User."""

import pytest

from domain.aggregates.user import User, UserRole
from domain.value_objects.identifiers import UserId


def test_user_creation_default_values():
    """Un usuario se crea con rol user y estado activo por defecto."""
    user = User.create(
        username="operator1",
        full_name="Operador Uno",
        hashed_password="hashed_secret",
    )

    assert isinstance(user.id, UserId)
    assert user.username == "operator1"
    assert user.full_name == "Operador Uno"
    assert user.hashed_password == "hashed_secret"
    assert user.role == UserRole.USER
    assert user.is_active is True
    assert user.is_superadmin is False
    assert user.must_change_password is False


def test_user_creation_admin():
    """Se puede crear un usuario con rol admin."""
    user = User.create(
        username="admin1",
        full_name="Administrador Uno",
        hashed_password="hashed_secret",
        role=UserRole.ADMIN,
    )

    assert user.role == UserRole.ADMIN
    assert user.is_admin() is True


def test_user_superadmin_promotion():
    """Un usuario puede ser promovido a superadmin."""
    user = User.create(
        username="onix",
        full_name="Admin Onix",
        hashed_password="hashed_secret",
        role=UserRole.ADMIN,
    )

    user.promote_to_superadmin()

    assert user.is_superadmin is True
    assert user.is_admin() is True


def test_user_deactivation_and_activation():
    """Se puede desactivar y reactivar un usuario."""
    user = User.create(
        username="operator1",
        full_name="Operador Uno",
        hashed_password="hashed_secret",
    )

    user.deactivate()
    assert user.is_active is False

    user.activate()
    assert user.is_active is True


def test_user_change_password():
    """Se puede cambiar la contraseña del usuario."""
    user = User.create(
        username="operator1",
        full_name="Operador Uno",
        hashed_password="old_hash",
    )

    user.change_password("new_hash")

    assert user.hashed_password == "new_hash"
    assert user.must_change_password is False


def test_user_change_password_resets_must_change_flag():
    """Cambiar la contraseña limpia el flag must_change_password."""
    user = User.create(
        username="operator1",
        full_name="Operador Uno",
        hashed_password="old_hash",
        must_change_password=True,
    )

    user.change_password("new_hash", reset_must_change=True)

    assert user.hashed_password == "new_hash"
    assert user.must_change_password is False


def test_user_force_password_change():
    """Un superadmin puede forzar el cambio de contraseña de un usuario."""
    user = User.create(
        username="operator1",
        full_name="Operador Uno",
        hashed_password="old_hash",
    )

    user.force_password_change("new_hash")

    assert user.hashed_password == "new_hash"
    assert user.must_change_password is True


def test_user_update_role():
    """Se puede actualizar el rol de un usuario."""
    user = User.create(
        username="operator1",
        full_name="Operador Uno",
        hashed_password="hashed_secret",
    )

    user.update_role(UserRole.ADMIN)

    assert user.role == UserRole.ADMIN


def test_user_creation_empty_username_raises():
    """No se puede crear un usuario con username vacío."""
    with pytest.raises(ValueError, match="username no puede estar vacío"):
        User.create(
            username="   ",
            full_name="Operador Uno",
            hashed_password="hashed_secret",
        )


def test_user_creation_empty_full_name_raises():
    """No se puede crear un usuario con nombre completo vacío."""
    with pytest.raises(ValueError, match="nombre completo no puede estar vacío"):
        User.create(
            username="operator1",
            full_name="",
            hashed_password="hashed_secret",
        )


def test_user_creation_empty_password_raises():
    """No se puede crear un usuario con hash de contraseña vacío."""
    with pytest.raises(ValueError, match="hash de contraseña no puede estar vacío"):
        User.create(
            username="operator1",
            full_name="Operador Uno",
            hashed_password="  ",
        )
