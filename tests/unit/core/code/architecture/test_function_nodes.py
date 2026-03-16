"""Tests for function/class/method architecture nodes."""
from unittest.mock import patch

from .conftest import make_func, make_file_metrics


# ==============================================================================
# J) FUNCTION/CLASS/METHOD ARCHITECTURE NODES
# ==============================================================================


class TestFunctionClassArchitectureNodes:
    """J) Tests for function/class/method nodes in the architecture tree."""

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_build_nodes_standalone_function(self, mock_read, mock_analyze):
        """Standalone functions produce type='function' nodes with correct id/parent."""
        from autocode.core.code.architecture import _build_architecture_nodes

        mock_read.return_value = "def validate_input(x): return x\n"
        func = make_func("validate_input", sloc=5, complexity=2, rank="A")
        mock_analyze.return_value = make_file_metrics("app.py", [func])

        nodes = _build_architecture_nodes(["app.py"])
        node_map = {n.id: n for n in nodes}

        assert "app.py::validate_input" in node_map
        assert node_map["app.py::validate_input"].type == "function"
        assert node_map["app.py::validate_input"].parent_id == "app.py"

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_build_nodes_class_and_method(self, mock_read, mock_analyze):
        """Class methods produce class node (id=fpath::Class) + method node (parent=class)."""
        from autocode.core.code.architecture import _build_architecture_nodes

        mock_read.return_value = "class UserService:\n    def auth(self): pass\n"
        method = make_func(
            "UserService.auth", sloc=3, complexity=1, rank="A", class_name="UserService"
        )
        mock_analyze.return_value = make_file_metrics("app.py", [method])

        nodes = _build_architecture_nodes(["app.py"])
        node_map = {n.id: n for n in nodes}
        method_nodes = [n for n in nodes if n.type == "method"]

        assert "app.py::UserService" in node_map
        assert node_map["app.py::UserService"].type == "class"
        assert len(method_nodes) == 1
        assert method_nodes[0].parent_id == "app.py::UserService"

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_build_nodes_function_carries_metrics(self, mock_read, mock_analyze):
        """Function nodes carry complexity, rank, and sloc from FunctionMetrics."""
        from autocode.core.code.architecture import _build_architecture_nodes

        mock_read.return_value = "def complex_func(): pass\n"
        func = make_func("complex_func", sloc=20, complexity=8, rank="B")
        mock_analyze.return_value = make_file_metrics("app.py", [func])

        nodes = _build_architecture_nodes(["app.py"])
        node_map = {n.id: n for n in nodes}
        fn = node_map["app.py::complex_func"]

        assert fn.complexity == 8
        assert fn.rank == "B"
        assert fn.sloc == 20

    def test_propagate_treats_class_as_container(self):
        """Class nodes should be treated as containers and have children_count set."""
        from autocode.core.code.models import ArchitectureNode
        from autocode.core.code.architecture import _propagate_metrics

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        file_node = ArchitectureNode(
            id="app.py", parent_id=".", name="app.py", type="file", path="app.py",
            sloc=30,
        )
        class_node = ArchitectureNode(
            id="app.py::MyClass", parent_id="app.py", name="MyClass",
            type="class", path="app.py",
        )
        method_a = ArchitectureNode(
            id="app.py::MyClass::__init__", parent_id="app.py::MyClass",
            name="__init__", type="method", path="app.py",
            sloc=10, loc=10, mi=100.0, avg_complexity=1.0, max_complexity=1,
        )
        method_b = ArchitectureNode(
            id="app.py::MyClass::authenticate", parent_id="app.py::MyClass",
            name="authenticate", type="method", path="app.py",
            sloc=20, loc=20, mi=80.0, avg_complexity=5.0, max_complexity=8,
        )
        nodes = [root, file_node, class_node, method_a, method_b]
        _propagate_metrics(nodes, ".")

        node_map = {n.id: n for n in nodes}
        assert node_map["app.py::MyClass"].children_count == 2

    def test_class_node_aggregates_method_sloc_and_complexity(self):
        """Class node should aggregate SLOC and CC from its method children."""
        from autocode.core.code.models import ArchitectureNode
        from autocode.core.code.architecture import _propagate_metrics

        root = ArchitectureNode(
            id=".", parent_id=None, name="root", type="directory", path="."
        )
        file_node = ArchitectureNode(
            id="app.py", parent_id=".", name="app.py", type="file", path="app.py",
            sloc=30,
        )
        class_node = ArchitectureNode(
            id="app.py::MyClass", parent_id="app.py", name="MyClass",
            type="class", path="app.py",
        )
        method_a = ArchitectureNode(
            id="app.py::MyClass::__init__", parent_id="app.py::MyClass",
            name="__init__", type="method", path="app.py",
            sloc=10, loc=10, mi=100.0, avg_complexity=1.0, max_complexity=1,
        )
        method_b = ArchitectureNode(
            id="app.py::MyClass::authenticate", parent_id="app.py::MyClass",
            name="authenticate", type="method", path="app.py",
            sloc=20, loc=20, mi=80.0, avg_complexity=5.0, max_complexity=8,
        )
        nodes = [root, file_node, class_node, method_a, method_b]
        _propagate_metrics(nodes, ".")

        node_map = {n.id: n for n in nodes}
        class_n = node_map["app.py::MyClass"]

        assert class_n.sloc == 30           # 10 + 20
        assert class_n.max_complexity == 8  # max(1, 8)
        # LOC-weighted avg_complexity: (1*10 + 5*20) / 30 = 110/30 ≈ 3.67
        assert abs(class_n.avg_complexity - 3.67) < 0.1


