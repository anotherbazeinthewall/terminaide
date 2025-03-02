# terminaide/__init__.py

"""
terminaide: Serve Python CLI applications in the browser using ttyd.

This package provides tools to easily serve Python CLI applications through
a browser-based terminal using ttyd. It handles binary installation and
management automatically across supported platforms.

Supported Platforms:
- Linux x86_64 (Docker containers)
- macOS ARM64 (Apple Silicon)
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union

# Configure package-level logging
logging.getLogger("terminaide").addHandler(logging.NullHandler())

# Core functionality - import directly from serve.py
from .serve import serve_tty, _configure_app
from .core.settings import TTYDConfig

# Installation management
from .installer import setup_ttyd, get_platform_info

# Demo functionality
from .demos import run as demo_run

# Expose all exceptions
from .exceptions import (
    terminaideError,
    BinaryError,
    InstallationError,
    PlatformNotSupportedError,
    DependencyError,
    DownloadError,
    TTYDStartupError,
    TTYDProcessError,
    ClientScriptError,
    TemplateError,
    ProxyError,
    ConfigurationError
)

__version__ = "0.2.0"  # Updated version number
__all__ = [
    # Main functionality
    "serve_tty",
    "TTYDConfig",
    
    # Binary management
    "setup_ttyd",
    "get_platform_info",
    
    # Demo functionality
    "demo_run",
    
    # Exceptions
    "terminaideError",
    "BinaryError",
    "InstallationError",
    "PlatformNotSupportedError",
    "DependencyError",
    "DownloadError",
    "TTYDStartupError",
    "TTYDProcessError",
    "ClientScriptError",
    "TemplateError",
    "ProxyError",
    "ConfigurationError"
]

# Create an alias for better import experience
demos = demo_run