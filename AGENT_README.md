# LangChain Feedback Analysis Agent

A sophisticated LangChain agent designed for analyzing customer feedback with grounding, reproducibility, and guardrails against hallucinated data.

## Overview

This implementation provides a LangChain agent with three specialized tools for comprehensive feedback analysis:

1. **AnalyticsSQLTool** - Read-only parameterized SQL queries for analytics
2. **VectorExamplesTool** - Retrieval of exemplar comments by topic/sentiment
3. **ReportWriterTool** - Generation of structured weekly summary reports

## System Prompt

```
Ground answers in DB; always cite feedback_ids when quoting.

You are an AI assistant specialized in analyzing customer feedback data. You have access to three tools...

IMPORTANT RULES:
- Always ground your answers in data from the database using the available tools
- When quoting specific feedback comments, ALWAYS cite the feedback_id
- Never hallucinate data, tables, or statistics that don't exist in the database
- Use the analytics_sql tool for aggregate queries and trends
- Use the vector_examples tool to get representative examples of feedback
- Use the report_writer tool to create structured weekly summaries
- Be precise and factual in your responses
- If you need data, use the appropriate tool rather than making assumptions
```

## Architecture

### Tools

#### AnalyticsSQLTool
- **Purpose**: Execute read-only, parameterized SQL queries against the feedback database
- **Safety**: Only allows SELECT queries to prevent data modification
- **Available Tables**:
  - `feedback`: Core feedback data with text, metadata, timestamps
  - `nlp_annotation`: Sentiment analysis, topics, toxicity scores, embeddings
  - `topic`: Topic definitions with keywords and labels
  - `topic_audit_log`: Change tracking for topics

#### VectorExamplesTool
- **Purpose**: Retrieve exemplar feedback comments filtered by topic and/or sentiment
- **Parameters**:
  - `topic_id`: Optional topic filter
  - `sentiment`: Optional sentiment filter (-1, 0, 1)
  - `limit`: Maximum examples (default 5, max 10)
- **Output**: Structured feedback examples with proper citations

#### ReportWriterTool
- **Purpose**: Generate structured weekly summary reports
- **Parameters**:
  - `week_start_date`: Report period start
  - `total_feedback`: Feedback volume metrics
  - `negative_percentage`: Sentiment analysis
  - `top_topics`: Topic distribution
  - `key_insights`: Analysis findings

### Agent Features

#### Grounding & Guardrails
- **Citation Requirements**: All quoted feedback must include `feedback_id`
- **Data Verification**: All statistics and trends verified through database queries
- **Hallucination Prevention**: Validation logic checks for unsupported claims
- **Tool Usage Tracking**: All agent actions logged for auditability

#### Reproducibility
- **Deterministic Tools**: Same inputs produce consistent outputs
- **Parameter Validation**: Strict input validation prevents ambiguous queries
- **Structured Responses**: Consistent response format across queries

#### Conversation Management
- **Memory**: ConversationBufferWindowMemory with 10-message context
- **Clear Memory**: API endpoint to reset conversation state
- **History Access**: Retrieve conversation history with pagination

## API Integration

### Chat Endpoints

#### POST `/api/v1/chat/query`
Process natural language queries about feedback data.

**Request:**
```json
{
  "query": "What are the main topics in customer feedback?",
  "context_limit": 10
}
```

**Response:**
```json
{
  "query": "What are the main topics in customer feedback?",
  "answer": "Based on the feedback data, the top topics are...",
  "sources": [],
  "confidence": 0.9,
  "tool_usage": [
    {
      "tool": "analytics_sql",
      "input": {"query": "SELECT topic_id, COUNT(*) as count FROM nlp_annotation GROUP BY topic_id ORDER BY count DESC LIMIT 5"},
      "output_preview": "[{'topic_id': 1, 'count': 150}, ...]"
    }
  ],
  "success": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET `/api/v1/chat/conversations`
Retrieve conversation history.

#### POST `/api/v1/chat/clear-memory`
Clear the agent's conversation memory.

#### GET `/api/v1/chat/suggestions`
Get suggested queries based on available data.

## Installation & Setup

### Dependencies
```toml
langchain==0.1.5
langchain-community==0.0.13
langchain-openai==0.0.5
```

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Initialization
```python
from app.agent import FeedbackAnalysisAgent

agent = FeedbackAnalysisAgent(openai_api_key="your-key")
result = agent.analyze_feedback("What are the main customer complaints?")
```

## Testing

Run comprehensive tests to verify implementation:

```bash
cd /path/to/feedback-analysis-agent
python3 test_agent.py
```

Tests cover:
- ✅ Agent structure and initialization
- ✅ Tool definitions and naming
- ✅ Guardrails against hallucinated data
- ✅ System prompt and grounding requirements
- ✅ Response validation logic

## Example Usage

### Query: "Show me examples of negative feedback about product quality"

**Agent Process:**
1. Uses `analytics_sql` to find topic_id for "product quality"
2. Uses `vector_examples` to retrieve negative examples for that topic
3. Returns properly cited feedback examples

**Response:**
```
Based on the feedback data, here are examples of negative comments about product quality:

As one customer stated (feedback_id: 123e4567-e89b-12d3-a456-426614174000): "The product quality is terrible, it broke after one week."

Another customer reported (feedback_id: 987fcdeb-51a2-43d0-8f12-345678901234): "Poor quality control, the item arrived damaged."
```

### Query: "Generate a weekly summary report"

**Agent Process:**
1. Uses `analytics_sql` to gather metrics for the specified week
2. Uses `vector_examples` to identify key insights
3. Uses `report_writer` to format structured output

## Guardrails Validation

The agent includes validation logic to ensure responses are properly grounded:

### ✅ Properly Grounded
- Statistics verified through database queries
- Feedback quotes include `feedback_id` citations
- Claims supported by tool outputs

### ❌ Hallucinated Content
- Unverified percentages or counts
- Quotes without proper citations
- References to non-existent tables or fields

## Performance Considerations

- **Batch Processing**: Tools support efficient batch operations
- **Query Optimization**: Analytics queries use appropriate indexes
- **Memory Management**: Conversation memory limited to recent context
- **Rate Limiting**: Tool usage controlled to prevent abuse
- **Caching**: Results cached where appropriate

## Future Enhancements

- **Multi-modal Analysis**: Support for analyzing feedback with images/audio
- **Advanced Filtering**: Time-based, customer segment, and source filtering
- **Automated Reporting**: Scheduled report generation
- **Feedback Classification**: Automated categorization improvements
- **Sentiment Drift Detection**: Advanced trend analysis

## Security & Compliance

- **Read-Only Operations**: All database access is read-only
- **Parameterized Queries**: SQL injection prevention
- **Input Validation**: Strict parameter validation
- **Audit Logging**: All tool usage tracked
- **Data Privacy**: No sensitive data exposure in responses

---

**Note**: This implementation ensures reproducible, grounded responses by requiring all claims to be backed by database-verified data and proper citation of feedback sources.
