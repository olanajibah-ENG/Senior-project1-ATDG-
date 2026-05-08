"""
agents.py — Documentation Generation Agents
Improved with: Chain-of-Thought prompts, Anti-Hallucination rules,
Few-Shot Examples, LangGraph-style node support.

Uses LangChain BaseTool and ChatPromptTemplate when available.
Falls back to a lightweight AgentTool ABC that mirrors the same interface
so the app runs even if langchain is not installed.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from .llm_client import LLMClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LangChain imports (optional — graceful fallback if not installed)
# ---------------------------------------------------------------------------
try:
    from langchain.tools import BaseTool as _LCBaseTool          # noqa: F401
    from langchain_core.prompts import ChatPromptTemplate         # noqa: F401
    _LANGCHAIN_AVAILABLE = True
    logger.info("[agents] LangChain imports OK")
except Exception:
    _LCBaseTool = None
    ChatPromptTemplate = None
    _LANGCHAIN_AVAILABLE = False
    logger.warning("[agents] LangChain not available — using AgentTool fallback")


# ---------------------------------------------------------------------------
# Lightweight BaseTool replacement (mirrors LangChain BaseTool interface)
# ---------------------------------------------------------------------------

class AgentTool(ABC):
    """
    Minimal tool base class that mirrors the LangChain BaseTool interface.
    Provides .run() → calls ._run(), and stores name/description.
    Drop-in compatible: swap AgentTool for BaseTool when langchain is available.
    """
    name: str = ""
    description: str = ""

    @abstractmethod
    def _run(self, *args, **kwargs) -> str:
        ...

    def run(self, *args, **kwargs) -> str:
        return self._run(*args, **kwargs)


# ---------------------------------------------------------------------------
# Pydantic Input Schemas
# ---------------------------------------------------------------------------

class SingleFileInput(BaseModel):
    code_content: str = Field(..., description="Raw source code of the file")
    class_name: Optional[str] = Field(None, description="Primary class name if known")
    analysis_summary: Optional[str] = Field(None, description="Pre-computed analysis summary")
    file_name: Optional[str] = Field(None, description="File name for labelling")


class LowLevelInput(BaseModel):
    code_content: str = Field(..., description="Raw source code")
    detailed_analysis: Optional[str] = Field(None, description="Pre-computed detailed analysis context")


class VerifierInput(BaseModel):
    code: str = Field(..., description="Original source code")
    explanation: str = Field(..., description="Generated explanation to verify")
    force_verification: bool = Field(False, description="Skip size guard and always verify")


# ---------------------------------------------------------------------------
# DocumentationState  (shared LangGraph state — pydantic v1 compatible)
# ---------------------------------------------------------------------------

class DocumentationState(BaseModel):
    """Shared state passed between LangGraph nodes."""
    model_config = {"frozen": False}  # pydantic v2: allow field mutation

    code_content: str = ""
    detailed_analysis: Optional[str] = None
    analysis_summary: Optional[str] = None
    class_name: Optional[str] = None
    file_name: Optional[str] = None
    exp_type: str = "high_level"
    is_project: bool = False
    raw_output: Optional[str] = None
    verified_output: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# BaseAgent
# ---------------------------------------------------------------------------

class BaseAgent:
    """Thin wrapper around LLMClient — keeps backward-compat .ask_ai() interface."""

    def ask_ai(self, system_prompt: str, user_prompt: str) -> str:
        return LLMClient.call_model(system_prompt, user_prompt)


# ---------------------------------------------------------------------------
# HighLevelAgent
# ---------------------------------------------------------------------------

_HIGH_LEVEL_SYSTEM = """\
## ROLE
You are a Senior Software Architect writing clear, non-technical documentation \
for business stakeholders and junior developers.

## TASK
Produce a HIGH-LEVEL explanation of the provided source code.
Focus on WHAT the code does and WHY it exists — NOT on implementation details.

## RULES
1. Think step by step before writing. Reason about the code's purpose first.
2. NEVER invent classes, methods, or behaviours that are not present in the code.
3. If something is unclear, say "Not determinable from source" — do NOT guess.
4. Use plain English. Avoid jargon.
5. Follow the OUTPUT FORMAT below exactly — do not add or remove any section.

