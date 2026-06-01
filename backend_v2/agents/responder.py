from google.adk import Agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

class Responder(Agent):
    def __init__(self):
        super().__init__(
            name="Responder",
            description="Informational answer generator using RAG.",
            instruction="Synthesize accurate answers from any provided documentation using a neutral, application-agnostic persona."
        )
        self._llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def answer_informational(self, query: str, context: str, history: list):
        """
        Answers informational queries strictly using RAG chunks.
        Neutral persona for multi-application support.
        Returns: (answer_str, usage_dict)
        """
        prompt = ChatPromptTemplate.from_template("""
        You are an AI Knowledge Synthesis Specialist.
        Your goal is to provide a COMPLETE and ACCURATE answer using ONLY the provided document context.

        ---
        STRICT RULES:
        1. NO HALLUCINATIONS (CRITICAL): If the user asks how to perform an operation and that specific operation is NOT explicitly described in the DOCUMENT CONTEXT, you MUST state:
           'I'm sorry, but the provided documentation does not contain information on [Operation Name].'
           
        2. SEMANTIC FLEXIBILITY: Administrative and technical terms should be treated with semantic overlap (e.g., 'map', 'tag', 'link', 'assign', 'provision') to ensure user queries match documentation phrased differently.

        3. SECRET SHIELD: NEVER disclose raw passwords or specific credentials. 
           - Use the exact string '[APP_ADMIN_USERNAME]' for any admin username.
           - Use the exact string '[APP_ADMIN_PASSWORD]' for any admin password.
        
        4. PRE-REQUISITES (CRITICAL REQUIREMENT): Your answer MUST begin from the very first step required to access the system based on the document. You must explicitly list opening the browser, navigating to the application URL, and logging in, before explaining the task-specific steps. Do NOT assume the user is already logged in.
        
        5. REQUIRED RESPONSE FORMAT: Always structure your procedural answers tightly as follows:
        **Prerequisites (System Access):**
        - [List steps: open browser, go to URL, enter username as [APP_ADMIN_USERNAME] and password as [APP_ADMIN_PASSWORD]]
        **Task Steps:**
        - [List the steps to perform the specific request...]
        
        6. RAG ONLY: Use ONLY the provided context. Do not use your internal knowledge of specific software products.
        ---

        DOCUMENT CONTEXT:
        {context}

        USER QUESTION:
        {query}

        CONVERSATION HISTORY:
        {history}
        """)

        chain = prompt | self._llm
        
        response = await chain.ainvoke({
            "context": context,
            "query": query,
            "history": history
        })
        
        # Capture usage stats (Mapping input_tokens -> prompt_tokens for Supervisor)
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.get("input_tokens", 0),
                "completion_tokens": response.usage_metadata.get("output_tokens", 0),
                "total_tokens": response.usage_metadata.get("total_tokens", 0)
            }
        
        return response.content, usage

# Singleton instance
responder = Responder()
