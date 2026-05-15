from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Enum, Boolean, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base
import datetime
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    premium_access = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    REDRAFT = "redraft"
    SIGNING = "signing"
    ACTIVE = "active"
    APPROVED = "approved"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class File(Base):
    """Central file registry — every uploaded file (contract or drive) gets one row."""

    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    size_bytes = Column(Integer, default=0)
    folder_id = Column(Integer, ForeignKey("document_drive_folders.id"), nullable=True, index=True)
    upload_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    folder = relationship("DocumentDriveFolder", back_populates="files")
    document_versions = relationship("DocumentVersion", back_populates="file")
    chunks = relationship("DocumentChunk", back_populates="file", cascade="all, delete-orphan")
    scoring_results = relationship("ScoringResult", back_populates="file")


class MasterSigner(Base):
    __tablename__ = "master_signers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    title = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    version_signers = relationship("VersionSigner", back_populates="master_signer")

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
    content = Column(Text)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String, unique=True, nullable=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    content = Column(Text)
    value = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # Legacy columns kept for backward compatibility
    file_path = Column(String, nullable=True)
    signed_file_path = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    # AI / review automation: guideline fields — one column per section for AI querying
    guideline_framework_slug = Column(String(128), nullable=True, index=True)
    guideline_framework_title = Column(String(256), nullable=True)
    guideline_snapshot = Column(JSON, nullable=True)  # kept for backward-compat
    guideline_financial_limits = Column(JSON, nullable=True)
    guideline_mandatory_clauses = Column(JSON, nullable=True)
    guideline_technical_standards = Column(JSON, nullable=True)
    guideline_compliance_requirements = Column(JSON, nullable=True)
    guideline_contractor_eligibility = Column(JSON, nullable=True)
    guideline_work_execution_standards = Column(JSON, nullable=True)
    guideline_measurement_payment = Column(JSON, nullable=True)
    guideline_contract_administration = Column(JSON, nullable=True)
    guideline_defect_liability = Column(JSON, nullable=True)
    guideline_documentation_requirements = Column(JSON, nullable=True)
    guideline_decision_thresholds = Column(JSON, nullable=True)
    guideline_validation_weights = Column(JSON, nullable=True)
    guideline_critical_issues = Column(JSON, nullable=True)

    template = relationship("Template")
    milestones = relationship("Milestone", back_populates="contract_parent")
    compliance_records = relationship("ComplianceRecord", back_populates="contract_parent")
    review_items = relationship("ReviewItem", back_populates="contract", cascade="all, delete-orphan", order_by="ReviewItem.created_at.desc()")
    document_versions = relationship(
        "DocumentVersion",
        back_populates="contract_parent",
        order_by="DocumentVersion.version_number"
    )
    signers = relationship("Signer", back_populates="contract_parent")
    signature_fields = relationship(
        "SignatureField",
        foreign_keys="SignatureField.contract_id",
        back_populates="contract_parent"
    )
