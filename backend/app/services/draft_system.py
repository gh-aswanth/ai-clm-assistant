import asyncio
import base64
import logging
import os
from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from fastapi import WebSocket

from app.services.output_json_to_docx import build_contract_docx_bytes

logger = logging.getLogger(__name__)

DOCX_ATTACHMENT_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

memory = InMemorySaver()
redline_prompt = """
# System Prompt for Legal Document Redlining and Amendment Generation

## Role
You are a specialized legal document redlining system designed to review document chunks and generate precise amendments based on user findings and recommendations. Your amendments will be directly applied to create redlined versions in document review mode. You also have the authority to suggest additional improvements beyond the provided chunks.

## Input
You will receive:
1. **Document chunks**: List of text strings from a legal contract
2. **User findings and recommendations**: Specific issues, changes, or improvements identified by the user

## Processing Instructions

### 1. Chunk Review Process
- Analyze each provided chunk against user findings and recommendations
- Determine if amendments are necessary based on user input
- Only process chunks that require changes according to user guidance
- Skip chunks that need no modifications (do not include in output)

### 2. Additional Amendment Authority
**Beyond Provided Chunks**: You are authorized to recommend additional amendments that are NOT in the existing chunks if they:
- Address legal gaps or deficiencies you identify
- Enhance contract clarity and enforceability
- Improve risk management or compliance
- Add standard industry provisions that are missing
- Strengthen legal protections for parties
- Address potential ambiguities or conflicts

**New Amendment Criteria**:
- Must be legally sound and beneficial
- Should align with contract's overall purpose
- Must not conflict with existing provisions
- Should follow industry best practices
- Must be clearly justified in ai_comment

### 3. Amendment Generation Rules

**Critical Requirements:**
- Generate amendments that will **completely replace** the original chunk
- Create text suitable for direct insertion into redlined documents
- Ensure amendments address specific user findings
- Maintain legal accuracy and document integrity
- Preserve original formatting structure where appropriate

**Amendment Types:**
- **Text modifications**: Word/phrase changes, corrections, clarifications
- **Additions**: New clauses, terms, conditions, or provisions
- **Deletions**: Remove problematic or unnecessary content
- **Restructuring**: Reorganize content for clarity or legal compliance
- **Compliance updates**: Address regulatory or legal requirement changes
- **New provisions**: Add missing but recommended legal protections or clarifications

### 4. Action Types
- **"replaced"**: When modifying existing content - include original text in `document_content` and new version in `redline_recommendation_text`
- **"added"**: When adding entirely new content OR recommended provisions not in existing chunks - set `document_content` to empty string and include new text in `redline_recommendation_text`

### 5. Task Management with TODO Write Tool
**MANDATORY**: After processing each step use the TODO write tool to update task status:

### 6. Processing Workflow with TODO Updates

**Phase 1 - Existing Chunks:**
For each chunk requiring changes:
1. **Review chunk** against user findings
2. **Generate amendment** using RedlineRequest format
3. **Include clear justification** in ai_comment

**Phase 2 - New Recommendations:**
After processing all chunks:
1. **Identify legal gaps** or improvement opportunities
2. **Generate new provisions** as "added" actions
3. **Include clear justification** in ai_comment

## Output Format

```json
[
  {
    "document_content": "EXACT ORIGINAL CHUNK TEXT FROM INPUT (for replaced action) or empty string (for added action)",
    "redline_recommendation_text": "COMPLETE NEW REPLACEMENT TEXT WITH ALL MODIFICATIONS APPLIED or NEW CONTENT TO BE ADDED",
    "ai_comment": "Brief description of what was changed and why - addresses specific user finding or legal improvement",
    "action": "replaced"
  },
  {
    "document_content": "",
    "redline_recommendation_text": "ENTIRELY NEW RECOMMENDED PROVISION NOT IN ORIGINAL CHUNKS",
    "ai_comment": "Detailed justification for new provision - addresses legal gap/risk/best practice",
    "action": "added"
  }
]
```

## Field Specifications

- **document_content**: 
  - For "replaced" action: Exact original chunk text from input
  - For "added" action: Empty string ""

- **redline_recommendation_text**: 
  - For "replaced" action: Complete new text that will replace the original
  - For "added" action: New content to be inserted OR new recommended provisions

- **ai_comment**: Clear explanation of changes made and how they address user findings OR justification for new recommendations

- **action**: Either "replaced" (modifying existing content) or "added" (inserting new content/recommendations)

## Amendment Quality Standards

### DO:
- **USE write_todos** after processing each chunk AND each new recommendation
- Provide complete replacement text in redline_recommendation_text
- Add beneficial provisions not covered in existing chunks
- Maintain legal document formatting and structure
- Address all relevant user findings in amendments
- Ensure amended text flows naturally with surrounding content
- Preserve section numbering and hierarchical structure
- Include clear, detailed AI comments explaining changes and new recommendations
- Justify new provisions with legal reasoning

### DON'T:
- Skip using todo_write_tool for task updates or new recommendations
- Add unnecessary or legally questionable provisions
- Provide partial amendments
- Include chunks that don't need changes
- Create amendments that don't address user findings
- Generate legally problematic or ambiguous language
- Add provisions that conflict with existing contract terms
- Use vague or unclear justifications for new recommendations

## New Recommendation Examples
- Missing indemnification clauses
- Inadequate termination provisions
- Absent intellectual property protections
- Missing governing law clauses
- Insufficient notice requirements
- Absent force majeure provisions
- Missing confidentiality terms
- Inadequate dispute resolution mechanisms

---

**Review the provided document chunks against user findings and generate appropriate amendments. Additionally, recommend new provisions not covered in existing chunks that would improve the contract. Use todo_write_tool to update task status after processing each chunk and each new recommendation. Output all changes using the RedlineRequest format.**"""

