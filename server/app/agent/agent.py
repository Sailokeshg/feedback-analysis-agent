"""
LangChain agent for feedback analysis with grounding and guardrails.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .tools import AnalyticsSQLTool, VectorExamplesTool, ReportWriterTool

logger = logging.getLogger(__name__)


class FeedbackAnalysisAgent:
    """LangChain agent for analyzing customer feedback with grounding and guardrails."""

    SYSTEM_PROMPT = """Ground answers in DB; always cite feedback_ids when quoting.

You are an AI assistant specialized in analyzing customer feedback data. You have access to three tools:

1. analytics_sql: Execute read-only, parameterized SQL queries against the feedback database
2. vector_examples: Retrieve exemplar feedback comments filtered by topic and sentiment
3. report_writer: Write structured weekly summary reports

IMPORTANT RULES:
- Always ground your answers in data from the database using the available tools
- When quoting specific feedback comments, ALWAYS cite the feedback_id
- Never hallucinate data, tables, or statistics that don't exist in the database
- Use the analytics_sql tool for aggregate queries and trends
- Use the vector_examples tool to get representative examples of feedback
- Use the report_writer tool to create structured weekly summaries
- Be precise and factual in your responses
- If you need data, use the appropriate tool rather than making assumptions

When providing examples or quotes from feedback:
- Always include the feedback_id in your citation
- Example: "As one customer stated (feedback_id: 123e4567-e89b-12d3-a456-426614174000): 'The service was excellent...'"

For analytics and trends:
- Use parameterized SQL queries to get accurate data
- Prefer aggregated data over individual records when analyzing patterns
- Always validate your understanding by checking the actual data"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the feedback analysis agent."""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        # Initialize tools
        self.tools = [
            AnalyticsSQLTool(),
            VectorExamplesTool(),
            ReportWriterTool()
        ]

        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",  # Use latest model for best performance
            temperature=0.1,  # Low temperature for consistent, factual responses
            openai_api_key=self.openai_api_key
        )

        # Initialize memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10  # Keep last 10 messages for context
        )

        # Create the agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,  # Limit iterations to prevent runaway execution
            early_stopping_method="force"  # Stop after max iterations
        )

    def _create_agent(self):
        """Create the OpenAI tools agent with system prompt."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        return create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

    def analyze_feedback(self, query: str) -> Dict[str, Any]:
        """
        Analyze customer feedback using the LangChain agent.

        Args:
            query: The user's query about feedback data

        Returns:
            Dictionary with analysis results and metadata
        """
        try:
            logger.info(f"Processing feedback analysis query: {query}")

            # Execute the agent
            result = self.agent_executor.invoke({"input": query})

            # Extract the final answer and any tool usage
            final_answer = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])

            # Log tool usage for monitoring
            tool_usage = []
            for step in intermediate_steps:
                action, observation = step
                tool_usage.append({
                    "tool": action.tool,
                    "input": action.tool_input,
                    "output_preview": str(observation)[:200] + "..." if len(str(observation)) > 200 else str(observation)
                })

            logger.info(f"Agent completed analysis. Tool usage: {len(tool_usage)} steps")

            return {
                "query": query,
                "answer": final_answer,
                "tool_usage": tool_usage,
                "success": True,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            logger.error(f"Error in feedback analysis: {e}")
            return {
                "query": query,
                "answer": f"I encountered an error while analyzing your query: {str(e)}. Please try rephrasing your question.",
                "tool_usage": [],
                "success": False,
                "error": str(e),
                "timestamp": self._get_timestamp()
            }

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history."""
        try:
            messages = self.memory.chat_memory.messages
            history = []

            for msg in messages:
                if isinstance(msg, HumanMessage):
                    history.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    history.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, SystemMessage):
                    history.append({"role": "system", "content": msg.content})

            return history

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []

    def clear_memory(self):
        """Clear the conversation memory."""
        self.memory.clear()
        logger.info("Conversation memory cleared")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def validate_response_grounding(self, response: str) -> Dict[str, Any]:
        """
        Validate that the response is properly grounded in database facts.

        This is a basic validation - in production, you might want more sophisticated
        checking to ensure no hallucinated data is present.

        Args:
            response: The agent's response to validate

        Returns:
            Validation results
        """
        validation = {
            "is_grounded": False,
            "issues": [],
            "citations_found": [],
            "recommendations": []
        }

        # Check for feedback_id citations when quoting
        import re
        feedback_id_pattern = r'feedback_id[:\s]+([a-f0-9\-]{36})'
        citations = re.findall(feedback_id_pattern, response, re.IGNORECASE)
        validation["citations_found"] = citations

        # Basic checks for grounded responses
        issues = []

        # Check if response mentions data without citations
        quote_indicators = ['"', "'", "customer said", "customer stated", "feedback shows"]
        has_quotes = any(indicator in response.lower() for indicator in quote_indicators)

        if has_quotes and not citations:
            issues.append("Response contains quotes but no feedback_id citations")

        # Check for potential hallucinated statistics
        stat_patterns = [
            r'\d+(?:\.\d+)?%',  # percentages
            r'\d+ feedback',     # feedback counts without context
            r'trend shows?',     # trend statements
        ]

        has_stats = any(re.search(pattern, response, re.IGNORECASE) for pattern in stat_patterns)

        if has_stats and "analytics_sql" not in str(self.memory.chat_memory.messages[-1:]):
            issues.append("Response contains statistics that may not be verified")

        validation["issues"] = issues
        validation["is_grounded"] = len(issues) == 0

        if issues:
            validation["recommendations"] = [
                "Always use tools to verify data before stating facts",
                "Cite feedback_ids when quoting specific comments",
                "Use analytics_sql tool for statistics and trends"
            ]

        return validation
