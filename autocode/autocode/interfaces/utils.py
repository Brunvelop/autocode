"""
Utility functions for inferring parameters and models from function signatures.
This module provides the core inference logic that eliminates duplication in the registry.
"""
import inspect
from typing import Dict, Any, List, Type, get_type_hints, get_origin, get_args, Union, Optional
from pydantic import BaseModel, Field, create_model
from autocode.autocode.interfaces.models import BaseFunctionInput, BaseFunctionOutput, GenericInput, GenericOutput


class InferenceUtils:
    """Utility class for inferring function information from signatures and type hints."""
    
    @staticmethod
    def infer_parameters(func) -> List[Dict[str, Any]]:
        """
        Extract parameter information from a function signature.
        
        Args:
            func: The function to analyze
            
        Returns:
            List of parameter dictionaries with name, type, default, required, description
        """
        params = []
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Parse docstring for parameter descriptions
        doc_params = InferenceUtils._parse_docstring_params(func)
        
        for param_name, param_info in signature.parameters.items():
            param_type = type_hints.get(param_name, str)
            
            # Handle Optional types
            is_optional = False
            if get_origin(param_type) is Union:
                args = get_args(param_type)
                if type(None) in args:
                    is_optional = True
                    # Get the non-None type
                    param_type = next(arg for arg in args if arg is not type(None))
            
            # Determine if required
            has_default = param_info.default != inspect.Parameter.empty
            required = not (has_default or is_optional)
            
            # Get default value
            default_value = param_info.default if has_default else None
            
            # Convert type to string representation
            type_str = InferenceUtils._type_to_string(param_type)
            
            param_dict = {
                "name": param_name,
                "type": type_str,
                "required": required,
                "default": default_value,
                "description": doc_params.get(param_name, f"Parameter {param_name}")
            }
            
            params.append(param_dict)
        
        return params
    
    @staticmethod
    def infer_input_model(func) -> Type[BaseModel]:
        """
        Dynamically create a Pydantic input model from function signature.
        
        Args:
            func: The function to analyze
            
        Returns:
            Dynamically generated Pydantic model class
        """
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        if not signature.parameters:
            # No parameters, use GenericInput
            return GenericInput
        
        # Build fields for the dynamic model
        fields = {}
        
        for param_name, param_info in signature.parameters.items():
            param_type = type_hints.get(param_name, str)
            
            # Handle Optional types
            if get_origin(param_type) is Union:
                args = get_args(param_type)
                if type(None) in args:
                    # Get the non-None type for Optional
                    param_type = next(arg for arg in args if arg is not type(None))
            
            # Determine default
            if param_info.default != inspect.Parameter.empty:
                default_value = param_info.default
                field_info = Field(default=default_value, description=f"Parameter {param_name}")
            else:
                field_info = Field(description=f"Parameter {param_name}")
            
            fields[param_name] = (param_type, field_info)
        
        # Create dynamic model
        model_name = f"{func.__name__.title()}Input"
        dynamic_model = create_model(
            model_name,
            __base__=BaseFunctionInput,
            **fields
        )
        
        return dynamic_model
    
    @staticmethod
    def infer_output_model(func) -> Type[BaseModel]:
        """
        Create a Pydantic output model based on function return annotation.
        
        Args:
            func: The function to analyze
            
        Returns:
            Dynamically generated Pydantic model class or GenericOutput
        """
        signature = inspect.signature(func)
        return_annotation = signature.return_annotation
        
        if return_annotation == inspect.Signature.empty or return_annotation == Any:
            # No return annotation, use GenericOutput
            return GenericOutput
        
        # Simple types - create a model with a single field
        if return_annotation in (str, int, float, bool):
            model_name = f"{func.__name__.title()}Output"
            
            # Determine field name based on return type
            if return_annotation == str:
                field_name = "message"
            elif return_annotation in (int, float):
                field_name = "result"
            else:
                field_name = "value"
            
            dynamic_model = create_model(
                model_name,
                __base__=BaseFunctionOutput,
                **{field_name: (return_annotation, Field(description=f"Function result"))}
            )
            
            return dynamic_model
        
        # For complex types, use GenericOutput
        return GenericOutput
    
    @staticmethod
    def _parse_docstring_params(func) -> Dict[str, str]:
        """
        Parse parameter descriptions from function docstring.
        
        Args:
            func: The function to analyze
            
        Returns:
            Dictionary mapping parameter names to descriptions
        """
        docstring = inspect.getdoc(func)
        param_descriptions = {}
        
        if not docstring:
            return param_descriptions
        
        # Simple parsing for Args: section
        in_args_section = False
        for line in docstring.split('\n'):
            line = line.strip()
            
            if line.lower().startswith('args:'):
                in_args_section = True
                continue
            elif line.lower().startswith('returns:') or line.lower().startswith('raises:'):
                in_args_section = False
                continue
            
            if in_args_section and ':' in line:
                # Parse "param_name: description" format
                parts = line.split(':', 1)
                if len(parts) == 2:
                    param_name = parts[0].strip()
                    description = parts[1].strip()
                    param_descriptions[param_name] = description
        
        return param_descriptions
    
    @staticmethod
    def _type_to_string(type_hint) -> str:
        """
        Convert a type hint to a string representation.
        
        Args:
            type_hint: The type hint to convert
            
        Returns:
            String representation of the type
        """
        if type_hint == str:
            return "str"
        elif type_hint == int:
            return "int"
        elif type_hint == float:
            return "float"
        elif type_hint == bool:
            return "bool"
        elif type_hint == list:
            return "list"
        elif type_hint == dict:
            return "dict"
        else:
            return str(type_hint)
