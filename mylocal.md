C:/trainings/build_effective_agents/py310env/Scripts/activate.bat
fastmcp run 03_mcp_training/server.py:mcp --transport streamable-http
fastmcp run mcp_server.py:mcp --transport streamable-http
fastmcp run mcp_server.py:mcp --transport sse
fastmcp dev 03_mcp_training/server.py
For dev Purposes you can also use MCP Inspector
fastmcp dev mcp_server.py

activate the environment->.venv\Scripts\activate
when a new library is installed we need to run pip freeze > requirements.txt
run MCP server
make sure -> set PYTHONPATH=C:\Episteck\AiFarm\aifarm
fastmcp run 03_mcp_training/server.py:mcp --transport streamable-http
For dev Purposes you can also use MCP Inspector
fastmcp dev dlm_mcp_server.py
to run the ract Agent:
Activate environment
.venv/Scripts/Activate or
C:\Episteck\AiFarm\aifarm/venv/Scripts/activate.bat
Set environment variables
set PYTHONPATH=C:\Episteck\AiFarm\aifarm
set MCP_SERVER_URL=http://localhost:8050/mcp
run MCP server
fastmcp run mcp_server/dlm_mcp_server.py:mcp --transport streamable-http
For dev Purposes you can also use MCP Inspector
fastmcp dev mcp_server/dlm_mcp_server.py
OR SYMPLY RUN:
.venv\Scripts\Activate.ps1; $env:PYTHONPATH = "C:\Episteck\AiFarm\aifarm"; .venv\Scripts\fastmcp.exe run mcp_server/dlm_mcp_server.py:mcp --transport streamable-http
