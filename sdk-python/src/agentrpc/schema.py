"""Module for generating JSON schemas from Python types."""

import json
import inspect
from typing import Any, Callable, Dict, Optional, Type, get_type_hints
import logging
from enum import Enum

try:
    from pydantic import BaseModel
    from pydantic.json_schema import model_json_schema
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

logger = logging.getLogger("agentrpc")

# Type to JSON Schema mapping
TYPE_TO_SCHEMA = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number"},
    bool: {"type": "boolean"},
    list: {"type": "array", "items": {}},
    dict: {"type": "object", "properties": {}, "additionalProperties": True},
    None: {"type": "null"},
}


def generate_schema_from_function(func: Callable) -> Dict[str, Any]:
    """Generate a JSON schema from a function's type annotations.
    
    Args:
        func: The function to analyze.
        
    Returns:
        A JSON schema representing the function's input.
    """
    # Get function signature
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    # Process parameters
    for param_name, param in sig.parameters.items():
        # Skip self/cls for methods
        if param_name in ("self", "cls"):
            continue
            
        param_type = type_hints.get(param_name, Any)
        
        # Process the parameter type
        if PYDANTIC_AVAILABLE and hasattr(param_type, "__origin__") and param_type.__origin__ is type and issubclass(param_type.__args__[0], BaseModel):
            # This is a Pydantic model type
            model_class = param_type.__args__[0]
            model_schema = model_json_schema(model_class)
            schema["properties"][param_name] = model_schema
            if param.default is param.empty:
                schema["required"].append(param_name)
                
        elif PYDANTIC_AVAILABLE and isinstance(param_type, type) and issubclass(param_type, BaseModel):
            # This is a Pydantic model instance
            model_schema = model_json_schema(param_type)
            schema["properties"][param_name] = model_schema
            if param.default is param.empty:
                schema["required"].append(param_name)
                
        else:
            # Handle basic types
            param_schema = TYPE_TO_SCHEMA.get(param_type, {"type": "object"})
            schema["properties"][param_name] = param_schema
            if param.default is param.empty:
                schema["required"].append(param_name)
    
    return schema


def generate_schema_from_model(model_class: Type) -> Dict[str, Any]:
    """Generate a JSON schema from a Pydantic model.
    
    Args:
        model_class: The Pydantic model class.
        
    Returns:
        A JSON schema representing the model.
    """
    if not PYDANTIC_AVAILABLE:
        raise ImportError("Pydantic is required to generate schemas from models")
        
    if not hasattr(model_class, "model_json_schema"):
        raise TypeError(f"Expected a Pydantic model class, got {model_class}")
        
    return model_json_schema(model_class)


def generate_schema_from_type_annotations(func: Callable) -> Dict[str, Any]:
    """Generate a JSON schema from a function's type annotations.
    
    Args:
        func: The function to analyze.
        
    Returns:
        A JSON schema representing the function's first parameter.
    """
    # Get function signature
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    # Get the first parameter (after self/cls if present)
    params = list(sig.parameters.items())
    if not params:
        return {"type": "object", "properties": {}}
        
    # Skip self/cls for methods
    start_idx = 0
    if params[0][0] in ("self", "cls"):
        start_idx = 1
        
    if start_idx >= len(params):
        return {"type": "object", "properties": {}}
        
    first_param_name, first_param = params[start_idx]
    first_param_type = type_hints.get(first_param_name, Any)
    
    # If it's a Pydantic model, use its schema
    if PYDANTIC_AVAILABLE:
        if hasattr(first_param_type, "__origin__") and first_param_type.__origin__ is type and issubclass(first_param_type.__args__[0], BaseModel):
            return generate_schema_from_model(first_param_type.__args__[0])
        elif isinstance(first_param_type, type) and issubclass(first_param_type, BaseModel):
            return generate_schema_from_model(first_param_type)
            
    # For other types, create a basic schema
    return {
        "type": "object",
        "properties": {},
        "additionalProperties": True
    } 