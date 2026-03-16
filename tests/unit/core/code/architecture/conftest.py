"""Shared fixtures and factory helpers for architecture tests."""
import pytest


def make_func(name, sloc, complexity, rank, class_name=None):
    """Factory: create a FunctionMetrics instance with predictable values."""
    from autocode.core.code.models import FunctionMetrics

    return FunctionMetrics(
        name=name,
        file="app.py",
        line=1,
        complexity=complexity,
        rank=rank,
        nesting_depth=0,
        sloc=sloc,
        is_method=class_name is not None,
        class_name=class_name,
    )


def make_file_metrics(path, functions=None, classes=None, **overrides):
    """Factory: create a FileMetrics from a list of FunctionMetrics objects."""
    from autocode.core.code.models import FileMetrics

    functions = functions or []
    classes = classes or []
    total_sloc = sum(f.sloc for f in functions)
    complexities = [f.complexity for f in functions]

    defaults = dict(
        path=path,
        language="python",
        sloc=total_sloc,
        comments=0,
        blanks=0,
        total_loc=total_sloc,
        functions=functions,
        classes=classes,
        classes_count=len({f.class_name for f in functions if f.class_name}),
        functions_count=len(functions),
        avg_complexity=sum(complexities) / len(complexities) if complexities else 0.0,
        max_complexity=max(complexities, default=0),
        max_nesting=0,
        maintainability_index=75.0,
    )
    defaults.update(overrides)
    return FileMetrics(**defaults)


def make_simple_file_metrics(path):
    """Factory: create a minimal FileMetrics (the _mock_fm pattern)."""
    from autocode.core.code.models import FileMetrics

    return FileMetrics(
        path=path,
        language="python",
        sloc=50,
        comments=5,
        blanks=5,
        total_loc=60,
        functions=[],
        classes_count=1,
        functions_count=2,
        avg_complexity=2.0,
        max_complexity=4,
        max_nesting=1,
        maintainability_index=75.0,
    )
