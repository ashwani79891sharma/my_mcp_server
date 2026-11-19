import platform, shutil, datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("laptop-mcp", host="127.0.0.1", port=8000)

@mcp.tool()
def system_info() -> str:
    """Return OS, Python version and free disk space of this laptop."""
    total, used, free = shutil.disk_usage("C:\\")
    return f"{platform.platform()}, Python {platform.python_version()}, free disk {free // 2**30} GB"

@mcp.tool()
def list_files(folder: str = "C:\\my-mcp") -> str:
    """List files in a folder."""
    p = Path(folder)
    if not p.is_dir():
        return "Folder not found"
    return "\n".join(x.name for x in p.iterdir())

@mcp.tool()
def current_time() -> str:
    """Return the current date and time."""
    return datetime.datetime.now().isoformat(timespec="seconds")

if __name__ == "__main__":
    mcp.run(transport="streamable-http")   # http://127.0.0.1:8000/mcp