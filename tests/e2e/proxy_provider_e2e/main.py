"""
project main module - Celery worker for job execution.

This module is executed via exec() with the following variables injected:
- app: Celery application instance
- agent_message: dict with agent configuration from Redis

In distant mode: agent injects them via exec()
In local mode: workbench/run_local.py uses exec() with the same pattern
"""

from ctx_agent_context import AgentContext
from ctx_job_context import JobContext
import asyncio
from celery.signals import worker_process_init, worker_process_shutdown
from ctx_script import ctx_script

# Runtime state (initialized by init_worker)
event_loop = None
agent_ctx = None


@worker_process_init.connect
def init_worker(sender, **kwargs):
    """Initialize the worker process with an event loop and agent context."""
    global event_loop, agent_ctx
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    async def setup():
        global agent_ctx
        agent_ctx = await AgentContext(agent_message).__aenter__()

    event_loop.run_until_complete(setup())


@worker_process_shutdown.connect
def shutdown_worker(sender, **kwargs):
    """Clean up agent context when the worker process shuts down."""
    global event_loop, agent_ctx
    if agent_ctx and event_loop:
        event_loop.run_until_complete(agent_ctx.__aexit__(None, None, None))


@app.task(name='tasks.consume_message', acks_late=True, queue=agent_message["run_id"])
def run_job(job_message):
    """Execute a job received from the Celery queue."""
    global event_loop, agent_ctx
    event_loop.run_until_complete(process_message(job_message, agent_ctx))


async def process_message(job_message, agent_ctx: AgentContext):
    """Process a single job message within the agent context."""
    async with JobContext(job_message) as job_ctx:
        await ctx_script(job_ctx, agent_ctx)
