import asyncio
from ctx_agent_context import AgentContext
from ctx_job_context import JobContext
import time



async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):
    print("####")
    print(agent_ctx.agent_message["run_id"])
    print("####")

    #fingerprint
    fingerprint = agent_ctx.fingerprint_manager.get_fingerprint({"desired_ua":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"})
    print(fingerprint)

    #database
    database_entry = agent_ctx.database.select_from_db("SELECT TOP 1 (uuid) FROM dim_email ORDER BY NEWID()")
    print(database_entry)

    #proxy
    # tab = await agent_ctx.browser.get("https://api.ipify.org")
    # element = await tab.select("pre")  
    # print(element)
    # tab = await agent_ctx.browser.get("https://google.com",)
    # print("round 2")
    # tab = await agent_ctx.browser.get("https://api.ipify.org")
    # element = await tab.select("pre")  
    # print(element)


