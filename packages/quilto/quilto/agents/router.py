"""Router agent for input classification and domain selection.

This module provides the RouterAgent class which classifies user input
as LOG/QUERY/BOTH/CORRECTION and selects relevant domains based on
input content matching against domain descriptions.
"""

from quilto.agents.models import RouterInput, RouterOutput
from quilto.llm import LLMClient


class RouterAgent:
    """Router agent for input classification and domain selection.

    Classifies raw user input as LOG/QUERY/BOTH/CORRECTION and
    selects relevant domains based on input content matching
    against domain descriptions.

    Attributes:
        llm_client: The LLM client for making inference calls.

    Example:
        >>> from quilto import LLMClient, load_llm_config
        >>> from quilto.agents import RouterAgent, RouterInput, DomainInfo
        >>> config = load_llm_config(Path("llm-config.yaml"))
        >>> client = LLMClient(config)
        >>> router = RouterAgent(client)
        >>> input = RouterInput(
        ...     raw_input="Bench pressed 185x5 today",
        ...     available_domains=[DomainInfo(name="strength", description="...")]
        ... )
        >>> output = await router.classify(input)
    """

    AGENT_NAME = "router"

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Router agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def build_prompt(self, router_input: RouterInput) -> str:
        """Build the system prompt with classification rules.

        Args:
            router_input: The RouterInput containing raw_input and domains.

        Returns:
            The formatted system prompt string.
        """
        domains_text = "\n".join(f"- {d.name}: {d.description}" for d in router_input.available_domains)
        if not domains_text:
            domains_text = "(No domains available)"

        session_context = router_input.session_context or "(No session context)"

        return f"""ROLE: You are an input classifier and domain selector for a personal logging system.

TASKS:
1. Classify the user's input type
2. Select relevant domain(s) for processing

=== CLASSIFICATION RULES ===

INPUT TYPES:
- LOG: Declarative statements recording activities, events, or observations
- QUERY: Questions seeking information, insights, or recommendations
- BOTH: Input that logs something AND asks a question
- CORRECTION: User fixing previously recorded information ("actually", "I meant", "that was wrong")

SIGNALS:
- Question words (why, how, what, when, which) → QUERY
- Question mark → QUERY
- Past tense declarative → LOG
- Correction language → CORRECTION

IMPORTANT:
- If input_type is BOTH, you MUST provide both log_portion and query_portion
- If input_type is CORRECTION, you MUST provide correction_target
- confidence should be >= 0.7 for clear classifications

=== DOMAIN SELECTION ===

Available domains:
{domains_text}

Select ALL domains that are relevant to the input. When uncertain, prefer broader selection.

=== INPUT ===
{router_input.raw_input}

Session context (recent messages):
{session_context}

=== OUTPUT (JSON) ===
Respond with a JSON object matching this schema:
- input_type: "LOG" | "QUERY" | "BOTH" | "CORRECTION"
- confidence: number between 0.0 and 1.0
- selected_domains: list of domain names
- domain_selection_reasoning: string explaining domain selection
- log_portion: string or null (required if BOTH)
- query_portion: string or null (required if BOTH)
- correction_target: string or null (required if CORRECTION)
- reasoning: string explaining classification"""

    async def classify(self, router_input: RouterInput) -> RouterOutput:
        """Classify input and select domains.

        Args:
            router_input: RouterInput with raw_input, session_context, available_domains.

        Returns:
            RouterOutput with classification and domain selection.

        Raises:
            ValueError: If raw_input is empty or whitespace-only.
        """
        if not router_input.raw_input or not router_input.raw_input.strip():
            raise ValueError("raw_input cannot be empty or whitespace-only")

        system_prompt = self.build_prompt(router_input)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": router_input.raw_input},
        ]

        result = await self.llm_client.complete_structured(
            agent=self.AGENT_NAME,
            messages=messages,
            response_model=RouterOutput,
        )
        return result  # type: ignore[return-value]
