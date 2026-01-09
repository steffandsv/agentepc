from browser_use.agent.views import AgentStepInfo
import dataclasses
print([f.name for f in dataclasses.fields(AgentStepInfo)])