# ==============================================================================
# K) ORPHAN CLASS NODES (classes with no methods)
# ==============================================================================


class TestOrphanClassNodes:
    """K) Tests for class nodes created for Python classes without methods."""

    def _make_class_info(self, name, line_start=1, line_end=5, sloc=4):
        from autocode.core.code.models import ClassInfo
        return ClassInfo(name=name, line_start=line_start, line_end=line_end, sloc=sloc)

    def _make_fm_with_orphan_classes(self, path, class_infos, functions=None):
        """Build a FileMetrics with classes but (optionally) no methods."""
        from autocode.core.code.models import FileMetrics
        functions = functions or []
        return FileMetrics(
            path=path,
            language="python",
            sloc=20,
            comments=2,
            blanks=3,
            total_loc=25,
            functions=functions,
            classes=class_infos,
            classes_count=len(class_infos),
            functions_count=len(functions),
            avg_complexity=0.0,
            max_complexity=0,
            max_nesting=0,
            maintainability_index=80.0,
        )

    def test_orphan_class_node_properties(self):
        """A class with no methods produces a class node with correct type/parent/sloc."""
        from autocode.core.code.architecture import _create_function_class_nodes

        cls_info = self._make_class_info("Config", line_start=1, line_end=4, sloc=7)
        fm = self._make_fm_with_orphan_classes("app.py", [cls_info])

        nodes = _create_function_class_nodes("app.py", fm)
        node_map = {n.id: n for n in nodes}

        assert "app.py::Config" in node_map
        assert node_map["app.py::Config"].type == "class"
        assert node_map["app.py::Config"].parent_id == "app.py"
        assert node_map["app.py::Config"].sloc == 7
        assert node_map["app.py::Config"].functions_count == 0

    def test_class_with_methods_not_duplicated_as_orphan(self):
        """A class that already has method nodes should NOT also be an orphan node."""
        from autocode.core.code.architecture import _create_function_class_nodes
        from autocode.core.code.models import FunctionMetrics, ClassInfo, FileMetrics

        method = FunctionMetrics(
            name="do_thing", file="app.py", line=3,
            complexity=1, rank="A", nesting_depth=0, sloc=5,
            is_method=True, class_name="MyService",
        )
        cls_info = ClassInfo(name="MyService", line_start=1, line_end=6, sloc=6)
        fm = FileMetrics(
            path="app.py", language="python",
            sloc=6, comments=0, blanks=0, total_loc=6,
            functions=[method],
            classes=[cls_info],
            classes_count=1,
            functions_count=1,
            avg_complexity=1.0, max_complexity=1, max_nesting=0,
            maintainability_index=80.0,
        )

        nodes = _create_function_class_nodes("app.py", fm)
        class_nodes = [n for n in nodes if n.id == "app.py::MyService"]

        assert len(class_nodes) == 1
        assert class_nodes[0].functions_count == 1

    def test_multiple_orphan_classes_all_get_nodes(self):
        """Multiple orphan classes should each produce their own class node."""
        from autocode.core.code.architecture import _create_function_class_nodes

        class_infos = [
            self._make_class_info("Config", sloc=3),
            self._make_class_info("Constants", sloc=5),
            self._make_class_info("Enums", sloc=2),
        ]
        fm = self._make_fm_with_orphan_classes("settings.py", class_infos)

        nodes = _create_function_class_nodes("settings.py", fm)
        ids = {n.id for n in nodes}

        assert "settings.py::Config" in ids
        assert "settings.py::Constants" in ids
        assert "settings.py::Enums" in ids

    def test_full_pipeline_orphan_class_produces_node(self):
        """End-to-end: analyze_file_metrics + _create_function_class_nodes."""
        from autocode.core.code.analyzer import analyze_file_metrics
        from autocode.core.code.architecture import _create_function_class_nodes

        code = (
            "class Config:\n"
            "    DEBUG = True\n"
            "    HOST = 'localhost'\n"
        )
        fm = analyze_file_metrics("cfg.py", code)
        nodes = _create_function_class_nodes("cfg.py", fm)

        node_map = {n.id: n for n in nodes}
        assert "cfg.py::Config" in node_map
        assert node_map["cfg.py::Config"].type == "class"
        assert node_map["cfg.py::Config"].functions_count == 0

    def test_full_pipeline_mixed_orphan_and_class_with_methods(self):
        """End-to-end: file with both orphan class and class-with-methods."""
        from autocode.core.code.analyzer import analyze_file_metrics
        from autocode.core.code.architecture import _create_function_class_nodes

        code = (
            "class Config:\n"
            "    DEBUG = True\n"
            "\n"
            "class Service:\n"
            "    def run(self):\n"
            "        return True\n"
        )
        fm = analyze_file_metrics("mixed.py", code)
        nodes = _create_function_class_nodes("mixed.py", fm)
        node_map = {n.id: n for n in nodes}

        assert "mixed.py::Config" in node_map
        assert node_map["mixed.py::Config"].functions_count == 0

        assert "mixed.py::Service" in node_map
        assert node_map["mixed.py::Service"].functions_count >= 1

    @patch("autocode.core.code.architecture.analyze_file_metrics")
    @patch("pathlib.Path.read_text")
    def test_build_nodes_creates_orphan_class_nodes(self, mock_read, mock_analyze):
        """_build_architecture_nodes should include orphan class nodes."""
        from autocode.core.code.architecture import _build_architecture_nodes
        from autocode.core.code.models import FileMetrics, ClassInfo

        mock_read.return_value = "class Config:\n    DEBUG = True\n"
        mock_analyze.return_value = FileMetrics(
            path="app.py", language="python",
            sloc=2, comments=0, blanks=0, total_loc=2,
            functions=[],
            classes=[ClassInfo(name="Config", line_start=1, line_end=2, sloc=2)],
            classes_count=1, functions_count=0,
            avg_complexity=0.0, max_complexity=0, max_nesting=0,
            maintainability_index=90.0,
        )

        nodes = _build_architecture_nodes(["app.py"])
        node_map = {n.id: n for n in nodes}

        assert "app.py::Config" in node_map
        assert node_map["app.py::Config"].type == "class"
        assert node_map["app.py::Config"].parent_id == "app.py"
        assert node_map["app.py::Config"].functions_count == 0