class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True, index=True)
    version_number = Column(Integer)
    label = Column(String, nullable=True)
    signed_file_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    is_latest = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    contract_parent = relationship("Contract", back_populates="document_versions")
    file = relationship("File", back_populates="document_versions")
    version_signers = relationship("VersionSigner", back_populates="version", cascade="all, delete-orphan")
    signature_fields_v2 = relationship(
        "SignatureField",
        foreign_keys="SignatureField.version_id",
        back_populates="version"
    )
    compliance_records = relationship(
        "ComplianceRecord",
        back_populates="document_version",
        passive_deletes=True,
    )
    knowledge_graph = relationship(
        "VersionKnowledgeGraph",
        back_populates="document_version",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def file_path(self):
        return self.file.file_path if self.file else None

    @property
    def file_type(self):
        return self.file.file_type if self.file else None

class VersionSigner(Base):
    __tablename__ = "version_signers"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("document_versions.id"))
    master_signer_id = Column(Integer, ForeignKey("master_signers.id"))
    signing_order = Column(Integer, default=1)
    status = Column(String, default="pending")  # pending, invited, signed, declined
    token = Column(String, unique=True, index=True)
    invited_at = Column(DateTime, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    declined_reason = Column(Text, nullable=True)

    version = relationship("DocumentVersion", back_populates="version_signers")
    master_signer = relationship("MasterSigner", back_populates="version_signers")
    signature_fields_v2 = relationship(
        "SignatureField",
        foreign_keys="SignatureField.version_signer_id",
        back_populates="version_signer"
    )

    __table_args__ = (
        UniqueConstraint('version_id', 'master_signer_id', name='uq_version_master_signer'),
    )

class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    title = Column(String)
    description = Column(Text)
    due_date = Column(DateTime)
    status = Column(String, default="pending")  # pending, completed, delayed

    contract_parent = relationship("Contract", back_populates="milestones")


class ComplianceRecord(Base):
    __tablename__ = "compliance_records"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    document_version_id = Column(
        Integer,
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    record_type = Column(String, default="compliance")  # compliance, complaint
    check_name = Column(String)
    status = Column(String)  # passed, failed, warning, open, resolved
    findings = Column(Text)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    contract_parent = relationship("Contract", back_populates="compliance_records")
    document_version = relationship("DocumentVersion", back_populates="compliance_records")

# Legacy table — kept so existing signing URLs still work
class Signer(Base):
    __tablename__ = "signers"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    email = Column(String, index=True)
    name = Column(String)
    status = Column(String, default="invited")  # invited, signed, declined
    signed_at = Column(DateTime, nullable=True)

    contract_parent = relationship("Contract", back_populates="signers")
    signature_fields = relationship(
        "SignatureField",
        foreign_keys="SignatureField.signer_id",
        back_populates="signer"
    )

class SignatureField(Base):
    __tablename__ = "signature_fields"

    id = Column(Integer, primary_key=True, index=True)
    # New version-linked columns
    version_id = Column(Integer, ForeignKey("document_versions.id"), nullable=True)
    version_signer_id = Column(Integer, ForeignKey("version_signers.id"), nullable=True)
    # Legacy columns
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    signer_id = Column(Integer, ForeignKey("signers.id"), nullable=True)

    page_number = Column(Integer)
    x_pos = Column(Float)
    y_pos = Column(Float)
    width = Column(Float, default=150)
    height = Column(Float, default=50)
    scale = Column(Float, default=1.5)
    field_type = Column(String, default="signature")  # signature, date, text, initials
    value = Column(Text, nullable=True)
    is_signed = Column(Boolean, default=False)

    contract_parent = relationship("Contract", foreign_keys=[contract_id], back_populates="signature_fields")
    signer = relationship("Signer", foreign_keys=[signer_id], back_populates="signature_fields")
    version = relationship("DocumentVersion", foreign_keys=[version_id], back_populates="signature_fields_v2")
    version_signer = relationship("VersionSigner", foreign_keys=[version_signer_id], back_populates="signature_fields_v2")


class GuidelineFramework(Base):
    """Root bundle for a contract review guideline framework (e.g. CPWD-aligned checklist)."""

    __tablename__ = "guideline_frameworks"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(256), nullable=False)
    summary = Column(Text, nullable=True)
    version_label = Column(String(64), nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sections = relationship(
        "GuidelineSection",
        back_populates="framework",
        order_by="GuidelineSection.sort_order",
        cascade="all, delete-orphan",
    )
    catalog_entries = relationship(
        "GuidelineCatalogEntry",
        back_populates="framework",
        order_by="GuidelineCatalogEntry.sort_order",
        cascade="all, delete-orphan",
    )


class GuidelineSection(Base):
    """Top-level document slice (financial_limits, mandatory_clauses, …) as structured JSON."""

    __tablename__ = "guideline_sections"

    id = Column(Integer, primary_key=True, index=True)
    framework_id = Column(Integer, ForeignKey("guideline_frameworks.id", ondelete="CASCADE"), nullable=False)
    section_key = Column(String(128), nullable=False)
    title = Column(String(256), nullable=False)
    sort_order = Column(Integer, default=0)
    body = Column(JSON, nullable=False)

    framework = relationship("GuidelineFramework", back_populates="sections")

    __table_args__ = (
        UniqueConstraint("framework_id", "section_key", name="uq_guideline_section_framework_key"),
    )


class GuidelineCatalogEntry(Base):
    """Flattened checklist rows (mandatory clauses domains, compliance lists, critical issues, …)."""

    __tablename__ = "guideline_catalog_entries"

    id = Column(Integer, primary_key=True, index=True)
    framework_id = Column(Integer, ForeignKey("guideline_frameworks.id", ondelete="CASCADE"), nullable=False)
    bucket = Column(String(64), nullable=False, index=True)
    domain = Column(String(128), nullable=True, index=True)
    code = Column(String(256), nullable=False)
    sort_order = Column(Integer, default=0)

    framework = relationship("GuidelineFramework", back_populates="catalog_entries")


class DocumentChunk(Base):
    """LLM-generated document chunks, linked to a File."""

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    file = relationship("File", back_populates="chunks")


class ReviewItem(Base):
    """Saved review-agent findings/actionable items for a contract."""

    __tablename__ = "review_items"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(512), nullable=True)
    content = Column(Text, nullable=False)
    source_query = Column(Text, nullable=True)
    item_type = Column(String(64), default="finding", nullable=False)  # finding | recommendation | summary
    severity = Column(String(32), nullable=True)                       # critical | moderate | minor
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    contract = relationship("Contract", back_populates="review_items")


class VersionKnowledgeGraph(Base):
    """LLM-extracted knowledge graph (LangChain GraphDocument list) per document version."""

    __tablename__ = "version_knowledge_graphs"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(
        Integer,
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    graph_documents_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    contract = relationship("Contract", backref="version_knowledge_graphs")
    document_version = relationship("DocumentVersion", back_populates="knowledge_graph")


class ScoringResult(Base):
    """Stored output from the agent-workflow scoring pipeline; keyed by contract + file (version document)."""

    __tablename__ = "scoring_results"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(Integer, ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"), nullable=True, index=True)
    result_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    contract = relationship("Contract", backref="scoring_results")
    document_version = relationship("DocumentVersion", backref="scoring_results")
    file = relationship("File", back_populates="scoring_results")


# ── Document Drive repository ────────────────────────────────────────────────────

class DocumentDrive(Base):
    __tablename__ = "document_drives"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    folders = relationship("DocumentDriveFolder", back_populates="drive", cascade="all, delete-orphan")


class DocumentDriveFolder(Base):
    __tablename__ = "document_drive_folders"

    id = Column(Integer, primary_key=True, index=True)
    drive_id = Column(Integer, ForeignKey("document_drives.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("document_drive_folders.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    drive = relationship("DocumentDrive", back_populates="folders")
    parent = relationship("DocumentDriveFolder", remote_side=[id], back_populates="children")
    children = relationship("DocumentDriveFolder", back_populates="parent", cascade="all, delete-orphan")
    files = relationship("File", back_populates="folder", cascade="all, delete-orphan")
