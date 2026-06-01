from google.adk import Agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Literal
import os
import json
from dotenv import load_dotenv

load_dotenv()

class SubTask(BaseModel):
    task_id: int = Field(description="Sequential task ID, starting at 1")
    intent: Literal["INFORMATIONAL", "ACTIONABLE"] = Field(description="The category of the task")
    description: str = Field(description="The task description and objective, including any parameters")
    reasoning: str = Field(default="", description="Brief explanation of why this task was created")

class DecompositionResult(BaseModel):
    tasks: List[SubTask]
    summary: str

class QueryDecomposer(Agent):
    def __init__(self):
        super().__init__(
            name="QueryDecomposer",
            description="Splits complex user queries into a sequence of atomic sub-tasks.",
            instruction="Decompose user requests into logical steps for any digital interface or application."
        )
        self._llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def decompose(self, query: str):
        """
        Decomposes the into atomic tasks.
        Returns: (DecompositionResult, usage_dict)
        """
        structured_llm = self._llm.with_structured_output(DecompositionResult, include_raw=True, method="function_calling")

        prompt = ChatPromptTemplate.from_template("""
        You are a Universal AI Orchestration Specialist.
        Your goal is to break down a requester's multi-part instruction into a logical sequence of Atomic Tasks.

        ---
        CATEGORIES:
        1. INFORMATIONAL: Seeking knowledge, steps, or documentation context.
        2. ACTIONABLE: Requesting the execution of a concrete task or operation within a digital system.

        ---
        RULES:
        1. CONTEXTUAL INTEGRITY (CRITICAL): If a user mentions an action but asks for "steps", "how-to", or "explanation", treat the ENTIRE request as a single INFORMATIONAL task.
        2. MISSING INFORMATION INTENT (CRITICAL): If a user mentions an action AND asks "what information do you need", "what details are required", or asks how the system can assist them to do it, treat it as an ACTIONABLE task. 
        3. ACTION DESCRIPTION (CRITICAL): For ACTIONABLE tasks, the 'description' MUST be phrased as the final objective AND MUST append all provided parameters to the end (e.g., 'Execute task X with parameter Y: value Z'). This ensures subsequent document retrieval (RAG) finds the correct technical procedures while retaining the data.
        4. RETAIN PARAMETERS (CRITICAL): You MUST preserve any specific data, parameters, constraints, or identifiers (e.g., 'User id: dummy', emails, passwords) provided in the original request EXACTLY as they are given within the task's 'description'. DO NOT summarize them away as 'specified details'.
        5. MULTI-STEP OPERATIONS (CRITICAL): If the user requests multiple distinct operations (e.g., "Create a role AND assign a permission to it", "Create user X then assign role Y"), you MUST split them into SEPARATE, sequential ACTIONABLE tasks. Do NOT combine distinct entity operations into a single task.
        6. Neutral persona: Do not assume the system is a specific application.
        ---

        REQUST: {query}
        """)

        chain = prompt | structured_llm
        raw_result = await chain.ainvoke({"query": query})
        
        result = raw_result.get("parsed")
        
        # Capture usage stats (Mapping input_tokens -> prompt_tokens)
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        raw_msg = raw_result.get("raw")
        if raw_msg and hasattr(raw_msg, "usage_metadata") and raw_msg.usage_metadata:
            usage = {
                "prompt_tokens": raw_msg.usage_metadata.get("input_tokens", 0),
                "completion_tokens": raw_msg.usage_metadata.get("output_tokens", 0),
                "total_tokens": raw_msg.usage_metadata.get("total_tokens", 0)
            }
            
        return result, usage

# Singleton instance
decomposer = QueryDecomposer()