# ==============================================================================
# L) METHOD ID COLLISION BUG REGRESSION TESTS
# ==============================================================================


class TestMethodIdCollisionBug:
    """Regression tests for method ID collision when two classes share the same method name.

    Bug: method_id was built as f"{fpath}::{method.name}", so two classes with
    __init__ both got ID "fpath::__init__" — the second overwrote the first.
    Fix: changed to f"{fpath}::{class_name}::{method.name}".
    """

    def test_method_id_includes_class_name_to_avoid_collision(self):
        """Two classes with __init__ must produce two distinct method node IDs."""
        from autocode.core.code.architecture import _create_function_class_nodes
        from autocode.core.code.models import FunctionMetrics, FileMetrics

        fpath = "models.py"

        method_a = FunctionMetrics(
            name="__init__",
            file=fpath,
            line=3,
            complexity=1,
            rank="A",
            nesting_depth=0,
            sloc=4,
            is_method=True,
            class_name="UserCreate",
        )
        method_b = FunctionMetrics(
            name="__init__",
            file=fpath,
            line=12,
            complexity=1,
            rank="A",
            nesting_depth=0,
            sloc=4,
            is_method=True,
            class_name="UserUpdate",
        )

        fm = FileMetrics(
            path=fpath,
            language="python",
            sloc=20,
            comments=0,
            blanks=0,
            total_loc=20,
            functions=[method_a, method_b],
            classes=[],
            classes_count=2,
            functions_count=2,
            avg_complexity=1.0,
            max_complexity=1,
            max_nesting=0,
            maintainability_index=80.0,
        )

        nodes = _create_function_class_nodes(fpath, fm)
        method_ids = [n.id for n in nodes if n.type == "method"]

        assert len(method_ids) == 2, (
            f"Expected 2 method nodes but got {len(method_ids)}: {method_ids}\n"
            "Bug: both __init__ methods get the same id='models.py::__init__'"
        )
        assert len(set(method_ids)) == 2, (
            f"Method IDs are not unique: {method_ids}\n"
            "Bug: id collision because class name is missing from method ID"
        )
        id_set = set(method_ids)
        assert any("UserCreate" in mid for mid in id_set), (
            f"No method ID contains 'UserCreate': {method_ids}"
        )
        assert any("UserUpdate" in mid for mid in id_set), (
            f"No method ID contains 'UserUpdate': {method_ids}"
        )

    def test_models_file_pydantic_classes_produce_nodes(self):
        """Pydantic BaseModel subclasses with only fields produce orphan class nodes."""
        from autocode.core.code.analyzer import analyze_file_metrics
        from autocode.core.code.architecture import _create_function_class_nodes

        pydantic_models_code = (
            "from pydantic import BaseModel\n"
            "from typing import Optional\n"
            "\n"
            "class UserCreate(BaseModel):\n"
            "    name: str\n"
            "    email: str\n"
            "    age: int\n"
            "\n"
            "class UserUpdate(BaseModel):\n"
            "    name: Optional[str] = None\n"
            "    email: Optional[str] = None\n"
            "\n"
            "class UserResponse(BaseModel):\n"
            "    id: int\n"
            "    name: str\n"
            "    email: str\n"
        )

        fm = analyze_file_metrics("models.py", pydantic_models_code)
        nodes = _create_function_class_nodes("models.py", fm)
        node_ids = {n.id for n in nodes}

        assert "models.py::UserCreate" in node_ids, (
            f"Missing node for UserCreate. Got: {node_ids}"
        )
        assert "models.py::UserUpdate" in node_ids, (
            f"Missing node for UserUpdate. Got: {node_ids}"
        )
        assert "models.py::UserResponse" in node_ids, (
            f"Missing node for UserResponse. Got: {node_ids}"
        )

        class_nodes = [n for n in nodes if n.type == "class"]
        assert len(class_nodes) == 3, (
            f"Expected 3 class nodes, got {len(class_nodes)}: "
            f"{[n.id for n in class_nodes]}"
        )

    def test_models_file_with_validators_produce_method_nodes(self):
        """Two Pydantic models with same-named validator must produce distinct method nodes."""
        from autocode.core.code.analyzer import analyze_file_metrics
        from autocode.core.code.architecture import _create_function_class_nodes

        pydantic_with_validators = (
            "from pydantic import BaseModel, validator\n"
            "\n"
            "class UserCreate(BaseModel):\n"
            "    name: str\n"
            "\n"
            "    @validator('name')\n"
            "    def validate_name(cls, v):\n"
            "        if not v.strip():\n"
            "            raise ValueError('name cannot be empty')\n"
            "        return v.strip()\n"
            "\n"
            "class ProductCreate(BaseModel):\n"
            "    name: str\n"
            "\n"
            "    @validator('name')\n"
            "    def validate_name(cls, v):\n"
            "        if len(v) > 100:\n"
            "            raise ValueError('name too long')\n"
            "        return v\n"
        )

        fm = analyze_file_metrics("models.py", pydantic_with_validators)
        nodes = _create_function_class_nodes("models.py", fm)

        method_nodes = [n for n in nodes if n.type == "method"]
        method_ids = [n.id for n in method_nodes]

        assert len(method_nodes) == 2, (
            f"Expected 2 method nodes (one per class) but got {len(method_nodes)}: "
            f"{method_ids}\n"
            "Bug: both validators get the same id='models.py::validate_name'"
        )
        assert len(set(method_ids)) == 2, (
            f"Method IDs are not unique: {method_ids}"
        )

        class_ids_of_methods = {n.parent_id for n in method_nodes}
        assert "models.py::UserCreate" in class_ids_of_methods, (
            f"No method under UserCreate. Parent IDs: {class_ids_of_methods}"
        )
        assert "models.py::ProductCreate" in class_ids_of_methods, (
            f"No method under ProductCreate. Parent IDs: {class_ids_of_methods}"
        )

    def test_build_nodes_models_file_complete_pipeline(self):
        """Full pipeline with duplicate method names across classes — all 4 nodes must appear."""
        from pathlib import Path
        from autocode.core.code.architecture import _build_architecture_nodes

        models_py_code = (
            "from pydantic import BaseModel, validator\n"
            "from typing import Optional\n"
            "\n"
            "class CreateRequest(BaseModel):\n"
            "    name: str\n"
            "    value: int\n"
            "\n"
            "    def __init__(self, **data):\n"
            "        super().__init__(**data)\n"
            "\n"
            "    @validator('name')\n"
            "    def validate_name(cls, v):\n"
            "        return v.strip()\n"
            "\n"
            "class UpdateRequest(BaseModel):\n"
            "    name: Optional[str] = None\n"
            "    value: Optional[int] = None\n"
            "\n"
            "    def __init__(self, **data):\n"
            "        super().__init__(**data)\n"
            "\n"
            "    @validator('name')\n"
            "    def validate_name(cls, v):\n"
            "        return v.strip() if v else v\n"
        )

        fpath = "autocode/api/models.py"

        with patch.object(Path, "read_text", return_value=models_py_code):
            nodes = _build_architecture_nodes([fpath])

        node_map = {n.id: n for n in nodes}

        assert f"{fpath}::CreateRequest" in node_map, (
            f"Missing CreateRequest class node. IDs: {list(node_map.keys())}"
        )
        assert f"{fpath}::UpdateRequest" in node_map, (
            f"Missing UpdateRequest class node. IDs: {list(node_map.keys())}"
        )

        method_nodes = [n for n in nodes if n.type == "method"]
        method_ids = [n.id for n in method_nodes]

        assert len(method_nodes) == 4, (
            f"Expected 4 method nodes (2 classes × 2 methods each) but got "
            f"{len(method_nodes)}: {method_ids}\n"
            "Bug: __init__ and validate_name from both classes get colliding IDs"
        )

        assert f"{fpath}::CreateRequest::__init__" in node_map, (
            f"Missing CreateRequest::__init__. Got: {method_ids}"
        )
        assert f"{fpath}::UpdateRequest::__init__" in node_map, (
            f"Missing UpdateRequest::__init__. Got: {method_ids}"
        )
        assert f"{fpath}::CreateRequest::validate_name" in node_map, (
            f"Missing CreateRequest::validate_name. Got: {method_ids}"
        )
        assert f"{fpath}::UpdateRequest::validate_name" in node_map, (
            f"Missing UpdateRequest::validate_name. Got: {method_ids}"
        )
