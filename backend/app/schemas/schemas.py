from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional, List, Any
from app.models.models import ContractStatus, UserRole


# ── Auth / Users ─────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str
    role: str
    premium_access: bool = True

class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: UserRole = UserRole.USER

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    premium_access: Optional[bool] = None

class UserSchema(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    premium_access: bool = True
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Master Signers ──────────────────────────────────────────────────────────

class MasterSignerBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None

class MasterSignerCreate(MasterSignerBase):
    pass

class MasterSignerSchema(MasterSignerBase):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Signature Fields ─────────────────────────────────────────────────────────

class SignatureFieldBase(BaseModel):
    signer_id: Optional[int] = None          # legacy
    version_signer_id: Optional[int] = None  # new
    page_number: int
    x_pos: float
    y_pos: float
    width: float = 150
    height: float = 50
    scale: Optional[float] = 1.5
    field_type: Optional[str] = "signature"
    value: Optional[str] = None
    is_signed: bool = False

class SignatureFieldUpdate(BaseModel):
    signer_id: Optional[int] = None
    version_signer_id: Optional[int] = None
    page_number: Optional[int] = None
    x_pos: Optional[float] = None
    y_pos: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    scale: Optional[float] = None
    field_type: Optional[str] = None
    value: Optional[str] = None
    is_signed: Optional[bool] = None

class SignatureFieldCreate(SignatureFieldBase):
    contract_id: Optional[int] = None
    version_id: Optional[int] = None

class SignatureFieldSchema(SignatureFieldBase):
    id: int
    contract_id: Optional[int] = None
    version_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# ── Version Signers ──────────────────────────────────────────────────────────

class VersionSignerCreate(BaseModel):
    master_signer_id: int
    signing_order: int = 1

class VersionSignerSchema(BaseModel):
    id: int
    version_id: int
    master_signer_id: int
    master_signer: MasterSignerSchema
    signing_order: int
    status: str
    token: str
    invited_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    signature_fields_v2: List[SignatureFieldSchema] = []
    model_config = ConfigDict(from_attributes=True)


# ── Templates ────────────────────────────────────────────────────────────────

class TemplateBase(BaseModel):
    name: str
    category: str
    content: str

class TemplateCreate(TemplateBase):
    pass

class TemplateSchema(TemplateBase):
    id: int
    version: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Compliance ───────────────────────────────────────────────────────────────

class ComplianceRecordBase(BaseModel):
    record_type: Optional[str] = "compliance"
    check_name: str
    status: str
    findings: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    document_version_id: Optional[int] = None

class ComplianceRecordCreate(ComplianceRecordBase):
    contract_id: int

class ComplianceRecordSchema(ComplianceRecordBase):
    id: int
    contract_id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ComplianceRecomputeRequest(BaseModel):
    """Re-run LLM compliance checks for a document version (uses ``file_id`` → ``document_chunks``)."""

    version_id: int


class ComplianceRecomputeResponse(BaseModel):
    contract_id: int
    version_id: int
    file_id: int
    count: int


# ── Milestones ───────────────────────────────────────────────────────────────

class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    status: str = "pending"

class MilestoneCreate(MilestoneBase):
    contract_id: int

class MilestoneUpdate(BaseModel):
    status: str

class MilestoneSchema(MilestoneBase):
    id: int
    contract_id: int
    model_config = ConfigDict(from_attributes=True)


# ── Files ────────────────────────────────────────────────────────────────────

class FileSchema(BaseModel):
    id: int
    original_filename: str
    file_path: str
    file_type: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: int = 0
    folder_id: Optional[int] = None
    upload_id: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Document Versions ────────────────────────────────────────────────────────

class DocumentVersionBase(BaseModel):
    version_number: int
    label: Optional[str] = None
    notes: Optional[str] = None

class DocumentVersionSchema(DocumentVersionBase):
    id: int
    contract_id: int
    file_id: Optional[int] = None
    # file_type and file_path are @property on DocumentVersion and resolve via the File FK
    file_type: Optional[str] = None
    file_path: Optional[str] = None
    signed_file_path: Optional[str] = None
    is_latest: bool
    created_at: Optional[datetime] = None
    version_signers: List[VersionSignerSchema] = []
    model_config = ConfigDict(from_attributes=True)


# ── Legacy Signer (kept for backward compat) ─────────────────────────────────

class SignerBase(BaseModel):
    email: str
    name: str
    status: str = "invited"

class SignerCreate(SignerBase):
    contract_id: int

class SignerSchema(SignerBase):
    id: int
    contract_id: int
    signed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Contracts ────────────────────────────────────────────────────────────────

class ContractBase(BaseModel):
    title: str
    description: Optional[str] = None
    template_id: Optional[int] = None
    status: ContractStatus = ContractStatus.DRAFT
    content: Optional[str] = None
    value: float
    start_date: datetime
    end_date: datetime

class ContractCreate(ContractBase):
    pass

class ContractSchema(ContractBase):
    id: int
    contract_number: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    file_path: Optional[str] = None
    signed_file_path: Optional[str] = None
    file_type: Optional[str] = None
    guideline_framework_slug: Optional[str] = None
    guideline_framework_title: Optional[str] = None
    guideline_snapshot: Optional[Any] = None
    guideline_financial_limits: Optional[Any] = None
    guideline_mandatory_clauses: Optional[Any] = None
    guideline_technical_standards: Optional[Any] = None
    guideline_compliance_requirements: Optional[Any] = None
    guideline_contractor_eligibility: Optional[Any] = None
    guideline_work_execution_standards: Optional[Any] = None
    guideline_measurement_payment: Optional[Any] = None
    guideline_contract_administration: Optional[Any] = None
    guideline_defect_liability: Optional[Any] = None
    guideline_documentation_requirements: Optional[Any] = None
    guideline_decision_thresholds: Optional[Any] = None
    guideline_validation_weights: Optional[Any] = None
    guideline_critical_issues: Optional[Any] = None
    template: Optional[TemplateSchema] = None
    compliance_records: List[ComplianceRecordSchema] = []
    milestones: List[MilestoneSchema] = []
    document_versions: List[DocumentVersionSchema] = []
    signers: List[SignerSchema] = []
    signature_fields: List[SignatureFieldSchema] = []
    model_config = ConfigDict(from_attributes=True)


# ── Token-based signing context ───────────────────────────────────────────────

class SigningContextSchema(BaseModel):
    token: str
    version_signer: VersionSignerSchema
    contract_id: int
    contract_title: str
    version_id: int
    version_number: int
    file_type: str = "pdf"
    all_version_signers: List[VersionSignerSchema] = []
    signature_fields: List[SignatureFieldSchema] = []
    model_config = ConfigDict(from_attributes=True)


# ── Contract review guidelines ───────────────────────────────────────────────

class GuidelineFrameworkSchema(BaseModel):
    id: int
    slug: str
    title: str
    summary: Optional[str] = None
    version_label: Optional[str] = None
    is_default: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class GuidelineSectionSchema(BaseModel):
    id: int
    section_key: str
    title: str
    sort_order: int
    body: Any
    model_config = ConfigDict(from_attributes=True)


class GuidelineCatalogEntrySchema(BaseModel):
    id: int
    bucket: str
    domain: Optional[str] = None
    code: str
    sort_order: int
    model_config = ConfigDict(from_attributes=True)


class GuidelineSectionIndexRow(BaseModel):
    """Row shape matching SQL view v_guideline_section_index."""

    framework_id: int
    framework_slug: str
    framework_title: str
    section_id: int
    section_key: str
    section_title: str
    sort_order: int


class GuidelineBundleSchema(BaseModel):
    framework: GuidelineFrameworkSchema
    sections: List[GuidelineSectionSchema]
    catalog: List[GuidelineCatalogEntrySchema]


class GuidelineFrameworkCreate(BaseModel):
    slug: str
    title: str
    summary: Optional[str] = None
    version_label: Optional[str] = None
    is_default: bool = False


class GuidelineFrameworkUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    version_label: Optional[str] = None
    is_default: Optional[bool] = None


class GuidelineSectionCreate(BaseModel):
    section_key: str
    title: str
    sort_order: int = 0
    body: Any = {}


class GuidelineSectionUpdate(BaseModel):
    title: Optional[str] = None
    sort_order: Optional[int] = None
    body: Optional[Any] = None


class ContractGuidelineUpdate(BaseModel):
    """Partial update for contract guideline data — one field per section for AI automation."""

    guideline_framework_slug: Optional[str] = None
    guideline_framework_title: Optional[str] = None
    guideline_snapshot: Optional[Any] = None
    guideline_financial_limits: Optional[Any] = None
    guideline_mandatory_clauses: Optional[Any] = None
    guideline_technical_standards: Optional[Any] = None
    guideline_compliance_requirements: Optional[Any] = None
    guideline_contractor_eligibility: Optional[Any] = None
    guideline_work_execution_standards: Optional[Any] = None
    guideline_measurement_payment: Optional[Any] = None
    guideline_contract_administration: Optional[Any] = None
    guideline_defect_liability: Optional[Any] = None
    guideline_documentation_requirements: Optional[Any] = None
    guideline_decision_thresholds: Optional[Any] = None
    guideline_validation_weights: Optional[Any] = None
    guideline_critical_issues: Optional[Any] = None


ContractSchema.model_rebuild()
SignerSchema.model_rebuild()


# ── Review Items ─────────────────────────────────────────────────────────────

class ReviewItemSchema(BaseModel):
    id: int
    contract_id: int
    title: Optional[str] = None
    content: str
    source_query: Optional[str] = None
    item_type: str = "finding"
    severity: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ReviewItemCreate(BaseModel):
    title: Optional[str] = None
    content: str
    source_query: Optional[str] = None
    item_type: str = "finding"
    severity: Optional[str] = None


# ── Scoring Results ────────────────────────────────────────────────────────────

class ScoringResultSchema(BaseModel):
    id: int
    contract_id: int
    document_version_id: Optional[int] = None
    file_id: Optional[int] = None
    result_json: dict
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ScoringResultReadSchema(BaseModel):
    """GET /contracts/{id}/scoring — includes empty state when no run exists yet."""

    id: Optional[int] = None
    contract_id: int
    document_version_id: Optional[int] = None
    file_id: Optional[int] = None
    result_json: Optional[dict] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class VersionKnowledgeGraphBuildResponse(BaseModel):
    """POST …/knowledge-graph/build — persisted graph documents for the version."""

    contract_id: int
    document_version_id: int
    graph_documents: List[Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Document Drive repository ────────────────────────────────────────────────────

class DocumentDriveFolderSchema(BaseModel):
    id: int
    drive_id: int
    parent_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    files: List[FileSchema] = []
    children: List["DocumentDriveFolderSchema"] = []
    model_config = ConfigDict(from_attributes=True)


class DocumentDriveSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    folders: List[DocumentDriveFolderSchema] = []
    model_config = ConfigDict(from_attributes=True)


class DocumentDriveCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DocumentDriveFolderCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class DocumentDriveFolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DocumentDriveChunkUploadResponse(BaseModel):
    upload_id: str
    complete: bool
    file: Optional[FileSchema] = None
    model_config = ConfigDict(from_attributes=True)


class DocumentChunkSchema(BaseModel):
    id: int
    file_id: int
    chunk_index: int
    content: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


VersionSignerSchema.model_rebuild()
DocumentVersionSchema.model_rebuild()
DocumentDriveFolderSchema.model_rebuild()
