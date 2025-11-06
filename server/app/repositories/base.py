"""
Base repository with retry/backoff and parameterized query safety.
"""

import time
import logging
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable, Union
from contextlib import contextmanager
from functools import wraps

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)

T = TypeVar('T')

class PaginationParams:
    """Pagination parameters with validation."""
    def __init__(self, page: int = 1, page_size: int = 50, max_page_size: int = 1000):
        if page < 1:
            raise ValueError("Page must be >= 1")
        if page_size < 1 or page_size > max_page_size:
            raise ValueError(f"Page size must be between 1 and {max_page_size}")

        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size

class DateFilter:
    """Date filtering parameters."""
    def __init__(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_field: str = "created_at"
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.date_field = date_field

    def to_sql_condition(self) -> str:
        """Generate SQL WHERE condition for date filtering."""
        conditions = []
        if self.start_date:
            conditions.append(f"{self.date_field} >= :start_date")
        if self.end_date:
            conditions.append(f"{self.date_field} <= :end_date")
        return " AND ".join(conditions) if conditions else ""

    def to_params(self) -> Dict[str, Any]:
        """Generate parameter dictionary for date filtering."""
        params = {}
        if self.start_date:
            params["start_date"] = self.start_date
        if self.end_date:
            params["end_date"] = self.end_date
        return params

class RetryConfig:
    """Retry configuration with exponential backoff."""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 0.1,
        max_delay: float = 5.0,
        backoff_factor: float = 2.0,
        retryable_exceptions: tuple = (OperationalError,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retryable_exceptions = retryable_exceptions

def retry_with_backoff(config: RetryConfig = None):
    """Decorator for retrying operations with exponential backoff."""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = config.base_delay

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        logger.warning(
                            f"Operation failed (attempt {attempt + 1}/{config.max_attempts}): {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * config.backoff_factor, config.max_delay)
                    else:
                        logger.error(f"Operation failed after {config.max_attempts} attempts: {e}")
                        raise last_exception
                except Exception as e:
                    # Don't retry non-retryable exceptions
                    logger.error(f"Non-retryable error: {e}")
                    raise e

        return wrapper
    return decorator

class BaseRepository(Generic[T]):
    """Base repository with parameterized queries and retry logic."""

    def __init__(self, session: Session, retry_config: RetryConfig = None):
        self.session = session
        self.retry_config = retry_config or RetryConfig()

    @contextmanager
    def _safe_query_context(self):
        """Context manager for safe query execution with rollback on error."""
        try:
            yield
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.session.rollback()
            raise

    def _execute_parameterized_query(
        self,
        query: str,
        params: Dict[str, Any] = None,
        fetch: str = "all"
    ) -> Union[List[Dict], Dict, int, None]:
        """
        Execute a parameterized query safely.

        Args:
            query: SQL query string with named parameters
            params: Dictionary of parameter values
            fetch: "all", "one", "scalar", or "none"

        Returns:
            Query results based on fetch mode
        """
        if params is None:
            params = {}

        # Log query for debugging (without sensitive data in production)
        logger.debug(f"Executing query: {query}")
        logger.debug(f"Parameters: {list(params.keys())}")

        with self._safe_query_context():
            result = self.session.execute(text(query), params)

            if fetch == "all":
                return [dict(row) for row in result.fetchall()]
            elif fetch == "one":
                row = result.fetchone()
                return dict(row) if row else None
            elif fetch == "scalar":
                return result.scalar()
            elif fetch == "none":
                return None
            else:
                raise ValueError(f"Invalid fetch mode: {fetch}")

    def _validate_sql_injection_safe(self, query: str, params: Dict[str, Any]) -> bool:
        """
        Validate that the query is safe from SQL injection.
        This is a basic validation - parameterized queries are the primary protection.
        """
        # Check that all parameters used in query are provided
        import re
        param_names = set(re.findall(r':([a-zA-Z_][a-zA-Z0-9_]*)', query))
        provided_params = set(params.keys())

        if param_names != provided_params:
            missing = param_names - provided_params
            extra = provided_params - param_names
            raise ValueError(
                f"Parameter mismatch. Missing: {missing}, Extra: {extra}"
            )

        # Check for dangerous patterns (basic validation)
        dangerous_patterns = [
            r';\s*--',  # Semicolon followed by comment
            r';\s*/\*',  # Semicolon followed by block comment
            r'union\s+select',  # Union-based injection
            r';\s*drop\s+',  # Drop statements
        ]

        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                raise ValueError(f"Potentially dangerous SQL pattern detected: {pattern}")

        return True

    @retry_with_backoff()
    def execute_query(
        self,
        query: str,
        params: Dict[str, Any] = None,
        fetch: str = "all",
        validate_safety: bool = True
    ) -> Union[List[Dict], Dict, int, None]:
        """Execute a query with retry logic and safety validation."""
        if validate_safety:
            self._validate_sql_injection_safe(query, params or {})

        return self._execute_parameterized_query(query, params, fetch)

    def apply_pagination(
        self,
        query: str,
        pagination: PaginationParams,
        params: Dict[str, Any] = None
    ) -> tuple[str, Dict[str, Any]]:
        """Apply pagination to a query."""
        if params is None:
            params = {}

        paginated_query = f"{query} LIMIT :limit OFFSET :offset"
        params.update({
            "limit": pagination.page_size,
            "offset": pagination.offset
        })

        return paginated_query, params

    def apply_date_filter(
        self,
        query: str,
        date_filter: DateFilter,
        params: Dict[str, Any] = None
    ) -> tuple[str, Dict[str, Any]]:
        """Apply date filtering to a query."""
        if params is None:
            params = {}

        condition = date_filter.to_sql_condition()
        if condition:
            # Check if WHERE already exists
            if "WHERE" in query.upper():
                query = f"{query} AND {condition}"
            else:
                query = f"{query} WHERE {condition}"

        params.update(date_filter.to_params())
        return query, params

    def get_count(self, table: str, conditions: str = "", params: Dict[str, Any] = None) -> int:
        """Get count of records in a table with optional conditions."""
        query = f"SELECT COUNT(*) FROM {table}"
        if conditions:
            query += f" WHERE {conditions}"

        result = self.execute_query(query, params, fetch="scalar")
        return result or 0
