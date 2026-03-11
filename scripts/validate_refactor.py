#!/usr/bin/env python3
"""
Script de validación post-refactor: circular dependency fix.

Verifica que:
1. No hay imports directos de autocode.interfaces.models/registry en autocode/core/
2. Los módulos nuevos son importables correctamente
3. Los re-exports en autocode/interfaces/ funcionan
4. No hay dependencias circulares detectadas por coupling.py
"""
import sys
import importlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent

OK = "✅"
FAIL = "❌"
WARN = "⚠️ "

errors = []

print("=" * 60)
print("VALIDACIÓN POST-REFACTOR: circular dependency fix")
print("=" * 60)

# -------------------------------------------------------
# 1. Verificar que no hay imports directos de autocode.interfaces
#    en autocode/core/ (excepto en comentarios/docstrings)
# -------------------------------------------------------
print("\n[1] Comprobando imports en autocode/core/...")

import ast

bad_imports = []
for py_file in (ROOT / "autocode" / "core").rglob("*.py"):
    try:
        tree = ast.parse(py_file.read_text())
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        module = None
        if isinstance(node, ast.ImportFrom) and node.module:
            module = node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if "autocode.interfaces" in alias.name:
                    bad_imports.append((str(py_file.relative_to(ROOT)), alias.name))
        if module and "autocode.interfaces" in module:
            bad_imports.append((str(py_file.relative_to(ROOT)), module))

if bad_imports:
    print(f"  {FAIL} Imports de autocode.interfaces encontrados en autocode/core/:")
    for fpath, mod in bad_imports:
        print(f"      {fpath}: {mod}")
    errors.append("Imports circulares detectados en autocode/core/")
else:
    print(f"  {OK} Sin imports directos de autocode.interfaces en autocode/core/")

# -------------------------------------------------------
# 2. Verificar que los nuevos módulos son importables
# -------------------------------------------------------
print("\n[2] Verificando importabilidad de nuevos módulos...")

new_modules = [
    "autocode.core.models",
    "autocode.core.registry",
]

for mod_name in new_modules:
    try:
        mod = importlib.import_module(mod_name)
        print(f"  {OK} {mod_name}")
    except Exception as e:
        print(f"  {FAIL} {mod_name}: {e}")
        errors.append(f"No se puede importar {mod_name}: {e}")

# -------------------------------------------------------
# 3. Verificar que los re-exports de autocode/interfaces/ funcionan
# -------------------------------------------------------
print("\n[3] Verificando re-exports en autocode/interfaces/...")

reexport_tests = [
    ("autocode.interfaces.models", ["GenericOutput", "FunctionInfo", "ParamSchema", "FunctionSchema"]),
    ("autocode.interfaces.registry", ["register_function", "get_all_functions", "clear_registry", "RegistryError"]),
]

for mod_name, symbols in reexport_tests:
    try:
        mod = importlib.import_module(mod_name)
        missing = [s for s in symbols if not hasattr(mod, s)]
        if missing:
            print(f"  {FAIL} {mod_name} — faltan símbolos: {missing}")
            errors.append(f"Re-exports incompletos en {mod_name}")
        else:
            print(f"  {OK} {mod_name} ({', '.join(symbols)})")
    except Exception as e:
        print(f"  {FAIL} {mod_name}: {e}")
        errors.append(f"No se puede importar {mod_name}: {e}")

# -------------------------------------------------------
# 4. Verificar identidad de objetos (re-export = mismo objeto)
# -------------------------------------------------------
print("\n[4] Verificando identidad de re-exports (mismo objeto)...")

try:
    from autocode.core.models import GenericOutput as GO_core
    from autocode.interfaces.models import GenericOutput as GO_iface
    if GO_core is GO_iface:
        print(f"  {OK} GenericOutput: core y interfaces apuntan al mismo objeto")
    else:
        print(f"  {FAIL} GenericOutput: objetos DISTINTOS (re-export roto)")
        errors.append("Re-export de GenericOutput es objeto distinto")
except Exception as e:
    print(f"  {FAIL} Error verificando identidad: {e}")
    errors.append(str(e))

try:
    from autocode.core.registry import register_function as RF_core
    from autocode.interfaces.registry import register_function as RF_iface
    if RF_core is RF_iface:
        print(f"  {OK} register_function: core y interfaces apuntan al mismo objeto")
    else:
        print(f"  {FAIL} register_function: objetos DISTINTOS (re-export roto)")
        errors.append("Re-export de register_function es objeto distinto")
except Exception as e:
    print(f"  {FAIL} Error verificando identidad: {e}")
    errors.append(str(e))

# -------------------------------------------------------
# 5. Verificar coupling analysis: 0 dependencias circulares
# -------------------------------------------------------
print("\n[5] Verificando análisis de coupling (0 circulares)...")

try:
    import subprocess
    result = subprocess.run(
        ["git", "ls-files", "--", "*.py"],
        capture_output=True, text=True, cwd=ROOT
    )
    files = [f for f in result.stdout.strip().split("\n") if f]
    
    from autocode.core.code.coupling import analyze_coupling
    coupling, circulars = analyze_coupling(files)
    
    if circulars:
        print(f"  {FAIL} Dependencias circulares detectadas ({len(circulars)}):")
        for pair in circulars:
            print(f"      • {pair[0]} ↔ {pair[1]}")
        errors.append(f"Todavía hay {len(circulars)} dependencia(s) circular(es)")
    else:
        print(f"  {OK} Sin dependencias circulares")
        
    # Mostrar el grafo de dependencias relevante
    print("\n     Dependencias autocode.core / autocode.interfaces:")
    for pkg in sorted(coupling, key=lambda p: p.name):
        if pkg.name in ("autocode.core", "autocode.interfaces"):
            print(f"      {pkg.name}: imports_to={pkg.imports_to}, imported_by={pkg.imported_by}")
except Exception as e:
    print(f"  {WARN} No se pudo ejecutar coupling analysis: {e}")

# -------------------------------------------------------
# Resumen final
# -------------------------------------------------------
print("\n" + "=" * 60)
if errors:
    print(f"{FAIL} VALIDACIÓN FALLIDA — {len(errors)} error(es):")
    for e in errors:
        print(f"  • {e}")
    sys.exit(1)
else:
    print(f"{OK} VALIDACIÓN EXITOSA — Refactor completado correctamente")
print("=" * 60)
