#!/usr/bin/env python3
"""
Example script demonstrating tool registration with AgentRPC.

This example shows how to:
1. Create an AgentRPC client
2. Register tools using both decorator and function syntax
3. Listen for tool invocations
4. Handle graceful shutdown

To run this example:
1. Set the AGENTRPC_API_SECRET environment variable to your API secret
2. Run the script: python tool_registration.py
"""

import os
import signal
import sys
import time
from typing import Dict, List, Optional

from agentrpc import AgentRPC

# Get API secret from environment variable
API_SECRET = os.environ.get("AGENTRPC_API_SECRET")
if not API_SECRET:
    print("Error: AGENTRPC_API_SECRET environment variable not set.")
    print("Please set it to your API secret from https://app.agentrpc.com")
    sys.exit(1)

# Create the AgentRPC client
rpc = AgentRPC(API_SECRET)
print(f"AgentRPC client initialized with cluster ID: {rpc.cluster_id}")

# Register tools
# Example 1: Basic function with primitive types
@rpc.register(name="greet", description="Greet a person by name")
def greet(name: str) -> str:
    """Return a greeting for the given name.
    
    Args:
        name: The name to greet
        
    Returns:
        A greeting message
    """
    return f"Hello, {name}!"

# Example 2: Function with multiple parameters and different return type
@rpc.register(description="Calculate the sum of two numbers")
def calculate_sum(a: int, b: int) -> int:
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The sum of a and b
    """
    return a + b

# Example 3: Function returning a complex object
@rpc.register(name="get_user_info", description="Get information about a user")
def get_user_info(user_id: str) -> Dict:
    """Retrieve information about a user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        A dictionary containing user information
    """
    # In a real application, this would fetch data from a database
    users = {
        "1": {"name": "Alice", "email": "alice@example.com", "role": "admin"},
        "2": {"name": "Bob", "email": "bob@example.com", "role": "user"},
        "3": {"name": "Charlie", "email": "charlie@example.com", "role": "user"},
    }
    
    if user_id in users:
        return users[user_id]
    else:
        return {"error": f"User {user_id} not found"}

# Example 4: Function with optional parameters
@rpc.register
def search_items(query: str, category: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Search for items matching the query.
    
    Args:
        query: The search query
        category: Optional category to filter by
        limit: Maximum number of results to return
        
    Returns:
        A list of matching items
    """
    # In a real application, this would search a database
    items = [
        {"id": "1", "name": "Laptop", "category": "electronics", "price": 999.99},
        {"id": "2", "name": "Smartphone", "category": "electronics", "price": 499.99},
        {"id": "3", "name": "Chair", "category": "furniture", "price": 149.99},
        {"id": "4", "name": "Table", "category": "furniture", "price": 249.99},
        {"id": "5", "name": "Book", "category": "books", "price": 19.99},
    ]
    
    # Filter by query (case-insensitive)
    results = [item for item in items if query.lower() in item["name"].lower()]
    
    # Filter by category if provided
    if category:
        results = [item for item in results if item["category"] == category]
    
    # Apply limit
    results = results[:limit]
    
    return results

# Example 5: Register a function with direct syntax
def process_order(order_id: str, items: List[Dict], customer_info: Dict) -> Dict:
    """Process an order.
    
    Args:
        order_id: The order ID
        items: List of items in the order
        customer_info: Customer information
        
    Returns:
        Order processing result
    """
    # Calculate total price
    total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
    
    # In a real application, this would create an order in a database
    result = {
        "order_id": order_id,
        "status": "processed",
        "total": total,
        "customer": customer_info.get("name", "Unknown"),
        "items_count": len(items)
    }
    
    return result

# Register using the direct function syntax
rpc.register(
    process_order,
    name="process_order",
    description="Process a new order with items and customer information"
)

# Set up graceful shutdown
def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    print("\nReceived shutdown signal. Stopping AgentRPC client...")
    rpc.unlisten()
    print("AgentRPC client stopped. Exiting.")
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, handle_shutdown)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, handle_shutdown)  # Handle termination signal

# Start listening for tool invocations
print(f"Starting AgentRPC client with {len(rpc._AgentRPC__polling_agent.tools)} registered tools:")
for name in rpc._AgentRPC__polling_agent.tools:
    print(f"- {name}")
    
print("\nStarting to listen for tool invocations...")
print("Press Ctrl+C to stop.")

# Start listening (this is a blocking call)
try:
    rpc.listen()
    
    # Keep the main thread alive
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    # Handle Ctrl+C
    print("\nShutting down...")
    rpc.unlisten()
    print("Goodbye!") 