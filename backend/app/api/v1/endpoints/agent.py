# backend/app/api/v1/endpoints/agent.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.agent import AgentTask, TaskStatus
from app.agent.graph import build_agent

router = APIRouter()

class AgentRequest(BaseModel):
    prompt: str

@router.post("/execute")
def execute_agent_task(
    payload: AgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Takes a natural language prompt, creates a Task record, 
    and executes the LangGraph agent to fulfill the request.
    """
    # 1. Log the incoming task to the database (Audit Trail)
    task = AgentTask(
        user_id=current_user.id,
        prompt=payload.prompt,
        status=TaskStatus.IN_PROGRESS
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        # 2. Build the agent and initialize the state
        agent = build_agent()
        initial_state = {
            "messages": [HumanMessage(content=payload.prompt)],
            "user_id": str(current_user.id) # The AI needs this!
        }

        # 3. Execute the graph (This might take 5-10 seconds for complex tasks)
        final_state = agent.invoke(initial_state)

        # 4. Extract the final answer
        final_ai_message = final_state["messages"][-1].content

        # 5. Update task status
        task.status = TaskStatus.COMPLETED
        db.commit()

        return {
            "task_id": task.id,
            "agent_response": final_ai_message
        }

    except Exception as e:
        task.status = TaskStatus.FAILED
        db.commit()
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")