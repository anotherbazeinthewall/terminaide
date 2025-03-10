#!/usr/bin/env python3
# tests/server.py

"""
Test server for terminaide that supports multiple configuration patterns.

This script demonstrates four key ways of configuring terminaide to understand
how each pattern works in practice:

Usage:
    python server.py                  # Default mode - shows instructions demo
    python server.py --mode single    # Single client script (Tetris) at root
    python server.py --mode multi     # Multiple script routes with index at root
    python server.py --mode mixed     # HTML page at root, scripts at other routes
"""

import argparse
import logging
import os
import sys
import json
from pathlib import Path
from typing import Dict, Optional, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from terminaide import serve_tty

import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:     %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the current directory
CURRENT_DIR = Path(__file__).parent
CLIENT_SCRIPT = CURRENT_DIR / "client.py"


def create_custom_root_endpoint(app: FastAPI):
    """Add a custom root endpoint to the app that returns HTML."""
    @app.get("/", response_class=HTMLResponse)
    async def custom_root(request: Request):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Terminaide</title>
            <link rel="icon" type="image/x-icon" href="{request.url_for('static', path='favicon.ico')}">
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    line-height: 1.5;
                    color: #f0f0f0;
                    background-color: black;
                    text-align: center;
                    padding: 40px 20px;
                    margin: 0;
                }}
                h1 {{
                    color: #3498db;
                    border-bottom: 1px solid #3498db;
                    padding-bottom: 15px;
                    margin: 0 auto 30px;
                    max-width: 600px;
                }}
                .card {{
                    background-color: #2d2d2d;
                    max-width: 600px;
                    margin: 0 auto 30px;
                    padding: 20px;
                }}
                .terminal-box {{
                    border: 1px solid #3498db;
                    max-width: 400px;
                    margin: 30px auto;
                    padding: 10px;
                }}
                .links {{
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                    margin: 30px auto;
                }}
                .terminal-link {{
                    display: inline-block;
                    background-color: #3498db;
                    color: #000;
                    padding: 8px 20px;
                    text-decoration: none;
                    font-weight: bold;
                }}
                .info-link {{
                    color: #3498db;
                    text-decoration: none;
                    margin-top: 40px;
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <h1>Terminaide Terminal Games</h1>
            
            <div class="card">
                This demo shows how HTML pages and terminal applications can be combined in one server.
            </div>
            
            <div class="terminal-box">
                Available Terminal Games
            </div>
            
            <div class="links">
                <a href="/terminal1" class="terminal-link">Snake Game</a>
                <a href="/terminal2" class="terminal-link">Pong Game</a>
                <a href="/terminal3" class="terminal-link">Tetris Game</a>
            </div>
            
            <a href="/info" class="info-link">Server Configuration Info</a>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)


def create_info_endpoint(app: FastAPI, mode: str, description: str):
    """Add an info endpoint that explains the current configuration."""
    @app.get("/info", response_class=HTMLResponse)
    async def info(request: Request):
        info_dict = {
            "mode": mode,
            "description": description,
            "client_script": str(CLIENT_SCRIPT),
            "modes": {
                "default": "Default configuration - shows instructions demo",
                "single": "Single script at root - Tetris game",
                "multi": "Multiple scripts with index.py at root, games at other routes",
                "mixed": "HTML page at root, games at other routes"
            },
            "usage": "Change mode by running with --mode [mode_name]",
            "notes": [
                "Route priority: User-defined routes take precedence over terminaide routes",
                "Order of route definition matters",
                "Custom routes can be defined before or after serve_tty() with different results"
            ]
        }
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Terminaide Info</title>
    <link rel="icon" type="image/x-icon" href="{request.url_for('static', path='favicon.ico')}">
</head>
<body>
    <pre>{json.dumps(info_dict, indent=2)}</pre>
</body>
</html>"""


def create_app() -> FastAPI:
    """
    Factory function that Uvicorn will import and call on each reload.

    Reads the mode from the environment instead of a global variable so that
    watchfiles reload can re-import this factory.
    
    Important notes about terminaide configuration:
    
    1. Route Priority: When both a custom route and a terminaide route target 
       the same path, the one defined FIRST in the code takes precedence.
    
    2. Root Path Handling: If you want your own content at the root path (/),
       either define your route BEFORE calling serve_tty() or don't specify
       a client_script or root path in script_routes when calling serve_tty().
    
    3. Configuration Interactions: 
       - If client_script is provided, it runs at the root path (/)
       - If script_routes includes "/", it overrides the default behavior
       - If neither is specified, terminaide shows its instructions demo
    
    4. FastAPI Integration: Terminaide works seamlessly with existing FastAPI
       applications, but be mindful of route conflicts and priorities.
    """
    # Get mode from environment or use default
    mode = os.environ.get("TERMINAIDE_MODE", "default")
    app = FastAPI(title=f"Terminaide Test - {mode.upper()} Mode")

    # We declare a local variable to describe the current configuration
    description = ""

    # Mode-specific configuration
    if mode == "default":
        # Default mode: no client script, no script routes
        # Important: In this configuration, terminaide will show its built-in instructions demo
        description = "Default configuration - shows instructions demo"
        serve_tty(
            app,
            title="Default Mode",
            debug=True
        )
        
    elif mode == "single":
        # Single mode: just one client script at root
        # This demonstrates running a standalone terminal application
        description = "Single script at root - Tetris game"
        serve_tty(
            app,
            client_script=[CLIENT_SCRIPT, "--tetris"],
            title="Single Script Mode",
            debug=True
        )
        
    elif mode == "multi":
        # Multi mode: client script (index) at root + script routes for games
        # This demonstrates a central menu with links to other terminal applications
        description = "Multiple scripts with index.py at root, games at other routes"
        serve_tty(
            app,
            client_script=[CLIENT_SCRIPT, "--index"],      # Index menu at root
            script_routes={
                "/terminal1": [CLIENT_SCRIPT, "--snake"],  # Snake game
                "/terminal2": [CLIENT_SCRIPT, "--pong"],   # Pong game
                "/terminal3": [CLIENT_SCRIPT, "--tetris"]  # Tetris game
            },
            title="Multi-Script Mode",
            debug=True
        )
        
    elif mode == "mixed":
        # Mixed mode: HTML page at root + script routes for games
        # This demonstrates how terminaide can be integrated with regular web pages
        description = "HTML page at root, games at other routes"
        
        # Define custom HTML root BEFORE serve_tty
        # Note: Order matters! The first route defined for a path takes precedence.
        # If we were to call serve_tty() before defining this route, and if serve_tty 
        # tried to assign a route to "/", terminaide's route would take precedence.
        # This demonstrates an important principle: route definition order determines priority.
        create_custom_root_endpoint(app)
        
        # When serve_tty is called, it will NOT override our custom root route
        # because we defined it first.
        serve_tty(
            app,
            script_routes={
                "/terminal1": [CLIENT_SCRIPT, "--snake"],  # Snake game
                "/terminal2": [CLIENT_SCRIPT, "--pong"],   # Pong game
                "/terminal3": [CLIENT_SCRIPT, "--tetris"]  # Tetris game
            },
            title="Mixed Mode",
            debug=True
        )
        
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # Add info endpoint
    create_info_endpoint(app, mode, description)

    return app


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test server for terminaide with different configuration patterns."
    )
    parser.add_argument(
        "--mode",
        choices=["default", "single", "multi", "mixed"],
        default="default",
        help="Which configuration pattern to test (default: default)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    return parser.parse_args()


def main():
    """
    Main function to run the server with watchfiles reload.
    We store --mode in an environment variable so create_app() can read it
    after re-importing this module on each reload.
    """
    args = parse_args()

    # Set mode in an env variable so create_app() sees it on reload
    os.environ["TERMINAIDE_MODE"] = args.mode

    logger.info(f"Starting server in {args.mode.upper()} mode on port {args.port}")
    logger.info(f"Visit http://localhost:{args.port} to see the main interface")
    logger.info(f"Visit http://localhost:{args.port}/info for configuration details")

    # Mode-specific information
    if args.mode == "default":
        logger.info("Default mode - showing built-in instructions demo")
    elif args.mode == "single":
        logger.info("Single mode - Tetris game running at root path (/)")
    elif args.mode == "multi":
        logger.info("Multi mode - index.py menu at root with links to:")
        logger.info("  /terminal1 - Snake Game")
        logger.info("  /terminal2 - Pong Game")
        logger.info("  /terminal3 - Tetris Game")
    elif args.mode == "mixed":
        logger.info("Mixed mode - HTML page at root with links to:")
        logger.info("  /terminal1 - Snake Game")
        logger.info("  /terminal2 - Pong Game")
        logger.info("  /terminal3 - Tetris Game")

    uvicorn.run(
        "tests.server:create_app",
        factory=True,
        host="0.0.0.0",
        port=args.port,
        log_level="info",
        reload=True,
        reload_dirs=[str(CURRENT_DIR.parent)]
    )


if __name__ == '__main__':
    main()