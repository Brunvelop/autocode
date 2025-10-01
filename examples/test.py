def fibonacci(n, _cache={0: 0, 1: 1}):
    """
    Calcula el n-ésimo número de Fibonacci de manera recursiva con memoización.

    Parámetros:
    n (int): El índice del número de Fibonacci a calcular. Debe ser un entero positivo.

    Retorna:
    int: El n-ésimo número de Fibonacci.

    Ejemplo:
    >>> fibonacci(10)
    55
    >>> fibonacci(20)
    6765
    """
    if n < 0:
        raise ValueError("El índice debe ser un entero positivo")
    if n not in _cache:
        _cache[n] = fibonacci(n-1, _cache) + fibonacci(n-2, _cache)
    return _cache[n]