## ANTI-HALLUCINATION CONSTRAINTS
- Only describe what you can directly observe in the provided source code.
- Do NOT assume external behaviour unless it is explicitly imported or called.
- If a class has no methods, write "No public methods defined."

## OUTPUT FORMAT (copy this structure exactly)
---
## Executive Summary
[2-3 sentences describing what the code does overall]

## Purpose & Responsibility
Purpose: [what the code aims to achieve]
Responsibility: [what it manages]
- [key responsibility 1]
- [key responsibility 2]
- [key responsibility 3]

## Key Capabilities
- [capability 1]
- [capability 2]
- [capability 3]

---
[Repeat the block below for EACH class found:]

## Class: [ClassName]
Purpose:
[One paragraph describing what this class represents]

### Constructor: __init__(self, param1: type, param2: type)
Logic Flow:
1. [step 1]
2. [step 2]

### Method: method_name(self, param: type)
Logic Flow:
1. [step 1]
2. [step 2]

---

## FEW-SHOT EXAMPLE
### Input snippet:
```python
class OrderService:
    def __init__(self, db):
        self.db = db
    def place_order(self, item_id, qty):
        item = self.db.get(item_id)
        self.db.save(Order(item, qty))
```
### Expected output excerpt:
---
## Executive Summary
OrderService manages the lifecycle of customer orders by coordinating \
database reads and writes. It acts as the primary entry point for order \
placement in the system.

## Class: OrderService
PURPOSE:
Encapsulates order-placement logic, keeping database interaction details \
away from callers.

### Constructor: __init__(self, db)
Logic Flow:
1. Receives a database connection object.
2. Stores it as an instance attribute for later use.

### Method: place_order(self, item_id, qty)
Logic Flow:
1. Retrieves the item record from the database using item_id.
2. Creates a new Order object combining the item and quantity.
3. Persists the new order to the database.
---

## IMPORTANT REMINDERS
- Do NOT include Parameters section
- Do NOT include Returns section
- Do NOT include Security Notes
- Do NOT include Impact Analysis
- Do NOT include Architectural Recommendations
- Keep it simple: PURPOSE + LOGIC FLOW only
"""


class HighLevelAgent(AgentTool, BaseAgent):
    name = "high_level_agent"
    description = "Generates a high-level, non-technical explanation of a single source file."
    args_schema = SingleFileInput

    # ---- LangChain BaseTool required method ----
    def _run(self, code_content: str, class_name: str = None,
             analysis_summary: str = None, file_name: str = None, **kwargs) -> str:
        return self.process(code_content, class_name=class_name,
                            analysis_summary=analysis_summary, file_name=file_name)

    # ---- Public interface (backward-compat) ----
    def process(self, code_content: str, class_name: str = None,
                analysis_summary: str = None, file_name: str = None, **kwargs) -> str:
        context = ""
        if class_name:
            context += f"Class: {class_name}\n"
        if analysis_summary:
            context += f"Analysis Summary:\n{analysis_summary}\n"

        file_label = f"File: {file_name}\n" if file_name else ""
        user_prompt = (
            f"{file_label}{context}\n"
            f"Source Code:\n{code_content}\n\n"
            f"Think step by step, then produce the report following the structure above. "
            f"Use '{file_name or 'Unknown'}' as the filename in the Source Code Analysis section."
        )
        logger.info("[HighLevelAgent] Generating high-level explanation")
        return self.ask_ai(_HIGH_LEVEL_SYSTEM, user_prompt)

    # ---- LangGraph node ----
    def as_node(self, state: DocumentationState) -> DocumentationState:
        try:
            result = self.process(
                state.code_content,
                class_name=state.class_name,
                analysis_summary=state.analysis_summary,
                file_name=state.file_name,
            )
            state.raw_output = result
        except Exception as exc:
            logger.error(f"[HighLevelAgent] node error: {exc}")
            state.error = str(exc)
        return state


# ---------------------------------------------------------------------------
# LowLevelAgent
# ---------------------------------------------------------------------------

_LOW_LEVEL_SYSTEM = """\
## ROLE
You are a Senior Technical Architect writing deep, developer-focused \
documentation for a single source file.

## TASK
Produce a LOW-LEVEL, technically detailed explanation of the provided source code.
Cover every class, constructor, and method — do NOT skip any.

