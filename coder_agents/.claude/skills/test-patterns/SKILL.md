---
name: test-patterns
description: Patrones pytest para tests generados por test_engineer. Usar al escribir, revisar o depurar test_{module_name} en generated-apps/.
---

# Patrones de tests (test_engineer)

## Ubicación

Los tests van en `generated-apps/{base_name}/test_{module_name}` (ej. `test_accounts.py`). Mismo directorio que el módulo backend. Cada app tiene su subcarpeta dentro de `generated-apps/`.

## Estructura de test (pytest)

### Nombre de funciones

```python
def test_{funcionalidad}():
    """Test {qué hace}."""

def test_{clase}_{metodo}():
    """Test {Clase}.{metodo} hace {qué}."""

def test_{caso_edge}_raises_{excepcion}():
    """Test que {caso} lanza {ExcepcionType}."""
```

### Estructura Arrange-Act-Assert

```python
def test_ejemplo():
    # Arrange
    instance = Account()

    # Act
    result = instance.deposit(100)

    # Assert
    assert result is not None
    assert instance.balance == 100
```

### Tests parametrizados

```python
@pytest.mark.parametrize("input_val,expected", [
    (100, 100),
    (0, 0),
    (-1, None),  # caso edge
])
def test_deposit_cases(account, input_val, expected):
    result = account.deposit(input_val)
    assert result == expected
```

### Probar excepciones

```python
def test_withdraw_sin_fondos_raises():
    """Test que retirar sin fondos lanza ValueError."""
    account = Account()

    with pytest.raises(ValueError, match="insuficientes"):
        account.withdraw(1000)
```

## Ejecutar tests

```bash
cd generated-apps/{base_name}   # ej. generated-apps/accounts
pytest test_{module_name} -v
pytest -v                    # todos en esa app
pytest -x                    # parar en primer fallo
pytest --lf                  # solo los que fallaron antes
pytest --cov=. --cov-report=term-missing   # con coverage
```

## Buenas prácticas (inspiradas en pytest-testing-patterns)

- Docstrings que expliquen qué se prueba
- Tests independientes (sin estado compartido)
- Casos edge: inputs vacíos, valores inválidos, límites
- Assertions concretas y significativas
- Fixtures para setup repetido (`@pytest.fixture`)
