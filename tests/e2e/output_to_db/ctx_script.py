from ctx_agent_context import AgentContext
from ctx_job_context import JobContext

async def ctx_script(job_ctx: JobContext, agent_ctx: AgentContext):
      agent_ctx.output_manager.send({"test":"test"})