## RULES
1. Think step by step. Analyse the code structure before writing.
2. NEVER invent parameters, return types, or logic that is not in the code.
3. If a method body is trivial (e.g., a getter), still document it fully.
4. Follow the OUTPUT FORMAT below exactly.

## ANTI-HALLUCINATION CONSTRAINTS
- Only describe what is explicitly present in the source code.
- Do NOT assume side-effects unless they are visible in the code.
- Parameter types must match the actual signatures.

## OUTPUT FORMAT
File: [Generic File Title]
---

## Application Lifecycle
[1-2 sentences: how the app initialises, configures dependencies, serves requests]


## API Routes Overview
- [METHOD] /path — short description

## Purpose & Responsibility
[Goal of this code]

## Key Capabilities
- Feature 1
- Feature 2

## Class: [ClassName]
**Purpose:** [Brief class purpose]
**Patterns:** [Mention what was found in context]
**Relationships:** [List all relationships in ONE line. If none, write 'None']
**Complexity Level:** (Low / Medium / High)
**Security Note:** [Identify any potential security risks. If none, write 'None']
**Impact Analysis:** [Side effects of modifying this class]
**Best Practices:** [Comparison vs industry standards — PEP 8, SOLID, etc.]

### Constructor: [name]
**Description:** [Text]

**Logic Flow:**
1. Step One
2. Step Two

**Parameters:**
- **p1**: description

**Returns:** [Text]

**Error Handling:** [How the constructor handles exceptions. If none, suggest what is missing.]

### Method: [name]

**Description:** [Text]

**Logic Flow:**
1. Step One
2. Step Two

**Parameters:**
- **p1**: description

**Returns:** [Text]

**Error Handling:** [How the method handles exceptions. If none, suggest what is missing.]

**Architectural Recommendations:** [Expert advice on improving this class]

---

[Repeat Class section for every class found]

## STRICT RULES FOR OUTPUT
- Do NOT produce any tables or markdown table syntax (no | --- | columns).
- Use only the structured sections above — no extra formatting.

## FEW-SHOT EXAMPLE
### Input snippet:
```python
class AuthMiddleware:
    def __init__(self, app):
        self.app = app
    def __call__(self, request):
        token = request.headers.get("Authorization")
        if not token:
            raise PermissionError("Missing token")
        return self.app(request)
```
### Expected output excerpt:
File: Authentication Middleware

---

## Class: AuthMiddleware
**Purpose:** Acts as a security gate that validates the Authorization header on every request.
**Relationships:** None
**Complexity Level:** Low
**Security Note:** Authorization header is checked but not validated for format or expiry — token forgery is possible.
**Impact Analysis:** Modifying this class affects every incoming request; incorrect changes could lock out all users.
**Best Practices:** Follows Single Responsibility Principle. Consider extracting token validation into a separate utility for testability (SOLID — SRP).

### Constructor: __init__
**Description:** Stores the inner WSGI/ASGI application for later delegation.

**Logic Flow:**
1. Receives the inner application as a parameter.
2. Assigns it to self.app.

**Parameters:**
- **app**: The inner WSGI/ASGI application to wrap.

**Returns:** None

**Error Handling:** No error handling present. Consider validating that app is callable.

### Method: __call__

**Description:** Intercepts each request, checks for an Authorization header, and delegates to the inner app.

**Logic Flow:**
1. Extracts the Authorization header from the request.
2. Raises PermissionError if the header is absent.
3. Delegates to the inner application when the token is present.

**Parameters:**
- **request**: The incoming HTTP request object.

**Returns:** Response from the inner application.

**Error Handling:** Raises PermissionError for missing token. Does not handle malformed tokens.

**Architectural Recommendations:** Extract token validation into a dedicated TokenValidator class. Add logging for failed auth attempts to support auditing.

