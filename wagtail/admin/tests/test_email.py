import pytest
from django.contrib.auth import get_user_model, authenticate
import re


# Função validate_login (para testar)
def validate_login(email, password):
    # Verifica se o formato do email é válido
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {"success": False, "error": "Invalid email format"}

    # Verifica se a senha tem pelo menos 8 caracteres
    if len(password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters"}

    # Tenta autenticar o usuário
    user = authenticate(email=email, password=password)

    if user is None:
        return {"success": False, "error": "Invalid email or password"}

    return {"success": True}


# Teste para formato de email inválido
@pytest.mark.django_db
def test_invalid_email_format():
    result = validate_login("invalidemail", "password123")
    assert result == {"success": False, "error": "Invalid email format"}


# Teste para senha curta
@pytest.mark.django_db
def test_short_password():
    result = validate_login("user@example.com", "short")
    assert result == {"success": False, "error": "Password must be at least 8 characters"}


# Teste para credenciais inválidas (usuário ou senha incorretos)
@patch("django.contrib.auth.authenticate")
@pytest.mark.django_db
def test_invalid_credentials(mock_authenticate):
    mock_authenticate.return_value = None  # Simula falha de autenticação
    result = validate_login("user@example.com", "wrongpassword")
    assert result == {"success": False, "error": "Invalid email or password"}


# Teste para credenciais válidas
@patch("django.contrib.auth.authenticate")
@pytest.mark.django_db
def test_valid_credentials(mock_authenticate):
    # Cria um usuário válido
    user = get_user_model().objects.create_user(email="user@example.com", password="correctpassword")

    # Simula sucesso de autenticação
    mock_authenticate.return_value = user

    result = validate_login("user@example.com", "correctpassword")
    assert result == {"success": True}