from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import InMemorySaver

class RedlineRequest(BaseModel):
    document_content: str | None = Field(description="the actual content of the contract if action is replaced else ''")
    redline_recommendation_text: str | None = Field(
        description="generate redline replacement text for the actual content if necessary ")
    ai_comment: str
    action: Literal["added", "replaced"]


class RedlineResponse(BaseModel):
    findings: list[RedlineRequest]

def get_redline_agent():
    checkpoint = InMemorySaver(
        serde=JsonPlusSerializer(
            allowed_msgpack_modules=[
                ("app.services.draft_system", "RedlineResponse"),
                ("app.services.draft_system", "RedlineRequest"),
            ],
            pickle_fallback=True
        )
    )
    draft_agent = create_agent(
        model=ChatOpenAI(model=os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4"), streaming=False),
        checkpointer=checkpoint,
        response_format=RedlineResponse,
        debug=False,
        system_prompt=redline_prompt,
        middleware=[TodoListMiddleware()],
    )
    return draft_agent


class DraftSystemError(RuntimeError):
    pass


def _structured_findings_as_dicts(structured_response) -> list[dict]:
    if structured_response is None:
        return []
    payload = (
        structured_response.model_dump()
        if hasattr(structured_response, "model_dump")
        else structured_response
    )
    if isinstance(payload, dict):
        findings = payload.get("findings")
        return list(findings) if findings else []
    if isinstance(payload, list):
        return list(payload)
    return []

def _file_type_for_extract(file_row) -> str:
    ft = (getattr(file_row, "file_type", None) or "").lower().strip()
    if not ft and getattr(file_row, "original_filename", None):
        ft = file_row.original_filename.rsplit(".", 1)[-1].lower()
    return ft or "pdf"


async def run_draft(
    websocket: WebSocket,
    message: str,
    draft_agent,
    *,
    version_id: int | None = None,
    contract_id: int | None = None,
    db=None,
    cpwd_augmentation: str | None = None,
):
    """
    Stream draft-agent events to the client (same envelope as /ws/review).
    json_data: { "name": "write_todos"|"model"|"attachment", "data": ... }

    *version_id* – ``DocumentVersion.id`` whose pre-computed chunks are loaded
    from ``document_chunks`` via the version's ``file_id``. When ``None`` the draft runs without chunk context.
    If *contract_id* is set with *version_id*, the version must belong to that contract.
    """
    from app.services.document_chunker import get_chunks_for_version
    from app.services.comparison_chat import extract_text_from_file
    from app.models.models import DocumentVersion, File

    logger.debug("Draft agent message: %s", message)
    logger.debug("Draft agent version_id: %s contract_id: %s", version_id, contract_id)
    thread_config = RunnableConfig(configurable={"thread_id": "draft"}, recursion_limit=100)

    chunk_list: list[str] = []
    source_text = ""
    if version_id and db:
        version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()
        if not version:
            logger.warning("Draft: document version id=%s not found", version_id)
        elif contract_id is not None and version.contract_id != contract_id:
            logger.warning(
                "Draft: version id=%s belongs to contract %s, not %s — skipping file context",
                version_id,
                version.contract_id,
                contract_id,
            )
        elif not version.file_id:
            logger.warning("Draft: version id=%s has no file_id — no chunks", version_id)
        else:
            stored = get_chunks_for_version(db, version_id)
            chunk_list = [c.content for c in stored]
            file_row = db.query(File).filter(File.id == version.file_id).first()
            if file_row and file_row.file_path:
                try:
                    source_text = "\n".join(chunk_list)
                except Exception:
                    logger.warning("Could not extract source text for version %s (file_id=%s)", version_id, version.file_id)
    draft_messages: list[dict] = []
    if cpwd_augmentation and str(cpwd_augmentation).strip():
        draft_messages.append(
            {
                "role": "user",
                "content": (
                    "[PREMIUM CPWD COPILOT — CONTEXT PACK]\n"
                    "Your job is to move the agreement toward a stronger, CPWD-aligned version by editing the contract text "
                    "(add, edit, replace, or rephrase clauses and lines in the document chunks you are given).\n"
                    "If a \"Saved review items\" section appears below, treat those items as high-priority fixes: address "
                    "each one explicitly in your revised wording unless the user instructs otherwise.\n"
                    "Use the guideline snapshot as the target posture, compliance findings to close identified gaps, and "
                    "the scoring summary to prioritize structural and risk improvements.\n"
                    "Output concrete revised contract language (not only commentary) so the user can apply a better version "
                    "of the deal paper.\n\n"
                    + str(cpwd_augmentation).strip()
                    + "\n[END CPWD COPILOT CONTEXT]"
                ),
            }
        )
    draft_messages.append(
        {
            "role": "user",
            "content": f"""
###DocumentChunks:
{chunk_list}\n
{message}
""",
        }
    )
    async for event in draft_agent.astream_events(
        {
            "messages": draft_messages,
        },
        config=thread_config,
        version="v2",
    ):
        # print(event)
        if event.get("name") == "write_todos":
            todos = event.get("data", {}).get("input", {}).get("todos", [])
            await websocket.send_json(
                {"type": "stream", "json_data": {"name": "write_todos", "data": todos}}
            )

    snapshot = await draft_agent.aget_state(thread_config)
    values = snapshot.values or {}
    structured = values.get("structured_response")
    findings_list = _structured_findings_as_dicts(structured)
    if findings_list and source_text:
        try:
            docx_bytes = await asyncio.to_thread(
                build_contract_docx_bytes, findings_list, source_text
            )
            b64 = base64.b64encode(docx_bytes).decode("ascii")
            await websocket.send_json(
                {
                    "type": "stream",
                    "json_data": {
                        "name": "attachment",
                        "data": {
                            "filename": "draft_redline.docx",
                            "content_type": DOCX_ATTACHMENT_MEDIA_TYPE,
                            "data": b64,
                        },
                    },
                }
            )
        except Exception:
            logger.exception("build_contract_docx_bytes failed")
            await websocket.send_json(
                {
                    "type": "stream",
                    "json_data": {
                        "name": "model",
                        "data": "\n\n*(Could not build DOCX attachment.)*",
                    },
                }
            )
    elif structured is None:
        logger.warning("Draft agent finished without structured_response in graph state")

    await websocket.send_json({"type": "done"})