---
"""


class LowLevelAgent(AgentTool, BaseAgent):
    name = "low_level_agent"
    description = "Generates a detailed, technical explanation of a single source file."
    args_schema = LowLevelInput

    def _run(self, code_content: str, detailed_analysis: str = None, **kwargs) -> str:
        return self.process(code_content, detailed_analysis=detailed_analysis)

    def process(self, code_content: str, detailed_analysis: str = None, **kwargs) -> str:
        context = ""
        if detailed_analysis:
            context = f"Detailed Analysis Context:\n{detailed_analysis}\n\n"

        user_prompt = (
            f"{context}"
            f"Code Content:\n{code_content}\n\n"
            "Think step by step, then provide the low-level detailed explanation "
            "following the OUTPUT FORMAT above."
        )
        logger.info("[LowLevelAgent] Generating low-level explanation")
        return self.ask_ai(_LOW_LEVEL_SYSTEM, user_prompt)

    def as_node(self, state: DocumentationState) -> DocumentationState:
        try:
            result = self.process(
                state.code_content,
                detailed_analysis=state.detailed_analysis,
            )
            state.raw_output = result
        except Exception as exc:
            logger.error(f"[LowLevelAgent] node error: {exc}")
            state.error = str(exc)
        return state


# ---------------------------------------------------------------------------
# ProjectHighLevelAgent
# ---------------------------------------------------------------------------

_PROJECT_HIGH_LEVEL_SYSTEM = """\
## ROLE
You are a Senior Software Architect producing a high-level, non-technical \
overview of an ENTIRE multi-file project for business stakeholders.

## TASK
Analyse the full project context provided and produce a concise architectural \
overview. Focus on WHAT the system does, its major components, and how they \
relate — NOT on implementation details.

## RULES
1. Think step by step. Map the project structure before writing.
2. NEVER invent modules, services, or behaviours not present in the context.
3. If a component's purpose is unclear, write "Purpose not determinable."
4. Follow the OUTPUT FORMAT exactly.

## ANTI-HALLUCINATION CONSTRAINTS
- Base every statement on the provided project context.
- Do NOT assume technology choices unless explicitly visible.
- Class names must match exactly what appears in the context.

## OUTPUT FORMAT
File: [Project Title]

## Executive Summary
[2-3 sentences describing what the project does overall]

---

## Application Lifecycle
[How the system starts, wires dependencies, and handles requests]

## Dependencies
- [External lib / service 1]
- [External lib / service 2]

## API Routes Overview
- [METHOD] /path — short description

## Purpose & Responsibility
[Overall goal of the project]

## Key Capabilities
- Feature 1
- Feature 2

## Class: [ClassName]
- Purpose: [Brief class purpose]
- Logic Flow:
  1. [Step 1]
  2. [Step 2]

[Repeat Class section for every class found across all files]

## FEW-SHOT EXAMPLE
### Project context snippet:
```
File: api/views.py — REST endpoints for user management
  Class: UserViewSet — CRUD operations on User model
File: models/user.py — User domain model
  Class: User — Stores user profile data
```
### Expected output excerpt:
File: User Management Service

## Executive Summary
This project exposes a RESTful API for managing user accounts. It separates \
concerns between the API layer (views.py) and the domain model (user.py).

## Class: UserViewSet
- Purpose: Handles HTTP requests for creating, reading, updating, and \
deleting user records.
- Logic Flow:
  1. Receives HTTP request from the router.
  2. Delegates to the User model for data persistence.
  3. Returns serialised JSON response.
"""


class ProjectHighLevelAgent(AgentTool, BaseAgent):
    name = "project_high_level_agent"
    description = "Generates a high-level overview of an entire multi-file project."
    args_schema = SingleFileInput

    def _run(self, code_content: str, class_name: str = None,
             analysis_summary: str = None, **kwargs) -> str:
        return self.process(code_content, class_name=class_name,
                            analysis_summary=analysis_summary)

    def process(self, code_content: str, class_name: str = None,
                analysis_summary: str = None, file_name: str = None, **kwargs) -> str:
        context = ""
        if analysis_summary:
            context = f"System Summary (Stats & Components):\n{analysis_summary}\n"

        user_prompt = (
            f"{context}"
            f"Project Context & Overview:\n{code_content}\n\n"
            "Think step by step, then provide the high-level system architecture report."
        )
        logger.info("[ProjectHighLevelAgent] Generating project high-level explanation")
        return self.ask_ai(_PROJECT_HIGH_LEVEL_SYSTEM, user_prompt)

    def as_node(self, state: DocumentationState) -> DocumentationState:
        try:
            result = self.process(
                state.code_content,
                class_name=state.class_name,
                analysis_summary=state.analysis_summary,
            )
            state.raw_output = result
        except Exception as exc:
            logger.error(f"[ProjectHighLevelAgent] node error: {exc}")
            state.error = str(exc)
        return state


# ---------------------------------------------------------------------------
# ProjectLowLevelAgent
# ---------------------------------------------------------------------------

_PROJECT_LOW_LEVEL_SYSTEM = """\
## ROLE
You are a Senior Technical Architect performing a DEEP SYSTEM-WIDE LOGIC \
ANALYSIS of an ENTIRE multi-file project.

