from ctx_agent_context import AgentContext
from ctx_job_context import JobContext

async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):
    try:
      page = await agent_ctx.browser.get("http://host.minikube.internal:5010")
      job_ctx.monitoring_client.record_success_event("page reached")
      await agent_ctx.browser.cookies.set_all([                            
        {"name": "account", "value": job_ctx.job_message["account"], "url": "http://host.minikube.internal:5010"}
    ])
      job_ctx.monitoring_client.record_success_event("cookie setup")
      await page.xsend_native(["#composeInput",0],[5,0],job_ctx.job_message["message"])
      job_ctx.monitoring_client.record_success_event("message written")
      await page.xclick_native(["#btnTweet",0],[0,3])
      job_ctx.monitoring_client.record_finalsuccess_event("message_sent")
      
    except BaseException as e:
       job_ctx.monitoring_client.record_failed_event(str(e))
   
  
    

