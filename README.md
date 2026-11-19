Step 1: Start the server

Open the folder in VS Code, open a terminal (Ctrl+`), and run:

cd C:\my-mcp_server
.venv\Scripts\Activate.ps1
python server.py

The server code should end with something like this:
if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)   # FastMCP 2.x
    # with the official mcp SDK, use transport="streamable-http" instead

    Leave this terminal running. The output should show the server listening on http://127.0.0.1:8000/mcp. If you open that address in a browser, an error such as “Not Acceptable” is normal, and it shows the server is up.
    Step 2: Create .vscode/mcp.json

In the project folder, create .vscode\mcp.json:

{
  "servers": {
    "my-mcp-server": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}

The port and the /mcp path must match what the server printed in Step 1.

Step 3: Start the server connection in VS Code

Open mcp.json. A Start link appears above the server name, so click it.
Or press Ctrl+Shift+P, run MCP: List Servers, pick my-mcp-server, and choose Start Server.
If VS Code asks whether you trust the server, read the prompt and choose Trust.
The list should show the server as running with 3 tools. If it fails, choose Show Output in the same menu to read the error.

Step 4: Use it in Copilot Chat

Open Copilot Chat with Ctrl+Alt+I.
Switch the mode dropdown from Ask to Agent. MCP tools only work in Agent mode.
Click the Tools icon in the chat box and check that system_info, list_files and current_time are ticked.
Ask something that needs a tool:
How much free disk space do I have?
What time is it right now?

Copilot shows a confirmation card naming the tool and its inputs. Click Allow (or Continue), and the answer comes back using the tool result. You can also name a tool directly, for example #current_time.
This follows the same pattern as the earlier agent: the model asks for a tool in text, and VS Code runs the call against your server.
Option: let VS Code start the server for you

With HTTP, you start the server yourself each time. For automatic start, use stdio instead. In server.py, change the last line to mcp.run() (stdio is the default), then use this in mcp.json:
{
  "servers": {
    "my-mcp-server": {
      "type": "stdio",
      "command": "C:\\my-mcp_server\\.venv\\Scripts\\python.exe",
      "args": ["C:\\my-mcp_server\\server.py"]
    }
  }
}

VS Code launches the process itself. Make sure the server never uses print() to stdout, because that breaks the protocol, and log to stderr instead.

Daily routine (HTTP version)

Open the folder and start python server.py in a terminal.
Start the server in VS Code (the Start link or MCP: List Servers).
Use Agent mode in Copilot Chat.
After editing the server code, stop and restart it, then choose Restart in MCP: List Servers so the tool list refreshes.

Troubleshooting

Connection refused or the server won’t start in VS Code: the Python server isn’t running, or the port or path doesn’t match. Check Step 1 again.
Port already in use: change port=8000 in both server.py and mcp.json, or stop the old process.
Tools don’t appear in chat: confirm you are in Agent mode, check the server shows as running, and restart it.
No MCP option at all: update VS Code and the Copilot extension. If your Copilot account is managed by an organisation, an admin policy can disable MCP servers, so ask your administrator.
ModuleNotFoundError: fastmcp: the environment isn’t active, or the package isn’t installed. Run pip install fastmcp inside .venv.

Keep it safe

Bind to 127.0.0.1 only, as above, so nobody else on your network can reach it.
Keep the tools read-only, and limit list_files to specific folders instead of the whole disk.
Read each tool confirmation before clicking Allow, especially once you add tools that change things.
