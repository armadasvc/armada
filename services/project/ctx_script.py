from ctx_agent_context import AgentContext
from ctx_job_context import JobContext

async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):
  
    
    try:
      page = await agent_ctx.browser.get("https://example.com")
      job_ctx.monitoring_client.record_success_event("page reached")
      h1_content = await page.select("h1")
      element = h1_content.text
      job_ctx.monitoring_client.record_finalsuccess_event(element)

    except BaseException as e:
       job_ctx.monitoring_client.record_failed_event(str(e))