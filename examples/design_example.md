# Documento de Diseño: Calculadora de Fibonacci

## Descripción
Crear una función que calcule el n-ésimo número de Fibonacci de manera recursiva con memoización para mejorar el rendimiento.

## Requisitos
- Función llamada `fibonacci`
- Parámetro: `n` (entero positivo)
- Retorna: el n-ésimo número de Fibonacci
- Debe incluir caché para evitar recalcular valores
- Agregar docstring explicativo

## Ejemplo de uso
```python
>>> fibonacci(10)
55
>>> fibonacci(20)
6765
