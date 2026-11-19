import platform, shutil, datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from monitoring import monitored

mcp = FastMCP("laptop-mcp", host="127.0.0.1", port=8000)
ALLOWED_FOLDER = Path(__file__).resolve().parent

@mcp.tool()
@monitored 
def system_info() -> str:
    """Return OS, Python version and free disk space of this laptop."""
    _, _, free = shutil.disk_usage(Path.home())
    return f"{platform.platform()}, Python {platform.python_version()}, free disk {free // 2**30} GB"

@mcp.tool()
@monitored 
def list_files(folder: str = ".") -> str:
    """List files within the MCP server folder."""
    try:
        requested = Path(folder)
        p = (ALLOWED_FOLDER if folder == "." else
             requested if requested.is_absolute() else ALLOWED_FOLDER / requested).resolve()
        p.relative_to(ALLOWED_FOLDER)
    except (OSError, ValueError):
        return "Access denied: folder is outside the MCP server folder"
    if not p.is_dir():
        return "Folder not found"
    try:
        return "\n".join(sorted(x.name for x in p.iterdir()))
    except OSError as exc:
        return f"Unable to list folder: {exc}"

@mcp.tool()
@monitored 
def current_time() -> str:
    """Return the current date and time."""
    return datetime.datetime.now().isoformat(timespec="seconds")

if __name__ == "__main__":
    mcp.run(transport="streamable-http")   # http://127.0.0.1:8000/mcp