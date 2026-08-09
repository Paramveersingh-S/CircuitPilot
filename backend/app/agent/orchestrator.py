class Planner:
    def __init__(self):
        pass
        
    async def decompose(self, user_text: str, context: str):
        # Stub implementation
        return []

class Orchestrator:
    def __init__(self):
        self.planner = Planner()
        
    async def handle_command(self, session, user_text: str):
        """
        Main dispatch loop.
        """
        plan = await self.planner.decompose(user_text, context=session.state_summary())
        for subtask in plan.subtasks:
            agent = session.AGENT_REGISTRY[subtask.agent]
            # broadcast(session, ChatEvent(role="assistant", text=agent.narrate_intent(subtask)))
            if subtask.is_destructive:
                approved = await session.request_approval(subtask)
                if not approved:
                    continue
            result = await agent.execute(subtask, tools=session.TOOL_REGISTRY[subtask.agent])
            session.log(subtask, result)
            # broadcast(session, FileChangedEvent(paths=result.changed_files))
            # broadcast(session, ChatEvent(role="assistant", text=agent.narrate_result(result)))
        
        # await verification_agent.run_checks(session)
