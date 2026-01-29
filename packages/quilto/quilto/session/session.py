"""Session class for managing conversation turns.

This module provides the Session class which wraps SessionData and
handles turn management including automatic pruning and persistence.
"""

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

from quilto.models import ClarificationQuestion, ProcessResult
from quilto.session.models import ConversationTurn, SessionConfig, SessionData

if TYPE_CHECKING:
    from quilto.quilto import Quilto
    from quilto.session.stores.base import SessionStore


class Session:
    """Manages a single conversation session.

    Wraps SessionData and provides methods for adding turns,
    automatic pruning when max turns is exceeded, and auto-saving
    to the backing store.

    The session also provides the process() method for running input
    through the Quilto orchestration pipeline.

    Attributes:
        data: The underlying SessionData.
        store: The SessionStore for persistence.
        config: Session configuration (max turns, etc.).

    Example:
        session = Session(data, store, config)
        session.add_turn("user", "Hello!")
        session.add_turn("agent", "Hi there!")
        history = session.get_history()

        # Using process() with Quilto orchestration
        result = await session.process("How was my workout?")
    """

    def __init__(
        self,
        data: SessionData,
        store: "SessionStore",
        config: SessionConfig,
    ) -> None:
        """Initialize session with data, store, and config.

        Args:
            data: The session data to manage.
            store: The backing store for persistence.
            config: Session configuration.
        """
        self._data = data
        self._store = store
        self._config = config
        self._quilto: Quilto | None = None

    def _set_quilto(self, quilto: "Quilto") -> None:
        """Set the Quilto reference for orchestration.

        This is called by Quilto.create_session() to enable the
        process() method.

        Args:
            quilto: The Quilto instance to use for processing.
        """
        self._quilto = quilto

    @property
    def session_id(self) -> str:
        """Return the session ID."""
        return self._data.session_id

    def add_turn(
        self,
        role: Literal["user", "agent"],
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a conversation turn.

        Creates a new ConversationTurn, enforces the max turns limit
        via pruning, updates the session timestamp, and auto-saves.

        Pruning strategy: When conversation exceeds max_conversation_turns,
        keeps [first_turn] + last (max_turns - 1) turns. This preserves
        the initial context while removing older middle turns.

        Args:
            role: Who produced this turn ("user" or "agent").
            content: The text content of the turn.
            metadata: Optional additional data (e.g., clarification questions).

        Raises:
            ValueError: If content is empty (enforced by ConversationTurn model).
        """
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now(UTC),
            metadata=metadata,
        )
        self._data.conversation.append(turn)

        # Prune if over limit: keep first turn + last (max - 1) turns
        max_turns = self._config.max_conversation_turns
        if len(self._data.conversation) > max_turns:
            first_turn = self._data.conversation[0]
            recent_turns = self._data.conversation[-(max_turns - 1) :]
            self._data.conversation = [first_turn] + recent_turns

        # Update timestamp and save
        self._data.updated_at = datetime.now(UTC)
        self._store.save(self._data)

    def get_history(self) -> list[ConversationTurn]:
        """Return the conversation history.

        Returns a copy of the conversation list to prevent external mutation
        that would bypass turn management (pruning, timestamps, auto-save).

        Returns:
            List of ConversationTurn objects in chronological order.
        """
        return list(self._data.conversation)

    def _build_conversation_context(self) -> str | None:
        """Build conversation context string from history.

        When history exceeds context_turns, uses first turn + last
        (context_turns - 1) turns to preserve original intent while
        including recent context. When history is within context_turns,
        all turns are included.

        Returns:
            Formatted context string, or None if no history.
        """
        history = self.get_history()
        if not history:
            return None

        context_turns = self._config.context_turns

        if len(history) <= context_turns:
            selected = history
        else:
            # First turn + last (N-1) turns - same strategy as storage pruning
            first_turn = history[0]
            recent_turns = history[-(context_turns - 1) :]
            selected = [first_turn] + recent_turns

        lines = [f"{turn.role}: {turn.content}" for turn in selected]
        return "\n".join(lines)

    async def process(
        self,
        text: str,
        mode: Literal["auto", "log", "query"] | None = None,
    ) -> ProcessResult:
        """Process user input through the Quilto orchestration pipeline.

        Routes input through agents based on Router classification or
        forced mode. Adds user turn before processing and agent turn
        after processing.

        For QUERY inputs:
            - Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator
            - Retry loop on INSUFFICIENT verdict
            - Observer triggers on completion

        For LOG inputs:
            - Router → Parser → Observer

        For BOTH inputs:
            - Query flow first, then Parser

        For CORRECTION inputs:
            - Router → Correction flow with upsert semantics

        Args:
            text: The user input text to process.
            mode: Force input type classification. "auto" uses Router
                classification (default). "log" bypasses Router and
                treats as LOG. "query" bypasses Router and treats as QUERY.

        Returns:
            ProcessResult with response, parsed_data, or clarification_questions
            depending on the flow that executed.

        Raises:
            RuntimeError: If session not connected to Quilto instance.
        """
        if self._quilto is None:
            raise RuntimeError(
                "Session not connected to Quilto. Use quilto.create_session() "
                "to create sessions with process() capability."
            )

        # Add user turn before processing
        self.add_turn("user", text)

        # Build conversation context from history (excluding the turn just added)
        conversation_context = self._build_conversation_context()

        # Get orchestration graph and run
        graph = self._quilto._get_graph()  # pyright: ignore[reportPrivateUsage]

        # Build initial state
        initial_state = {
            "user_input": text,
            "mode": mode or "auto",
            "conversation_context": conversation_context,
            "max_retries": self._quilto.max_retries,
            "retry_count": 0,
            "is_partial": False,
            "error": None,
            "traces": [],
        }

        # Run the graph with timing
        start_time = time.perf_counter()
        final_state = await graph.ainvoke(initial_state)
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000
        final_state["total_elapsed_ms"] = total_elapsed_ms

        # Build ProcessResult from final state
        result = self._build_process_result(final_state)

        # Add agent turn with response
        agent_content = result.response or ""
        if result.clarification_questions:
            # Format clarification questions for conversation
            questions_text = "\n".join(f"- {q.question}" for q in result.clarification_questions)
            agent_content = f"I need some clarification:\n{questions_text}"

        if agent_content:
            metadata: dict[str, Any] | None = None
            if result.clarification_questions:
                metadata = {"clarification_questions": [q.model_dump() for q in result.clarification_questions]}
            self.add_turn("agent", agent_content, metadata)

        return result

    def _build_process_result(self, state: dict[str, Any]) -> ProcessResult:
        """Build ProcessResult from orchestration final state.

        Args:
            state: Final state dict from orchestration graph.

        Returns:
            ProcessResult populated from state fields.
        """
        from quilto.models import AgentTrace, ProcessDebug

        # Map state to ProcessResult fields
        input_type = state.get("input_type", "query")
        response = state.get("response")
        confidence = state.get("confidence")
        source_entry_ids = state.get("source_entry_ids", [])
        parsed_data = state.get("parsed_data")
        selected_domains = state.get("selected_domains", [])
        correction_result = state.get("correction_result")

        # Handle clarification questions - supports both dict and string formats
        # PlannerOutput.clarify_questions is list[str] | None, but session may have dicts
        clarify_questions_raw = state.get("clarify_questions")
        clarification_questions: list[ClarificationQuestion] | None = None
        if clarify_questions_raw:
            result_questions: list[ClarificationQuestion] = []
            for q in clarify_questions_raw:  # q: str | dict[str, Any]
                if isinstance(q, dict) and q.get("question"):
                    result_questions.append(
                        ClarificationQuestion(
                            question=q.get("question", ""),
                            options=q.get("options"),
                        )
                    )
                elif isinstance(q, str) and q.strip():
                    result_questions.append(ClarificationQuestion(question=q, options=None))
            clarification_questions = result_questions if result_questions else None

        # Build debug info if enabled
        debug: ProcessDebug | None = None
        if self._quilto and self._quilto.debug:
            traces_raw = state.get("traces", [])
            traces = [
                AgentTrace(
                    agent_name=t.get("agent_name", "unknown"),
                    input_summary=t.get("input_summary", ""),
                    output_summary=t.get("output_summary", ""),
                    elapsed_ms=t.get("elapsed_ms", 0.0),
                    timestamp=t.get("timestamp", datetime.now(UTC)),
                )
                for t in traces_raw
            ]
            debug = ProcessDebug(
                traces=traces,
                total_elapsed_ms=state.get("total_elapsed_ms", 0.0),
                retry_count=state.get("retry_count", 0),
            )

        return ProcessResult(
            response=response,
            confidence=confidence,
            source_entry_ids=source_entry_ids,
            parsed_data=parsed_data,
            correction_result=correction_result,
            input_type=input_type,
            selected_domains=selected_domains,
            clarification_questions=clarification_questions,
            debug=debug,
        )
