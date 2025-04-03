# demo/server.py
"""
Test server for terminaide that demonstrates all three API tiers.
Usage:
python server.py                     # Default mode - shows getting started interface
python server.py --function          # Function mode - demo of serve_function() with Asteroids
python server.py --script            # Script mode - demo of serve_script()
python server.py --apps              # Apps mode - HTML page at root, terminal games at routes
python server.py --container         # Run the apps mode in a Docker container
"""
import os
import sys
import json
import shutil
import argparse
import tempfile
import subprocess
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from terminaide import serve_function, serve_script, serve_apps
import uvicorn
from terminaide import logger

CURRENT_DIR = Path(__file__).parent
CLIENT_SCRIPT = CURRENT_DIR / "client.py"

MODE_HELP = {
    "default": "Default (getting started interface)",
    "function": "Serve function mode (Asteroids)",
    "script": "Serve script mode",
    "apps": "Apps mode (HTML + routes)",
    "container": "Docker container mode (same as apps)"
}

def create_custom_root_endpoint(app: FastAPI):
    @app.get("/", response_class=HTMLResponse)
    async def custom_root(request: Request):
        title_mode = "Container" if os.environ.get("CONTAINER_MODE") == "true" else "Apps"
        html_content = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>Termin-Arcade ({title_mode})</title>
            <link rel="icon" type="image/x-icon" href="{request.url_for('static', path='favicon.ico')}">
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    line-height: 1.5;
                    background-color: black;
                    color: #f0f0f0;
                    text-align: center;
                    padding: 40px 20px;
                    margin: 0;
                }}
                .ascii-banner pre {{
                    margin: 0 auto 40px;
                    white-space: pre;
                    line-height: 1;
                    display: inline-block;
                    text-align: left;
                    background: linear-gradient(
                        to right,
                        red,
                        orange,
                        yellow,
                        green,
                        blue,
                        indigo,
                        violet
                    );
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    color: transparent;
                }}
                .card {{
                    background-color: #2d2d2d;
                    max-width: 600px;
                    margin: 0 auto 30px;
                    padding: 20px;
                }}
                .terminal-box {{
                    border: 1px solid #fff;
                    max-width: 400px;
                    margin: 30px auto;
                    padding: 10px;
                    color: #fff;
                }}
                .links {{
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                    margin: 30px auto;
                }}
                .terminal-link {{
                    display: inline-block;
                    background-color: #fff;
                    color: #000;
                    padding: 8px 20px;
                    text-decoration: none;
                    font-weight: bold;
                }}
                .info-link {{
                    color: #fff;
                    text-decoration: none;
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <div class="ascii-banner">
                <pre>████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗      █████╗ ██████╗  ██████╗ █████╗ ██████╗ ███████╗
╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║     ██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝
   ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║     ███████║██████╔╝██║     ███████║██║  ██║█████╗  
   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║     ██╔══██║██╔══██╗██║     ██╔══██║██║  ██║██╔══╝  
   ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║     ██║  ██║██║  ██║╚██████╗██║  ██║██████╔╝███████╗
   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝     ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝</pre>
            </div>
            <div class="card">
                This demo shows how HTML pages and terminal applications can be combined in one server.
                Each game runs in its own terminal instance.
            </div>
            <div class="terminal-box">
                Available Games
            </div>
            <div class="links">
                <a href="/snake" class="terminal-link">Snake</a>
                <a href="/tetris" class="terminal-link">Tetris</a>
                <a href="/pong" class="terminal-link">Pong</a>
            </div>
            <a href="/info" class="info-link">Server Configuration Info</a>
        </body>
        </html>"""
        return HTMLResponse(html_content)

def create_info_endpoint(app: FastAPI, mode: str, description: str):
    @app.get("/info", response_class=HTMLResponse)
    async def info(request: Request):
        info_dict = {
            "mode": mode,
            "description": description,
            "client_script": str(CLIENT_SCRIPT),
            "modes": MODE_HELP,
            "usage": "python server.py [--default|--function|--script|--apps|--container]",
            "notes": [
                "serve_function: Simplest - just pass a function",
                "serve_script: Simple - pass a script file",
                "serve_apps: Advanced - integrate with FastAPI"
            ]
        }
        return f"""<!DOCTYPE html>
        <html>
        <head>
            <title>Terminaide Info</title>
            <link rel="icon" type="image/x-icon" href="{request.url_for('static', path='favicon.ico')}">
        </head>
        <body><pre>{json.dumps(info_dict, indent=2)}</pre></body>
        </html>"""

def play_asteroids_function():
    from terminarcade import play_asteroids
    play_asteroids()

def create_app():
    """
    Factory function: read mode from environment, build and return FastAPI app.
    Used by Uvicorn with 'factory=True' so it can reload properly.
    """
    mode = os.environ.get("TERMINAIDE_MODE", "default")
    app = FastAPI(title=f"Terminaide - {mode.upper()} Mode")
    description = ""
    
    # Don't try to use any Docker stuff here - just handle the apps mode
    if mode == "apps":
        description = "Apps mode - HTML root + separate terminal routes"
        create_custom_root_endpoint(app)
        serve_apps(
            app,
            terminal_routes={
                "/snake": {"client_script": [CLIENT_SCRIPT, "--snake"], "title": "Termin-Arcade (Snake)"},
                "/tetris": {"client_script": [CLIENT_SCRIPT, "--tetris"], "title": "Termin-Arcade (Tetris)"},
                "/pong":   {"client_script": [CLIENT_SCRIPT, "--pong"],   "title": "Termin-Arcade (Pong)"}
            },
            debug=True
        )
        create_info_endpoint(app, mode, description)
    
    return app

def generate_requirements_txt(pyproject_path, temp_dir):
    try:
        logger.info("Generating requirements.txt (excluding dev)")
        req_path = Path(temp_dir) / "requirements.txt"
        result = subprocess.run(
            ["poetry", "export", "--without", "dev", "--format", "requirements.txt"],
            cwd=pyproject_path.parent, capture_output=True, text=True, check=True
        )
        with open(req_path, "w") as f:
            f.write(result.stdout)
        logger.info(f"Requirements file at {req_path}")
        return req_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate requirements: {e}\nPoetry output: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to generate requirements: {e}")
        sys.exit(1)

def build_and_run_container(port=8000):
    try:
        import docker
        
        # Get the correct Docker socket location from the context
        context_result = subprocess.run(['docker', 'context', 'inspect'], 
                                     capture_output=True, text=True)
        if context_result.returncode == 0:
            context_data = json.loads(context_result.stdout)
            if context_data and 'Endpoints' in context_data[0]:
                docker_host = context_data[0]['Endpoints']['docker']['Host']
                client = docker.DockerClient(base_url=docker_host)
        else:
            client = docker.from_env()
            
        client.ping()
        
        logger.info("Connected to Docker daemon")
        project_root = Path(__file__).parent.parent.absolute()
        image_name = project_root.name.lower()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Add 'terminarcade' to the list of directories
            for directory in ["terminaide", "demo", "terminarcade"]:  # Add "terminarcade" here
                src_dir = project_root / directory
                dst_dir = temp_path / directory
                if src_dir.exists():
                    # Basic solution - ensure bin directory exists but is empty
                    shutil.copytree(src_dir, dst_dir, ignore=lambda src, names:
                        ['ttyd'] if os.path.basename(src) == 'bin' else [])
                    # Alternatively, create an empty bin directory if it was excluded
                    (dst_dir / 'bin').mkdir(exist_ok=True)
            generate_requirements_txt(project_root / "pyproject.toml", temp_path)
            dockerfile_content = """
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
WORKDIR /app
COPY terminaide/ ./terminaide/
COPY terminarcade/ ./terminarcade/
COPY demo/ ./demo/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["python", "demo/server.py", "--apps"]
"""
            dockerfile_path = temp_path / "Dockerfile"
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)
            logger.info(f"Building Docker image: {image_name}")
            image, build_logs = client.images.build(
                path=str(temp_path),
                tag=image_name,
                rm=True
            )
            for log in build_logs:
                if 'stream' in log:
                    line = log['stream'].strip()
                    if line:
                        logger.info(f"Build: {line}")
            container_name = f"{image_name}-container"
            try:
                old_container = client.containers.get(container_name)
                old_container.stop()
                old_container.remove()
            except docker.errors.NotFound:
                pass
            logger.info(f"Starting container {container_name} on port {port}")
            c = client.containers.run(
                image.id,
                name=container_name,
                ports={f"8000/tcp": port},
                detach=True,
                environment={"CONTAINER_MODE": "true"}
            )
            logger.info(f"Container {container_name} started (ID: {c.id[:12]})")
            logger.info(f"Access at: http://localhost:{port}")
            logger.info("Streaming container logs (Ctrl+C to stop)")
            try:
                for line in c.logs(stream=True):
                    print(line.decode().strip())
            except KeyboardInterrupt:
                logger.info("Stopping container...")
                c.stop()
                logger.info("Container stopped")
    except Exception as e:
        if "docker" in str(e.__class__):
            logger.error(f"Docker error: {e}")
            logger.error("Ensure Docker is installed and running")
        else:
            logger.error(f"Error: {e}")
        sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser()
    # Add boolean flags for each mode
    parser.add_argument("--default", action="store_true", help="Runs the default instructions")
    parser.add_argument("--function", action="store_true", help="Serves a function")
    parser.add_argument("--script", action="store_true", help="Serves a script")
    parser.add_argument("--apps", action="store_true", help="Serves multiple scripts")
    parser.add_argument("--container", action="store_true", help="Same as serve apps but in a container")
    
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    
    # Determine which mode was selected
    mode_flags = {
        "default": args.default,
        "function": args.function,
        "script": args.script,
        "apps": args.apps,
        "container": args.container
    }
    
    # Find selected mode, defaulting to "default" if none specified
    selected_modes = [mode for mode, flag in mode_flags.items() if flag]
    
    if len(selected_modes) > 1:
        logger.error(f"Only one mode can be selected, but found: {', '.join(selected_modes)}")
        sys.exit(1)
    
    args.actual_mode = selected_modes[0] if selected_modes else "default"
    return args

def main():
    args = parse_args()
    mode = args.actual_mode
    port = args.port
    os.environ["TERMINAIDE_MODE"] = mode
    
    if mode != "container":
        os.environ["WATCHFILES_FORCE_POLLING"] = "0"
        os.environ["WATCHFILES_POLL_DELAY"] = "0.1"
        os.environ["TERMINAIDE_VERBOSE"] = "0"
        log_level = "WARNING" if mode != "apps" else "INFO"
        # Set terminaide logger level directly
        logger.setLevel(log_level)
        # Also set uvicorn logger level
        import logging
        logging.getLogger("uvicorn").setLevel(log_level)
        
    logger.info(f"Starting server in {mode.upper()} mode on port {port}")
    
    if mode == "container":
        build_and_run_container(port)
        return
    
    # DEFAULT MODE
    if mode == "default":
        instructions_path = CURRENT_DIR.parent / "terminarcade" / "instructions.py"
        serve_script(
            instructions_path,
            port=port,
            title="Terminaide (Intro)",
            debug=True,
            reload=True    # <-- Enable reload for default mode
        )
        return
    
    # FUNCTION MODE
    if mode == "function":
        serve_function(
            play_asteroids_function,
            port=port,
            title="Termin-Asteroids (Function)",
            debug=True,
            reload=True   # <-- Enable reload for function mode
        )
        return
    
    # SCRIPT MODE
    if mode == "script":
        serve_script(
            CLIENT_SCRIPT,
            port=port,
            title="Termin-Arcade (Script)",
            debug=True,
            reload=True   # <-- Enable reload for script mode
        )
        return
    
    # APPS MODE
    if mode == "apps":
        logger.info(f"Visit http://localhost:{port} for the main interface")
        logger.info(f"Visit http://localhost:{port}/info for details")
        uvicorn.run(
            "demo.server:create_app",
            factory=True,
            host="0.0.0.0",
            port=port,
            reload=True,
            reload_dirs=[str(CURRENT_DIR.parent)]
        )

if __name__ == '__main__':
    main()