## TASK
Produce a comprehensive, developer-focused technical analysis covering every \
file, class, constructor, and method in the project.

## RULES
1. Think step by step. Build a mental model of the project before writing.
2. Your very first line MUST be: "Project: Full Technical Analysis"
3. NEVER skip a constructor or method — even trivial ones must be documented.
4. Use the provided Detailed Context to fill in cross-file relationships.
5. If the context says "No inheritance", write "None".
6. Follow the OUTPUT FORMAT exactly.

## ANTI-HALLUCINATION CONSTRAINTS
- Only describe what is present in the provided code and context.
- Parameter names and types must match the actual signatures.
- Do NOT invent design patterns — only report ones you can justify.

## OUTPUT FORMAT

Project: Full Technical Analysis

=== STEP 1: DEEP MODULE ANALYSIS ===

## File: [filename.py]

**File Purpose:** [What this file does in the overall system]

**Cross-Dependencies:** [Other files/services/libraries this file depends on]

---

### Class: [ClassName]

**Purpose:** [What this class is responsible for]

**Patterns:** [Design patterns used, or 'None']

**Relationships:** [e.g., Inherits from 'BaseModel', Composition with 'Engine'. Or 'None']

**Complexity Level:** [Low / Medium / High]

**Security Note:** [Risks or 'None detected']

**Impact Analysis:** [What breaks if this class changes]

**Best Practices:** [PEP 8 / SOLID observations]

### Constructor: [name]

**Description:** [What this constructor initialises]

**Logic Flow:**
1. Step One
2. Step Two

**Parameters:**
- **param1**: type and description

**Returns:** None

**Error Handling:** [How it handles invalid inputs, or what is missing]

### Method: [name]

**Description:** [What this method does]

**Logic Flow:**
1. Step One
2. Step Two

**Parameters:**
- **param1**: type and description

**Returns:** [Return type and contents]

**Error Handling:** [Exceptions, edge cases, or missing handling]

**Architectural Recommendations:** [Expert advice for this class]

---

## Global Architectural Recommendations
[System-wide advice on structure, decoupling, scalability, security]

## FEW-SHOT EXAMPLE
### Context snippet:
```
Class: PaymentProcessor
  Method: charge(amount: float, card_token: str) -> bool
  Inherits: BaseProcessor
```
### Expected output excerpt:
### Class: PaymentProcessor

**Purpose:** Handles the execution of payment charges against external \
payment gateways.

**Relationships:** Inherits from 'BaseProcessor'

### Method: charge

**Description:** Submits a charge request to the payment gateway using \
the provided card token.

**Logic Flow:**
1. Validates that amount is positive.
2. Sends charge request to the gateway with card_token.
3. Returns True on success, False on failure.

**Parameters:**
- **amount**: float — monetary value to charge
- **card_token**: str — tokenised card identifier

**Returns:** bool — True if charge succeeded, False otherwise

