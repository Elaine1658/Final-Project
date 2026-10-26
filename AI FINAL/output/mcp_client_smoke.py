import asyncio, json, subprocess
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'mcp_smoke.json'

async def main():
    params = StdioServerParameters(command='python3', args=['-m', 'mcp_server.server'], cwd=str(ROOT))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            calls = [('sales_history', {'meal': 'Grilled chicken bowl'}), ('inventory_snapshot', {}), ('campus_context', {})]
            results = []
            for name, args in calls:
                result = await session.call_tool(name, args)
                results.append({'tool': name, 'ok': not result.isError, 'preview': getattr(result.content[0], 'text', '')[:250]})
    OUT.write_text(json.dumps({'discovered_tools': names, 'calls': results}, indent=2))
    print(OUT)

if __name__ == '__main__': asyncio.run(main())
