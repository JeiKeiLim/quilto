"""Quilto main entry point for agent orchestration.

This module provides the Quilto class, the primary interface for
applications to interact with the Quilto agent framework.
"""

from typing import TYPE_CHECKING, Any

from quilto.domain import DomainModule
from quilto.domain_selector import DomainSelector
from quilto.handlers import ProgressHandler
from quilto.llm import LLMClient
from quilto.observability.noop import NoOpProvider
from quilto.observability.provider import ObservabilityProvider
from quilto.session import Session, SessionManager
from quilto.session.stores import SQLiteSessionStore
from quilto.state import ObserverTriggerConfig
from quilto.storage import StorageRepository

if TYPE_CHECKING:
    from quilto.config import QuiltoConfig
    from quilto.orchestration import OrchestrationGraph


class Quilto:
    """Main entry point for the Quilto agent framework.

    Quilto orchestrates all agents via LangGraph, providing a single
    interface for applications. New agents added to Quilto automatically
    propagate to all applications using the framework.

    Attributes:
        llm_client: The LLM client for agent calls.
        storage: The storage repository for entries.
        domains: List of domain modules.
        observer_config: Observer trigger configuration.
        max_retries: Maximum retry attempts for Evaluator failures.
        debug: Enable debug mode with traces.
        progress_handler: Optional progress callbacks.
        observability_provider: Provider for LLM and agent tracing.

    Example:
        >>> from quilto import Quilto, LLMClient, StorageRepository
        >>> from my_app.domains import FitnessDomain
        >>>
        >>> llm_client = LLMClient(config_path="./llm.yaml")
        >>> storage = StorageRepository(base_path="./logs")
        >>>
        >>> q = Quilto(
        ...     llm_client=llm_client,
        ...     storage=storage,
        ...     domains=[FitnessDomain()],
        ...     progress_handler=MyUIHandler(),  # Optional
        ...     debug=False,
        ... )
        >>>
        >>> session = q.create_session()
        >>> result = await session.process("How was my workout last week?")

    With observability (auto-configured from config):
        >>> from quilto import Quilto, load_config
        >>> config = load_config(Path("config.yaml"))
        >>> q = Quilto(
        ...     llm_client=LLMClient(config.llm),
        ...     storage=storage,
        ...     domains=domains,
        ...     config=config,  # Observability auto-configured
        ... )
    """

    def __init__(
        self,
        llm_client: LLMClient,
        storage: StorageRepository,
        domains: list[DomainModule],
        observer_config: ObserverTriggerConfig | None = None,
        max_retries: int = 2,
        debug: bool = False,
        progress_handler: ProgressHandler | None = None,
        session_db_path: str = "quilto_sessions.db",
        config: "QuiltoConfig | None" = None,
        observability: ObservabilityProvider | None = None,
    ) -> None:
        """Initialize Quilto with required components.

        Args:
            llm_client: LLM client for all agent calls.
            storage: Storage repository for entry retrieval and saving.
            domains: List of domain modules for domain-specific processing.
            observer_config: Observer trigger configuration. Defaults to
                ObserverTriggerConfig() with post_query=True.
            max_retries: Maximum retry attempts when Evaluator returns
                INSUFFICIENT. Defaults to 2.
            debug: Enable debug mode to include traces in ProcessResult.
                Defaults to False.
            progress_handler: Optional handler for progress callbacks
                (on_agent_start, on_agent_complete, on_retry, on_stage).
            session_db_path: Path to SQLite database for session persistence.
                Defaults to "quilto_sessions.db". Use ":memory:" for testing.
            config: Optional unified Quilto configuration. If provided with
                observability enabled, creates provider from config.
            observability: Optional explicit observability provider. Takes
                precedence over config-based provider creation.
        """
        self.llm_client = llm_client
        self.storage = storage
        self.domains = domains
        self.observer_config = observer_config or ObserverTriggerConfig()
        self.max_retries = max_retries
        self.debug = debug
        self.progress_handler = progress_handler

        # Initialize observability provider (AC#1, AC#2, AC#3, AC#7)
        if observability is not None:
            # Explicit provider override (AC#1)
            self.observability_provider: ObservabilityProvider = observability
        elif config is not None:
            # Create from config (AC#2)
            from quilto.config import create_observability_provider

            self.observability_provider = create_observability_provider(config.observability)
        else:
            # Default to NoOpProvider (AC#3, AC#7 backward compatibility)
            self.observability_provider = NoOpProvider()

        # Initialize domain selector
        self._domain_selector = DomainSelector(domains)

        # Initialize session management
        self._session_store = SQLiteSessionStore(session_db_path)
        self._session_manager = SessionManager(self._session_store)

        # Lazy-loaded orchestration graph
        self._graph: OrchestrationGraph | None = None

    @property
    def domain_selector(self) -> DomainSelector:
        """Return the domain selector."""
        return self._domain_selector

    def _get_graph(self) -> "OrchestrationGraph":
        """Get or create the orchestration graph.

        Returns:
            The compiled LangGraph for agent orchestration.
        """
        if self._graph is None:
            from quilto.orchestration import create_orchestration_graph

            self._graph = create_orchestration_graph(self)
        return self._graph

    def _get_storage_summary(self) -> dict[str, Any]:
        """Get storage summary for Planner agent.

        Returns:
            Storage summary as dict from storage.get_storage_summary().
        """
        return self.storage.get_storage_summary().model_dump()

    def get_storage_summary(self) -> dict[str, Any]:
        """Get storage summary for agent planning.

        Returns:
            Summary of storage contents for date range decisions.
        """
        return self._get_storage_summary()

    def flush(self) -> None:
        """Flush pending observability traces.

        Call before application shutdown to ensure all traces are sent
        to the observability backend. This is particularly important for
        Langfuse which batches trace submissions.

        Example:
            >>> q = Quilto(...)
            >>> session = q.create_session()
            >>> result = await session.process("...")
            >>> q.flush()  # Ensure traces are sent before shutdown
        """
        self.observability_provider.flush()

    def create_session(self) -> Session:
        """Create a new conversation session.

        Creates a Session with a reference back to this Quilto instance,
        enabling session.process() to use the orchestration graph.

        Returns:
            A new Session ready for processing.
        """
        # Create session through manager
        session = self._session_manager.create_session()

        # Set Quilto reference for process() method
        session._set_quilto(self)  # pyright: ignore[reportPrivateUsage]

        return session

    def get_session(self, session_id: str) -> Session | None:
        """Retrieve an existing session by ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            Session if found, None if session doesn't exist.
        """
        session = self._session_manager.get_session(session_id)
        if session is not None:
            session._set_quilto(self)  # pyright: ignore[reportPrivateUsage]
        return session