**Error Handling:** Does not handle network timeouts — recommend adding \
retry logic.
"""


class ProjectLowLevelAgent(AgentTool, BaseAgent):
    name = "project_low_level_agent"
    description = "Generates a deep technical analysis of an entire multi-file project."
    args_schema = LowLevelInput

    def _run(self, code_content: str, detailed_analysis: str = None, **kwargs) -> str:
        return self.process(code_content, detailed_analysis=detailed_analysis)

    def process(self, code_content: str, detailed_analysis: str = None, **kwargs) -> str:
        # Guard: ensure detailed_analysis is always a string
        safe_analysis = detailed_analysis or "No detailed analysis context provided."
        user_prompt = (
            f"--- DETAILED SYSTEM ANALYSIS CONTEXT ---\n{safe_analysis}\n\n"
            f"--- PROJECT CONTEXTS AND EXECUTION FLOW ---\n{code_content}\n\n"
            "Think step by step, then produce the full technical analysis following "
            "the OUTPUT FORMAT above."
        )
        logger.info("[ProjectLowLevelAgent] Generating project low-level explanation")
        return self.ask_ai(_PROJECT_LOW_LEVEL_SYSTEM, user_prompt)

    def as_node(self, state: DocumentationState) -> DocumentationState:
        try:
            result = self.process(
                state.code_content,
                detailed_analysis=state.detailed_analysis,
            )
            state.raw_output = result
        except Exception as exc:
            logger.error(f"[ProjectLowLevelAgent] node error: {exc}")
            state.error = str(exc)
        return state


# ---------------------------------------------------------------------------
# VerifierAgent
# ---------------------------------------------------------------------------

_VERIFIER_SYSTEM = """\
## ROLE
You are a QA Lead and Technical Reviewer. Your sole job is to verify the \
accuracy of a generated technical explanation against the actual source code.

## TASK
Compare the explanation with the code. Correct ONLY factual errors \
(wrong logic, wrong parameter names, wrong return types). \
Do NOT rewrite or restructure the document.

## RULES
1. Think step by step. Read the code first, then the explanation.
2. Preserve ALL formatting tags: 'File:', '## Class:', '### Method:', \
'### Constructor:', '---', bold keys (**Purpose:**, **Logic Flow:**, etc.).
3. Correct ONLY technical content that is demonstrably wrong.
4. Return ONLY the corrected explanation — no meta-commentary.
5. Maintain the 'File: [FileName]' or 'Project: [Project Name]' first line.
6. Do NOT use '---' inside method descriptions — only between classes/sections.

## ANTI-HALLUCINATION CONSTRAINTS
- Do NOT add information that is not in the source code.
- Do NOT remove sections that are correct.
- If the explanation is already accurate, return it unchanged.

## FEW-SHOT EXAMPLE
### Code:
```python
def add(a: int, b: int) -> int:
    return a + b
```
### Explanation (with error):
"Method: add — multiplies two numbers and returns the product."
### Corrected explanation:
"Method: add — adds two integers and returns their sum."
"""


class VerifierAgent(AgentTool, BaseAgent):
    name = "verifier_agent"
    description = "Verifies and corrects a generated explanation against the source code."
    args_schema = VerifierInput

    SIZE_LIMIT: ClassVar[int] = 50_000  # chars — skip AI verification above this threshold

    def _run(self, code: str, explanation: str,
             force_verification: bool = False, **kwargs) -> str:
        return self.verify(code, explanation, force_verification=force_verification)

    # ---- Public interface (backward-compat) ----
    def verify(self, code: str, explanation: str,
               force_verification: bool = False, **kwargs) -> str:
        """
        Verify explanation accuracy.
        Skips AI call for very large inputs unless force_verification=True.
        """
        code_size = len(str(code)) + len(str(explanation))

        if code_size > self.SIZE_LIMIT and not force_verification:
            logger.warning(
                f"[VerifierAgent] Input too large ({code_size} chars). "
                "Skipping AI verification."
            )
            return explanation

        user_prompt = (
            f"Original Code:\n{code}\n\n"
            f"Explanation to Verify:\n{explanation}\n\n"
            "Verify and correct the content above while keeping all formatting tags intact."
        )

        try:
            logger.info("[VerifierAgent] Running verification")
            return self.ask_ai(_VERIFIER_SYSTEM, user_prompt)
        except Exception as exc:
            logger.error(f"[VerifierAgent] Verification failed: {exc}")
            return explanation

    def verify_async(self, code: str, explanation: str, **kwargs) -> str:
        return self.verify(code, explanation, force_verification=True, **kwargs)

    # ---- LangGraph node ----
    def as_node(self, state: DocumentationState) -> DocumentationState:
        if not state.raw_output:
            logger.warning("[VerifierAgent] No raw_output to verify — skipping")
            state.verified_output = state.raw_output
            return state
        try:
            verified = self.verify(state.code_content, state.raw_output)
            state.verified_output = verified
        except Exception as exc:
            logger.error(f"[VerifierAgent] node error: {exc}")
            state.verified_output = state.raw_output  # fallback
        return state
