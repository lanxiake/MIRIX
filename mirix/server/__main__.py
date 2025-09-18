#!/usr/bin/env python3
"""
Main entry point for Mirix server when called with python -m mirix.server.server
"""

import sys
import argparse
import os
from pathlib import Path

def main():
    """Main entry point for Mirix server."""
    parser = argparse.ArgumentParser(description='Mirix AI Assistant Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=None, help='Port to bind the server to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Determine port from command line, environment variable, or default
    port = args.port
    if port is None:
        port = int(os.environ.get('PORT', 47283))
    
    print(f"Starting Mirix server on {args.host}:{port}")
    if args.debug:
        print("Debug mode enabled")
    
    import uvicorn
    from mirix.server import app
    
    # Configure uvicorn log level based on debug flag
    log_level = "debug" if args.debug else "info"
    
    uvicorn.run(
        app, 
        host=args.host, 
        port=port,
        log_level=log_level,
        access_log=args.debug
    )

if __name__ == "__main__":
    main()