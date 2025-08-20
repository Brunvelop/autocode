"""
FastAPI server with dynamic endpoints from registry and static file serving.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import inspect

from autocode.autocode.interfaces.registry import (
    FUNCTION_REGISTRY, 
    get_function, 
    get_function_info,
    get_input_model,
    get_output_model
)
from autocode.autocode.interfaces.models import BaseFunctionInput, BaseFunctionOutput

def create_dynamic_dependency(input_model):
    """Create a dynamic dependency function for query parameters."""
    if not input_model:
        return None
    
    # Create a function that FastAPI can use as a dependency
    def dependency(**kwargs):
        # Filter kwargs to only include fields that exist in the model
        valid_kwargs = {}
        for field_name in input_model.model_fields.keys():
            if field_name in kwargs:
                valid_kwargs[field_name] = kwargs[field_name]
        
        return input_model(**valid_kwargs)
    
    # Set the function signature dynamically based on the model
    sig_params = []
    for field_name, field_info in input_model.model_fields.items():
        default_value = field_info.default if field_info.default is not ... else None
        param = inspect.Parameter(
            field_name,
            inspect.Parameter.KEYWORD_ONLY,
            default=default_value,
            annotation=Optional[field_info.annotation] if default_value is not None else field_info.annotation
        )
        sig_params.append(param)
    
    dependency.__signature__ = inspect.Signature(sig_params)
    return dependency


def create_result_response(result, output_model):
    """Helper function to format result response."""
    if output_model:
        if isinstance(result, str):
            # Assume single field output for string results
            output_fields = list(output_model.model_fields.keys())
            if output_fields:
                return output_model(**{output_fields[0]: result})
        elif isinstance(result, (int, float)):
            # Handle numeric results - assume "result" field
            output_fields = list(output_model.model_fields.keys())
            if "result" in output_fields:
                return output_model(result=result)
            elif output_fields:
                return output_model(**{output_fields[0]: result})
        elif isinstance(result, dict):
            return output_model(**result)
        else:
            return output_model(result=result)
    else:
        return {"result": result}


def create_api_app() -> FastAPI:
    """Create an independent FastAPI app for API server."""
    app = FastAPI(
        title="Autocode API",
        description="Minimalistic framework for code quality tools",
        version="1.0.0"
    )

    # Create specific endpoints from registry - no generic handlers
    for func_name, func_info in FUNCTION_REGISTRY.items():
        func = func_info.func
        input_model = get_input_model(func_name)  # Use inference
        output_model = get_output_model(func_name)  # Use inference
        
        for method in func_info.http_methods:
            if method.upper() == "POST" and input_model:
                # Create specific POST endpoint
                def make_post_handler(target_func, target_input_model, target_output_model):
                    async def post_handler(request: target_input_model):
                        try:
                            # Get function signature to match parameters
                            sig = inspect.signature(target_func)
                            params = {}
                            
                            # Map request fields to function parameters
                            for param_name in sig.parameters.keys():
                                if hasattr(request, param_name):
                                    params[param_name] = getattr(request, param_name)
                            
                            result = target_func(**params)
                            return create_result_response(result, target_output_model)
                            
                        except Exception as e:
                            raise HTTPException(status_code=500, detail=str(e))
                    return post_handler
                
                handler = make_post_handler(func, input_model, output_model)
                
            elif method.upper() == "GET":
                # Create specific GET endpoint
                dependency = create_dynamic_dependency(input_model)
                
                if dependency:
                    from fastapi import Depends
                    
                    def make_get_handler_with_params(target_func, target_input_model, target_output_model, target_dependency):
                        async def get_handler(params: target_input_model = Depends(target_dependency)):
                            try:
                                # Get function signature to match parameters
                                sig = inspect.signature(target_func)
                                func_params = {}
                                
                                # Map model fields to function parameters
                                for param_name in sig.parameters.keys():
                                    if hasattr(params, param_name):
                                        func_params[param_name] = getattr(params, param_name)
                                
                                result = target_func(**func_params)
                                return create_result_response(result, target_output_model)
                                
                            except Exception as e:
                                raise HTTPException(status_code=500, detail=str(e))
                        return get_handler
                    
                    handler = make_get_handler_with_params(func, input_model, output_model, dependency)
                    
                else:
                    # Fallback for functions without input models
                    def make_get_handler_no_params(target_func, target_output_model):
                        async def get_handler():
                            try:
                                result = target_func()
                                return create_result_response(result, target_output_model)
                                
                            except Exception as e:
                                raise HTTPException(status_code=500, detail=str(e))
                        return get_handler
                    
                    handler = make_get_handler_no_params(func, output_model)
            
            else:
                continue  # Skip unsupported methods
            
            # Add the specific route
            path = f"/{func_name}"
            operation_id = f"{func_name}_{method.lower()}"
            
            app.add_api_route(
                path, 
                handler, 
                methods=[method],
                response_model=output_model,
                operation_id=operation_id,
                summary=func_info.description
            )

    @app.get("/")
    async def root():
        """Root endpoint - serve the web UI."""
        return FileResponse("autocode/autocode/web/index.html")

    @app.get("/functions")
    async def list_functions():
        """List all available functions."""
        return {"functions": list(FUNCTION_REGISTRY.keys())}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "functions": len(FUNCTION_REGISTRY)}

    # Mount static files (web directory)
    if os.path.exists("autocode/autocode/web"):
        app.mount("/static", StaticFiles(directory="autocode/autocode/web"), name="static")

    return app
