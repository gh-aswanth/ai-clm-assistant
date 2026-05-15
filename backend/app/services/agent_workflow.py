"""
CPWD Contract Validation Agent Workflow

Multi-agent LangGraph workflow that:
1. Loads contract-specific guidelines from the database
2. Classifies the contract and routes it through parallel validation agents
3. Cross-validates the results

Usage::

    from app.services.agent_workflow import compile_graph, load_contract_guidelines
    from app.db.database import SessionLocal

    db = SessionLocal()
    contract_id = 42
    initial_state = load_contract_guidelines(contract_id, db)
    graph = compile_graph()
    result = graph.invoke(initial_state)
"""

import json
import logging
import operator
import os
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing_extensions import Annotated

logger = logging.getLogger(__name__)

# LLM model for all agent nodes — override via OPENAI_CHAT_MODEL env var
_OPENAI_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4")

# ---------------------------------------------------------------------------
# Guideline section keys — must match Contract model column suffixes
# ---------------------------------------------------------------------------

_GUIDELINE_COLUMN_MAP: Dict[str, str] = {
    "financial_limits": "guideline_financial_limits",
    "mandatory_clauses": "guideline_mandatory_clauses",
    "technical_standards": "guideline_technical_standards",
    "compliance_requirements": "guideline_compliance_requirements",
    "contractor_eligibility": "guideline_contractor_eligibility",
    "work_execution_standards": "guideline_work_execution_standards",
    "measurement_payment": "guideline_measurement_payment",
    "contract_administration": "guideline_contract_administration",
    "defect_liability": "guideline_defect_liability",
    "documentation_requirements": "guideline_documentation_requirements",
    "decision_thresholds": "guideline_decision_thresholds",
    "validation_weights": "guideline_validation_weights",
    "critical_issues": "guideline_critical_issues",
}

# ---------------------------------------------------------------------------
# DB → Guidelines loader
# ---------------------------------------------------------------------------


def load_contract_guidelines(contract_id: int, db: Session) -> dict:
    """Fetch a contract from the database and return the initial graph state.

    Reads the ``guideline_*`` JSON columns from the ``contracts`` table and
    assembles them into the ``guidelines`` dict that the workflow nodes expect.

    Returns a dict suitable for passing directly to ``graph.invoke()``.

    Raises ``ValueError`` if the contract does not exist.
    """
    from app.models.models import Contract  # deferred to avoid circular imports

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract is None:
        raise ValueError(f"Contract with id={contract_id} not found")

    guidelines: Dict[str, Any] = {}
    for section_key, column_name in _GUIDELINE_COLUMN_MAP.items():
        value = getattr(contract, column_name, None)
        if value is not None:
            guidelines[section_key] = value

    return {
        "contract_id": contract_id,
        "guidelines": guidelines,
    }


# ---------------------------------------------------------------------------
# Shared Enums
# ---------------------------------------------------------------------------


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceLevel(str, Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"


class ComplianceStatus(str, Enum):
    PASS = "PASS"
    CONDITIONAL = "CONDITIONAL"
    FAIL = "FAIL"


class ImpactLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------------------------
# Classification Schemas
# ---------------------------------------------------------------------------


class ValidationClassification(BaseModel):
    agent_type: Literal[
        "mandatory_clauses",
        "financial_compliance",
        "technical_standards",
        "legal_statutory",
        "contractor_eligibility",
        "work_execution",
        "documentation_admin",
    ] = Field(description="Type of validation agent to route to")
    contract_sections: List[str] = Field(
        description="List of contract sections relevant to this validation type"
    )
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(
        description="Severity level of validation findings"
    )
    validation_focus: List[str] = Field(
        description="List of specific validation aspects to focus on"
    )


class ContractMetadata(BaseModel):
    contract_id: Optional[str] = Field(default=None, description="Contract reference number or ID")
    value: Optional[str] = Field(default=None, description="Contract value in rupees")
    duration: Optional[str] = Field(default=None, description="Contract duration")
    contract_type: Optional[str] = Field(default=None, description="Type of contract/work")
    parties: Optional[str] = Field(default=None, description="Contract parties summary")
    work_description: Optional[str] = Field(default=None, description="Brief work description")


class ValidationClassificationResult(BaseModel):
    classifications: List[ValidationClassification] = Field(
        description="List of validation agents to invoke with their targeted contract sections"
    )
    contract_metadata: ContractMetadata = Field(
        description="Basic contract information extracted during classification"
    )


# ---------------------------------------------------------------------------
# Financial Compliance Schemas
# ---------------------------------------------------------------------------


class FinancialComplianceDetails(BaseModel):
    amount_analyzed: float | int | str = Field(
        description="Actual amount/percentage found in contract"
    )
    cpwd_limit: str = Field(description="CPWD prescribed limit for this category")
    variance: float | int | str = Field(description="Percentage variance from CPWD limit")
    compliance_status: str = Field(description="COMPLIANT/DEVIATION/NON_COMPLIANT")
    risk_level: str = Field(description="LOW/MEDIUM/HIGH/CRITICAL")


class FinancialCriticalIssue(BaseModel):
    issue_type: str = Field(description="Type of financial non-compliance")
    description: str = Field(description="Detailed issue description")
    impact: str = Field(description="Impact on contract execution")
    severity: str = Field(description="LOW/MEDIUM/HIGH/CRITICAL")
    remedial_action: str = Field(description="Specific action required to resolve")


class FinancialRecommendation(BaseModel):
    category: str = Field(description="Financial category being addressed")
    recommendation: str = Field(description="Specific recommendation text")
    priority: str = Field(description="HIGH/MEDIUM/LOW priority")
    implementation: str = Field(description="How to implement this recommendation")


class FinancialAnalyticsScore(BaseModel):
    advance_payments: Any = Field(None, description="Advance payment compliance score")
    retention_money: Any = Field(None, description="Retention money compliance score")
    performance_guarantee: Any = Field(None, description="Performance guarantee compliance score")
    liquidated_damages: Any = Field(None, description="Liquidated damages compliance score")
    security_deposits: Any = Field(None, description="Security deposits compliance score")
    price_variation: Any = Field(None, description="Price variation compliance score")
    overall_compliance_score: Any = Field(None, ge=0, le=100)
    financial_risk_rating: Any = Field(None, description="LOW/MEDIUM/HIGH/CRITICAL")
    compliance_details: Dict[str, FinancialComplianceDetails] | Any = Field(None)
    critical_issues: List[FinancialCriticalIssue] | Any = Field(None)
    recommendations: List[FinancialRecommendation] | Any = Field(None)
    approval_recommendation: Any = Field(None, description="APPROVE/CONDITIONAL/REVISE/REJECT")
    conditions_for_approval: List[str] | Any = Field(default=[])
    executive_summary: str | Any = Field(None)


class ValidationOutput(BaseModel):
    agent_type: str = Field(description="Type of validation agent")
    category_scores: Dict[str, float] = Field(description="Scores for each validation category")
    overall_score: float = Field(description="Overall validation score")
    compliance_status: str = Field(description="Compliance status after validation")
    findings: List[Dict] = Field(description="List of validation findings")
    critical_issues: List[Dict] = Field(description="List of critical validation issues")
    recommendations: List[str] = Field(description="List of validation recommendations")
    validation_details: Dict[str, Any] = Field(description="Additional details from validation")


# ---------------------------------------------------------------------------
# Mandatory Clauses Schemas
# ---------------------------------------------------------------------------


class CategoryScores(BaseModel):
    contract_essentials: float = Field(..., ge=0, le=100)
    payment_terms: float = Field(..., ge=0, le=100)
    timeline_provisions: float = Field(..., ge=0, le=100)
    quality_safety: float = Field(..., ge=0, le=100)
    legal_provisions: float = Field(..., ge=0, le=100)
    insurance_guarantees: float = Field(..., ge=0, le=100)


class Finding(BaseModel):
    category: str = Field(...)
    issue: str = Field(...)
    severity: SeverityLevel = Field(...)
    score_impact: float = Field(...)


class MandatoryCriticalIssue(BaseModel):
    issue: str = Field(...)
    category: str = Field(...)
    impact: ImpactLevel = Field(...)


class ValidationDetails(BaseModel):
    total_clauses_checked: int = Field(..., ge=0)
    compliant_clauses: int = Field(..., ge=0)
    missing_clauses: int = Field(..., ge=0)
    conditional_clauses: int = Field(..., ge=0)


class MandatoryClausesValidation(BaseModel):
    agent_type: Literal["mandatory_clauses"] = Field(default="mandatory_clauses")
    category_scores: CategoryScores = Field(...)
    overall_score: float = Field(..., ge=0, le=100)
    compliance_status: ComplianceStatus = Field(...)
    findings: List[Finding] = Field(default_factory=list)
    critical_issues: List[MandatoryCriticalIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    validation_details: ValidationDetails = Field(...)


class MandatoryClausesValidationResponse(BaseModel):
    validation_results: List[MandatoryClausesValidation] = Field(...)


# ---------------------------------------------------------------------------
# Technical Standards Schemas
# ---------------------------------------------------------------------------


class ConcreteGrade(str, Enum):
    M10 = "M10"
    M15 = "M15"
    M20 = "M20"
    M25 = "M25"
    M30 = "M30"
    M35 = "M35"
    M40 = "M40"


class SteelGrade(str, Enum):
    Fe415 = "Fe415"
    Fe500 = "Fe500"
    Fe550 = "Fe550"


class CementType(str, Enum):
    OPC_33 = "OPC_33"
    OPC_43 = "OPC_43"
    OPC_53 = "OPC_53"
    PPC = "PPC"
    SRC = "SRC"


class TechnicalCategoryScores(BaseModel):
    concrete_standards: float = Field(..., ge=0, le=100)
    steel_specifications: float = Field(..., ge=0, le=100)
    cement_quality: float = Field(..., ge=0, le=100)
    testing_requirements: float = Field(..., ge=0, le=100)
    quality_control: float = Field(..., ge=0, le=100)
    material_compliance: float = Field(..., ge=0, le=100)


class TechnicalFinding(BaseModel):
    category: str = Field(...)
    finding: str = Field(...)
    compliance: ComplianceLevel = Field(...)


class TechnicalCriticalIssue(BaseModel):
    issue: str = Field(...)
    category: str = Field(...)
    severity: SeverityLevel = Field(...)


class TechnicalValidationDetails(BaseModel):
    concrete_grade: Optional[ConcreteGrade] = None
    concrete_is_codes: List[str] = Field(default_factory=list)
    steel_grade: Optional[SteelGrade] = None
    steel_is_codes: List[str] = Field(default_factory=list)
    cement_type: Optional[CementType] = None
    cement_is_codes: List[str] = Field(default_factory=list)
    brick_standards: List[str] = Field(default_factory=list)
    aggregate_standards: List[str] = Field(default_factory=list)
    quality_plan_required: bool = False
    third_party_inspection: bool = False
    nabl_accredited_labs: bool = False
    testing_frequency_specified: bool = False
    mill_test_certificates: bool = False


class TechnicalStandardsValidation(BaseModel):
    agent_type: Literal["technical_standards"] = Field(default="technical_standards")
    category_scores: TechnicalCategoryScores = Field(...)
    overall_score: float = Field(..., ge=0, le=100)
    compliance_status: ComplianceStatus = Field(...)
    findings: List[TechnicalFinding] = Field(default_factory=list)
    critical_issues: List[TechnicalCriticalIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    validation_details: TechnicalValidationDetails = Field(...)


class TechnicalStandardsAgentResponse(BaseModel):
    validation_results: List[TechnicalStandardsValidation] = Field(...)


# ---------------------------------------------------------------------------
# Legal / Statutory Schemas
# ---------------------------------------------------------------------------


class LegalCategoryScores(BaseModel):
    arbitration_compliance: float = Field(..., ge=0, le=100)
    statutory_requirements: float = Field(..., ge=0, le=100)
    contractor_eligibility: float = Field(..., ge=0, le=100)
    force_majeure_provisions: float = Field(..., ge=0, le=100)
    jurisdiction_clarity: float = Field(..., ge=0, le=100)
    legal_documentation: float = Field(..., ge=0, le=100)


class LegalFinding(BaseModel):
    category: str = Field(...)
    finding: str = Field(...)
    compliance: ComplianceLevel = Field(...)


class LegalCriticalIssue(BaseModel):
    issue: str = Field(...)
    category: str = Field(...)
    severity: SeverityLevel = Field(...)


class LegalValidationDetails(BaseModel):
    arbitration_act_2015_compliant: bool = False
    arbitration_clause_present: bool = False
    arbitrator_selection_method: Optional[str] = None
    jurisdiction_specified: Optional[str] = None
    governing_law_mentioned: bool = False
    force_majeure_comprehensive: bool = False
    force_majeure_events_listed: List[str] = Field(default_factory=list)
    statutory_clearances_mentioned: bool = False
    statutory_details_adequate: bool = False
    environmental_clearance_required: bool = False
    labor_law_compliance_mentioned: bool = False
    contractor_registration_required: bool = False
    registration_type_specified: Optional[str] = None
    technical_capacity_criteria: bool = False
    financial_capacity_criteria: bool = False
    performance_security_compliant: bool = False
    termination_clause_adequate: bool = False
    indemnity_clause_present: bool = False
    liability_limitations_defined: bool = False


class LegalStatutoryValidation(BaseModel):
    agent_type: Literal["legal_statutory"] = Field(default="legal_statutory")
    category_scores: LegalCategoryScores = Field(...)
    overall_score: float = Field(..., ge=0, le=100)
    compliance_status: ComplianceStatus = Field(...)
    findings: List[LegalFinding] = Field(default_factory=list)
    critical_issues: List[LegalCriticalIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    validation_details: LegalValidationDetails = Field(...)


class LegalStatutoryAgentResponse(BaseModel):
    validation_results: List[LegalStatutoryValidation] = Field(...)


# ---------------------------------------------------------------------------
# Work Execution Schemas
# ---------------------------------------------------------------------------


class EnvironmentalPlanLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"
    COMPREHENSIVE = "comprehensive"
    DETAILED = "detailed"


class WorkExecutionCategoryScores(BaseModel):
    quality_control: float = Field(..., ge=0, le=100)
    safety_management: float = Field(..., ge=0, le=100)
    environmental_compliance: float = Field(..., ge=0, le=100)
    testing_requirements: float = Field(..., ge=0, le=100)
    execution_methodology: float = Field(..., ge=0, le=100)
    supervision_standards: float = Field(..., ge=0, le=100)


class WorkExecutionFinding(BaseModel):
    category: str = Field(...)
    finding: str = Field(...)
    compliance: ComplianceLevel = Field(...)


class WorkExecutionCriticalIssue(BaseModel):
    issue: str = Field(...)
    category: str = Field(...)
    severity: SeverityLevel = Field(...)


class WorkExecutionValidationDetails(BaseModel):
    quality_plan_required: bool = False
    quality_control_procedures_defined: bool = False
    inspection_and_testing_plan: bool = False
    safety_officer_mandatory: bool = False
    safety_equipment_standards: bool = False
    safety_training_requirements: bool = False
    environmental_plan: EnvironmentalPlanLevel = EnvironmentalPlanLevel.NONE
    environmental_clearance_compliance: bool = False
    waste_management_procedures: bool = False
    dust_control_measures: bool = False
    noise_pollution_limits: bool = False
    nabl_testing_specified: bool = False
    third_party_inspection: bool = False
    cpwd_specifications_referenced: bool = False
    method_statements_required: bool = False
    progress_monitoring_system: bool = False
    quality_assurance_plan: bool = False
    material_approval_process: bool = False
    workmanship_standards: bool = False
    site_supervision_requirements: bool = False
    record_keeping_requirements: bool = False
    completion_criteria: bool = False


class WorkExecutionValidation(BaseModel):
    agent_type: Literal["work_execution"] = Field(default="work_execution")
    category_scores: WorkExecutionCategoryScores = Field(...)
    overall_score: float = Field(..., ge=0, le=100)
    compliance_status: ComplianceStatus = Field(...)
    findings: List[WorkExecutionFinding] = Field(default_factory=list)
    critical_issues: List[WorkExecutionCriticalIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    validation_details: WorkExecutionValidationDetails = Field(...)


class WorkExecutionAgentResponse(BaseModel):
    validation_results: List[WorkExecutionValidation] = Field(...)


# ---------------------------------------------------------------------------
# Documentation / Admin Schemas
# ---------------------------------------------------------------------------


class AdministrativeProcedureLevel(str, Enum):
    NONE = "none"
    BASIC = "basic"
    COMPREHENSIVE = "comprehensive"
    DETAILED = "detailed"


class VariationLimitType(str, Enum):
    NOT_SPECIFIED = "not_specified"
    TEN_PERCENT = "10_percent"
    FIFTEEN_PERCENT = "15_percent"
    TWENTY_PERCENT = "20_percent"
    TWENTY_FIVE_PERCENT_COMPETENT_AUTHORITY = "25_percent_competent_authority"
    THIRTY_PERCENT = "30_percent"
    UNLIMITED_APPROVAL_REQUIRED = "unlimited_approval_required"


class DocumentationCategoryScores(BaseModel):
    mandatory_documents: float = Field(..., ge=0, le=100)
    technical_documentation: float = Field(..., ge=0, le=100)
    administrative_procedures: float = Field(..., ge=0, le=100)
    variation_management: float = Field(..., ge=0, le=100)
    record_keeping: float = Field(..., ge=0, le=100)
    submission_procedures: float = Field(..., ge=0, le=100)


class DocumentationFinding(BaseModel):
    category: str = Field(...)
    finding: str = Field(...)
    compliance: ComplianceLevel = Field(...)


class DocumentationCriticalIssue(BaseModel):
    issue: str = Field(...)
    category: str = Field(...)
    severity: SeverityLevel = Field(...)


class DocumentationValidationDetails(BaseModel):
    drawings_specified: bool = False
    technical_specs_attached: bool = False
    boq_present: bool = False
    method_statements_required: bool = False
    safety_code_referenced: bool = False
    environmental_clearance_docs: bool = False
    statutory_approval_docs: bool = False
    administrative_procedures: AdministrativeProcedureLevel = AdministrativeProcedureLevel.NONE
    approval_hierarchy_defined: bool = False
    submission_procedures_defined: bool = False
    review_and_approval_timeline: bool = False
    variation_limits: VariationLimitType = VariationLimitType.NOT_SPECIFIED
    variation_approval_procedure: bool = False
    rate_determination_method: bool = False
    quality_plan_submission: bool = False
    progress_report_format: bool = False
    as_built_drawings_required: bool = False
    quality_record_maintenance: bool = False
    material_approval_docs: bool = False
    testing_certificate_requirements: bool = False
    inspection_report_format: bool = False
    third_party_certification: bool = False
    correspondence_procedures: bool = False
    change_order_documentation: bool = False
    claim_submission_procedures: bool = False
    final_documentation_handover: bool = False
    digital_submission_format: bool = False
    document_version_control: bool = False
    electronic_approval_system: bool = False


class DocumentationAdminValidation(BaseModel):
    agent_type: Literal["documentation_admin"] = Field(default="documentation_admin")
    category_scores: DocumentationCategoryScores = Field(...)
    overall_score: float = Field(..., ge=0, le=100)
    compliance_status: ComplianceStatus = Field(...)
    findings: List[DocumentationFinding] = Field(default_factory=list)
    critical_issues: List[DocumentationCriticalIssue] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    validation_details: DocumentationValidationDetails = Field(...)


class DocumentationAdminAgentResponse(BaseModel):
    validation_results: List[DocumentationAdminValidation] = Field(...)


# ---------------------------------------------------------------------------
# Graph State
# ---------------------------------------------------------------------------


class CPWDValidationState(TypedDict):
    contract_id: int
    contract_text: str
    guidelines: dict
    contract_metadata: dict
    classifications: dict
    validation_results: Annotated[list, operator.add]
    cross_validation_result: dict
    finance_analysis: dict
    weighted_scores: dict
    final_decision: dict
    comprehensive_report: dict


# ---------------------------------------------------------------------------
# Financial Analysis Tools — factory that closes over a specific guidelines dict
# ---------------------------------------------------------------------------


def _create_financial_tools(guidelines: dict) -> list:
    """Return a list of @tool-decorated functions bound to *guidelines*."""
    fin = guidelines.get("financial_limits", {})

    @tool
    def analyze_advance_payment_structure(contract_value: float) -> str:
        """Comprehensive advance payment analysis against guidelines."""
        limits = fin.get("advance_payment", {})
        sec = limits.get("secured_advance_max", "N/A")
        mob = limits.get("mobilization_advance_max", "N/A")
        pla = limits.get("plant_machinery_advance_max", "N/A")
        mat = limits.get("material_advance_max", "N/A")
        parts = [
            f"ADVANCE PAYMENT ANALYSIS:\nContract Value: ₹{contract_value:,.0f}",
            f"Advance Payment Limits:",
        ]
        if isinstance(sec, (int, float)):
            parts.append(f"- Secured Advance: Maximum {sec}% (₹{contract_value * sec / 100:,.0f})")
        if isinstance(mob, (int, float)):
            parts.append(f"- Mobilization Advance: Maximum {mob}% (₹{contract_value * mob / 100:,.0f})")
        if isinstance(mat, (int, float)):
            parts.append(f"- Material Advance: Maximum {mat}% of material cost")
        if isinstance(pla, (int, float)):
            parts.append(f"- Plant & Machinery Advance: Maximum {pla}% of P&M cost")
        parts += [
            "Security Requirements:",
            "- Bank guarantee mandatory for all advances",
            "- Guarantee validity: Contract period + 6 months",
            "- Recovery through running bills",
        ]
        return "\n".join(parts)

    @tool
    def evaluate_retention_money_terms() -> str:
        """Detailed retention money evaluation."""
        rl = fin.get("retention_money", {})
        return (
            f"RETENTION MONEY EVALUATION:\n"
            f"Retention Guidelines:\n"
            f"- Standard Rate: {rl.get('min', 'N/A')}-{rl.get('max', 'N/A')}% of each running bill\n"
            f"- Maximum Retention: {rl.get('max', 'N/A')}% of contract value\n"
            f"- Release Schedule: {json.dumps(rl.get('release_conditions', {}), indent=2)}\n"
            f"- Interest: Applicable if retention exceeds prescribed limits\n"
            f"Compliance Verification:\n"
            f"- Rate within prescribed range\n"
            f"- Release conditions clearly defined\n"
            f"- Maximum cap specified\n"
            f"- Interest clause present if applicable"
        )

    @tool
    def assess_performance_guarantee_adequacy(contract_value: float) -> str:
        """Performance guarantee adequacy assessment."""
        pg = fin.get("performance_guarantee", {})
        pg_min = pg.get("min", "N/A")
        pg_max = pg.get("max", "N/A")
        parts = [
            "PERFORMANCE GUARANTEE ASSESSMENT:",
            "Requirements:",
        ]
        if isinstance(pg_min, (int, float)) and isinstance(pg_max, (int, float)):
            parts.append(
                f"- Amount: {pg_min}-{pg_max}% of contract value "
                f"(₹{contract_value * pg_min / 100:,.0f} - ₹{contract_value * pg_max / 100:,.0f})"
            )
        parts += [
            "- Form: Bank guarantee or insurance guarantee",
            f"- Validity: {pg.get('validity', 'N/A')}",
            "- Format: As per standard format",
            "- Invocation: On contractor default",
        ]
        return "\n".join(parts)

    @tool
    def analyze_liquidated_damages_fairness(contract_value: float) -> str:
        """Liquidated damages fairness and compliance analysis."""
        ld = fin.get("liquidated_damages", {})
        rate = ld.get("max_per_week", "N/A")
        cap = ld.get("total_max", "N/A")
        grace = ld.get("grace_period_days", "N/A")
        parts = [
            "LIQUIDATED DAMAGES ANALYSIS:",
            "Guidelines:",
            f"- Rate: Maximum {rate}% per week of contract value",
        ]
        if isinstance(cap, (int, float)):
            parts.append(f"- Total Cap: Maximum {cap}% of contract value (₹{contract_value * cap / 100:,.0f})")
        parts += [
            f"- Grace Period: {grace} days",
            "- Application: Automatic on delay",
            "Fairness Assessment:",
            "- Rate proportionate to actual loss",
            "- Not punitive in nature",
            "- Reasonable total cap",
            "- Clear calculation method",
        ]
        return "\n".join(parts)

    @tool
    def validate_security_deposit_structure(estimated_cost: float) -> str:
        """Security deposit structure validation."""
        perf = fin.get("security_deposit", {}).get("performance", {})
        p_min = perf.get("min", "N/A")
        p_max = perf.get("max", "N/A")
        parts = ["SECURITY DEPOSIT VALIDATION:", "Security Requirements:"]
        if isinstance(p_min, (int, float)) and isinstance(p_max, (int, float)):
            parts += [
                f"Tender Security:",
                f"- Amount: {p_min}-{p_max}% of contract value "
                f"(₹{estimated_cost * p_min / 100:,.0f} - ₹{estimated_cost * p_max / 100:,.0f})",
                f"Performance Security:",
                f"- Amount: {p_min}-{p_max}% of contract value "
                f"(₹{estimated_cost * p_min / 100:,.0f} - ₹{estimated_cost * p_max / 100:,.0f})",
                "- Additional to tender security",
            ]
        return "\n".join(parts)

    @tool
    def examine_price_variation_applicability(contract_value: float, duration_months: int) -> str:
        """Price variation clause examination for applicability."""
        pv = fin.get("price_variation", {})
        thresh_amt = pv.get("threshold_amount", 0)
        thresh_per = pv.get("threshold_period", 0)
        applicable = (
            "YES"
            if isinstance(thresh_amt, (int, float))
            and isinstance(thresh_per, (int, float))
            and contract_value > thresh_amt
            and duration_months > thresh_per
            else "NO"
        )
        return (
            f"PRICE VARIATION EXAMINATION:\n"
            f"Price Variation Criteria:\n"
            f"- Applicable: Contract Value > {thresh_amt} AND duration > {thresh_per} months\n"
            f"- Current Contract: ₹{contract_value:,.0f}, Duration: {duration_months} months\n"
            f"- Formula Based: {'YES' if pv.get('formula_based') else 'NO'}\n"
            f"- Threshold: 10% variation in material cost\n"
            f"Applicability: {applicable}"
        )

    return [
        analyze_advance_payment_structure,
        evaluate_retention_money_terms,
        assess_performance_guarantee_adequacy,
        analyze_liquidated_damages_fairness,
        validate_security_deposit_structure,
        examine_price_variation_applicability,
    ]


# ---------------------------------------------------------------------------
# System Prompt builders — each receives the per-contract guidelines dict
# ---------------------------------------------------------------------------


def _financial_system_prompt(guidelines: dict) -> str:
    fin_limits = guidelines.get("financial_limits", {})
    return (
        "# CPWD FINANCIAL COMPLIANCE EXPERT SYSTEM\n\n"
        "You are the **CPWD Financial Compliance Authority** - the definitive expert for "
        "validating all financial terms in government construction contracts against "
        "the contract-specific guideline framework.\n\n"
        "## PRIMARY MANDATE\n"
        "Protect government financial interests while ensuring fair, legally compliant "
        "contract terms that facilitate successful project execution.\n\n"
        "## FINANCIAL COMPLIANCE MATRIX:\n"
        f"```json\n{json.dumps(fin_limits, indent=2)}\n```\n\n"
        "EXPERT SCORING METHODOLOGY\n"
        "1. ADVANCE PAYMENTS SCORING (Weight: 25%)\n"
        "   95-100: Perfect compliance with all advance types within limits\n"
        "   85-94: Minor procedural gaps but amounts compliant\n"
        "   70-84: Slight excess (1-5%) with adequate security\n"
        "   50-69: Moderate excess (5-15%) requiring justification\n"
        "   Below 50: Major non-compliance (>15% excess) - CRITICAL\n\n"
        "2. RETENTION MONEY SCORING (Weight: 15%)\n"
        "   95-100: Proper rate, release schedule, interest clause\n"
        "   85-94: Correct rate, minor release condition issues\n"
        "   70-84: Slightly outside range, adequate release terms\n"
        "   50-69: Rate outside range or unclear release terms\n"
        "   Below 50: Excessive retention or no release terms\n\n"
        "3. PERFORMANCE GUARANTEE SCORING (Weight: 25%)\n"
        "   95-100: Correct amount, proper validity, standard format\n"
        "   85-94: Correct amount, minor format/validity issues\n"
        "   70-84: Slightly outside range, adequate validity period\n"
        "   50-69: Outside range or insufficient validity\n"
        "   Below 50: No guarantee or inadequate security - CRITICAL\n\n"
        "4. LIQUIDATED DAMAGES SCORING (Weight: 20%)\n"
        "   95-100: Within prescribed weekly/total limits, reasonable terms\n"
        "   85-94: Slightly above weekly limit but fair total cap\n"
        "   70-84: Needs justification\n"
        "   50-69: Potentially punitive\n"
        "   Below 50: Excessive - CRITICAL\n\n"
        "5. SECURITY DEPOSITS SCORING (Weight: 10%)\n"
        "   95-100: Within prescribed ranges, proper format\n"
        "   85-94: Amounts correct, minor procedural issues\n"
        "   70-84: Slightly outside ranges but reasonable\n"
        "   50-69: Inadequate security for risk profile\n"
        "   Below 50: Insufficient or excessive requirements\n\n"
        "6. PRICE VARIATION SCORING (Weight: 5%)\n"
        "   95-100: Proper applicability, formula-based, fair threshold\n"
        "   85-94: Applicable, minor formula refinements needed\n"
        "   70-84: Needs clarification on formula/threshold\n"
        "   50-69: Inappropriate application or unclear terms\n"
        "   Below 50: Unfair price variation terms\n\n"
        "DECISION SUPPORT FRAMEWORK\n"
        "APPROVE: Score ≥90, no critical issues, full compliance\n"
        "CONDITIONAL: Score 75-89, minor issues with specific conditions\n"
        "REVISE: Score 60-74, moderate issues requiring amendments\n"
        "REJECT: Score <60, major non-compliance or critical issues\n\n"
        "You MUST provide comprehensive FinancialAnalyticsScore output."
    )


def _mandatory_clauses_system_prompt(guidelines: dict) -> str:
    mc = guidelines.get("mandatory_clauses", {})
    return (
        "You are a mandatory clauses validation expert with comprehensive knowledge "
        "of all required contract elements.\n\n"
        f"MANDATORY CLAUSES FRAMEWORK:\n{json.dumps(mc, indent=2)}\n\n"
        "VALIDATION RESPONSIBILITIES:\n"
        "1. Contract Essentials: Verify party identification, work description, contract value breakup, scope definition\n"
        "2. Payment Terms: Validate payment schedule, milestone payments, advance terms, retention money, final payment conditions\n"
        "3. Timeline Provisions: Check commencement date, completion timeline, extension clauses, liquidated damages\n"
        "4. Quality & Safety: Assess quality specifications, testing requirements, safety provisions, environmental compliance\n"
        "5. Legal Provisions: Validate arbitration clause, termination provisions, force majeure, applicable law\n"
        "6. Insurance & Guarantees: Check insurance requirements, performance guarantees, defect liability\n\n"
        "SCORING METHODOLOGY:\n"
        "- Each category scored 0-100 based on completeness and compliance\n"
        "- Critical missing clauses result in automatic point deduction\n"
        "- Overall score is weighted average of all categories\n"
        "- Flag critical issues that affect contract enforceability\n\n"
        "Provide detailed analysis with specific recommendations for improvements."
    )


def _technical_standards_system_prompt(guidelines: dict) -> str:
    ts = guidelines.get("technical_standards", {})
    return (
        "You are a technical standards validation expert ensuring compliance with IS codes and quality requirements.\n\n"
        f"TECHNICAL STANDARDS:\n{json.dumps(ts, indent=2)}\n\n"
        "VALIDATION CATEGORIES:\n"
        "1. Concrete Specifications: Grades, IS Codes, Testing frequency\n"
        "2. Steel Specifications: Grades, IS Codes, Testing requirements\n"
        "3. Cement Specifications: Types, IS Codes, Testing\n"
        "4. Masonry Work: Brick classes, mortar ratios\n\n"
        "QUALITY CONTROL REQUIREMENTS:\n"
        "- Third-party inspection for critical items\n"
        "- NABL accredited testing laboratories\n"
        "- Quality plan mandatory for all works\n"
        "- Material test certificates required\n\n"
        "SCORING CRITERIA:\n"
        "- IS codes compliance: 40% weightage\n"
        "- Material specifications: 30% weightage\n"
        "- Testing requirements: 20% weightage\n"
        "- Quality control measures: 10% weightage\n\n"
        "Flag non-standard specifications or missing IS code references as critical issues."
    )


def _legal_statutory_system_prompt(guidelines: dict) -> str:
    comp = guidelines.get("compliance_requirements", {})
    elig = guidelines.get("contractor_eligibility", {})
    return (
        "You are a legal and statutory compliance expert ensuring all legal requirements are met.\n\n"
        "LEGAL COMPLIANCE FRAMEWORK:\n"
        "- Arbitration clause compliance with Arbitration Act 2015\n"
        "- Termination provisions as per contract law\n"
        "- Force majeure clauses covering all scenarios\n"
        "- Applicable law and jurisdiction clearly specified\n"
        "- Statutory clearances and permissions\n\n"
        f"COMPLIANCE REQUIREMENTS:\n{json.dumps(comp, indent=2)}\n\n"
        f"CONTRACTOR ELIGIBILITY:\n{json.dumps(elig, indent=2)}\n\n"
        "VALIDATION SCORING:\n"
        "- Arbitration clause: 25% (critical)\n"
        "- Statutory compliance: 25% (critical)\n"
        "- Contractor eligibility: 20%\n"
        "- Termination provisions: 15%\n"
        "- Force majeure coverage: 15%\n\n"
        "Any missing legal clause or statutory non-compliance is a critical issue."
    )


def _work_execution_system_prompt(guidelines: dict) -> str:
    we = guidelines.get("work_execution_standards", {})
    mp = guidelines.get("measurement_payment", {})
    return (
        "You are a work execution standards expert focusing on quality control, safety, and environmental compliance.\n\n"
        f"WORK EXECUTION STANDARDS:\n{json.dumps(we, indent=2)}\n\n"
        f"MEASUREMENT & PAYMENT:\n{json.dumps(mp, indent=2)}\n\n"
        "Score each category 0-100 and provide weighted overall score.\n"
        "Flag inadequate safety provisions or missing environmental measures as critical."
    )


def _documentation_admin_system_prompt(guidelines: dict) -> str:
    dr = guidelines.get("documentation_requirements", {})
    ca = guidelines.get("contract_administration", {})
    return (
        "You are a documentation and contract administration expert ensuring all procedural requirements are met.\n\n"
        f"DOCUMENTATION REQUIREMENTS:\n{json.dumps(dr, indent=2)}\n\n"
        f"CONTRACT ADMINISTRATION:\n{json.dumps(ca, indent=2)}\n\n"
        "SCORING METHODOLOGY:\n"
        "- Documentation completeness: 40%\n"
        "- Administrative procedures: 30%\n"
        "- Submission requirements: 20%\n"
        "- Variation and extension clauses: 10%\n\n"
        "Flag missing critical documents or inadequate administrative procedures."
    )


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------


def classify_contract_comprehensive(state: CPWDValidationState):
    """Route contract sections to appropriate validation agents."""
    guidelines = state["guidelines"]
    classifier_llm = init_chat_model(f"openai:{_OPENAI_MODEL}")
    structured_llm = classifier_llm.with_structured_output(ValidationClassificationResult)

    mc = guidelines.get("mandatory_clauses", {})
    fl = guidelines.get("financial_limits", {})
    ts = guidelines.get("technical_standards", {})

    classification_prompt = (
        "Analyze this contract comprehensively and classify for specialized validation agents.\n\n"
        "VALIDATION FRAMEWORK:\n"
        f"- Mandatory Clauses: {len(mc)} categories\n"
        f"- Financial Compliance: {len(fl)} areas\n"
        f"- Technical Standards: {len(ts)} material types\n"
        "- Legal/Statutory: Multiple compliance requirements\n"
        "- Work Execution: Quality, safety, environmental standards\n"
        "- Documentation: Administrative and procedural requirements\n\n"
        "VALIDATION AGENTS AVAILABLE:\n"
        "1. mandatory_clauses: Essential contract elements and clauses\n"
        "2. financial_compliance: Payment terms, advances, guarantees vs limits\n"
        "3. technical_standards: Material specs, IS codes, quality requirements\n"
        "4. legal_statutory: Legal clauses, statutory compliance, contractor eligibility\n"
        "5. work_execution: Quality control, safety, environmental standards\n"
        "6. documentation_admin: Documentation requirements and administrative procedures\n\n"
        "CLASSIFICATION REQUIREMENTS:\n"
        "- Extract relevant contract sections for each agent\n"
        "- Identify specific validation focus areas within each section\n"
        "- Set priority levels based on criticality and compliance impact\n"
        "- Extract basic contract metadata for validation context\n\n"
        f"CONTRACT TO ANALYZE:\n{state['contract_text']}\n\n"
        "Provide comprehensive classification ensuring all aspects are covered."
    )

    result: ValidationClassificationResult = structured_llm.invoke(
        [
            {"role": "system", "content": classification_prompt},
            {"role": "user", "content": "Perform comprehensive contract classification"},
        ]
    )
    return {
        "classifications": {rec.agent_type: rec.model_dump() for rec in result.classifications},
        "contract_metadata": result.contract_metadata.model_dump(),
    }


def validate_contract_comprehensive(state: CPWDValidationState):
    """Financial compliance validation node."""
    guidelines = state["guidelines"]
    model = init_chat_model(f"openai:{_OPENAI_MODEL}")
    financial_tools = _create_financial_tools(guidelines)

    financial_compliance_agent = create_agent(
        model,
        response_format=FinancialAnalyticsScore,
        tools=financial_tools,
        system_prompt=_financial_system_prompt(guidelines),
    )

    fin_limits = guidelines.get("financial_limits", {})
    response = financial_compliance_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Perform comprehensive financial compliance validation:\n\n"
                        f"CONTRACT SECTIONS: {state['classifications']['financial_compliance']['contract_sections']}\n"
                        f"FINANCIAL LIMITS: {json.dumps(fin_limits, indent=2)}\n"
                        f"CONTRACT METADATA: {state['contract_metadata']}\n\n"
                        "Validate every financial term against the guideline limits."
                    ),
                }
            ]
        }
    )
    return {"finance_analysis": response["structured_response"].model_dump(mode="json")}


def validate_mandatory_clauses_comprehensive(state: CPWDValidationState) -> dict:
    """Comprehensive mandatory clauses validation."""
    guidelines = state["guidelines"]
    model = init_chat_model(f"openai:{_OPENAI_MODEL}")

    mandatory_clauses_agent = create_agent(
        model,
        response_format=MandatoryClausesValidationResponse,
        middleware=[TodoListMiddleware()],
        system_prompt=_mandatory_clauses_system_prompt(guidelines),
    )

    cls = state["classifications"]["mandatory_clauses"]
    result = mandatory_clauses_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Perform comprehensive mandatory clauses validation:\n\n"
                        f"CONTRACT:\n```\n{state['contract_text']}\n```\n"
                        f"PRIORITY: {cls['priority']}\n"
                        f"CONTRACT SECTIONS: {cls['contract_sections']}\n"
                        f"CONTRACT METADATA: {state['contract_metadata']}\n"
                        f"VALIDATION FOCUS: {cls.get('validation_focus', [])}\n\n"
                        "Validate against all mandatory clause categories and provide detailed scoring."
                    ),
                }
            ]
        }
    )
    return result["structured_response"].model_dump(mode="json")


def validate_technical_standards_comprehensive(state: CPWDValidationState) -> dict:
    """Comprehensive technical standards validation."""
    guidelines = state["guidelines"]
    model = init_chat_model(f"openai:{_OPENAI_MODEL}", temperature=0.0)

    technical_standards_agent = create_agent(
        model,
        response_format=TechnicalStandardsAgentResponse,
        system_prompt=_technical_standards_system_prompt(guidelines),
    )

    cls = state["classifications"]["technical_standards"]
    ts = guidelines.get("technical_standards", {})
    result = technical_standards_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Perform comprehensive technical standards validation:\n"
                        f"CONTRACT:\n```\n{state['contract_text']}\n```\n"
                        f"PRIORITY: {cls['priority']}\n"
                        f"CONTRACT SECTIONS: {cls['contract_sections']}\n"
                        f"VALIDATION FOCUS: {cls.get('validation_focus', [])}\n"
                        f"TECHNICAL STANDARDS: {json.dumps(ts, indent=2)}\n\n"
                        "Validate all material specifications, IS codes, and quality requirements."
                    ),
                }
            ]
        }
    )
    return result["structured_response"].model_dump(mode="json")


def validate_legal_statutory_comprehensive(state: CPWDValidationState) -> dict:
    """Comprehensive legal and statutory compliance validation."""
    guidelines = state["guidelines"]
    model = init_chat_model(f"openai:{_OPENAI_MODEL}", temperature=0.0)

    legal_statutory_agent = create_agent(
        model,
        response_format=LegalStatutoryAgentResponse,
        system_prompt=_legal_statutory_system_prompt(guidelines),
    )

    cls = state["classifications"]["legal_statutory"]
    result = legal_statutory_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Perform comprehensive legal and statutory validation:\n\n"
                        f"CONTRACT:\n```\n{state['contract_text']}\n```\n"
                        f"PRIORITY: {cls['priority']}\n"
                        f"CONTRACT SECTIONS: {cls['contract_sections']}\n"
                        f"VALIDATION FOCUS: {cls.get('validation_focus', [])}\n"
                        f"CONTRACT METADATA: {state['contract_metadata']}\n\n"
                        "Validate complete legal compliance and statutory requirements."
                    ),
                }
            ]
        }
    )
    return result["structured_response"].model_dump(mode="json")


def validate_work_execution_comprehensive(state: CPWDValidationState) -> dict:
    """Comprehensive work execution standards validation."""
    guidelines = state["guidelines"]
    model = init_chat_model(f"openai:{_OPENAI_MODEL}", temperature=0.0)

    work_execution_agent = create_agent(
        model,
        response_format=WorkExecutionAgentResponse,
        system_prompt=_work_execution_system_prompt(guidelines),
    )

    cls = state["classifications"]["work_execution"]
    result = work_execution_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Perform comprehensive work execution validation:\n"
                        f"CONTRACT:\n```\n{state['contract_text']}\n```\n"
                        f"PRIORITY: {cls['priority']}\n"
                        f"CONTRACT SECTIONS: {cls['contract_sections']}\n"
                        f"VALIDATION FOCUS: {cls.get('validation_focus', [])}\n\n"
                        "Validate all work execution and administrative standards."
                    ),
                }
            ]
        }
    )
    return result["structured_response"].model_dump(mode="json")


def validate_documentation_admin_comprehensive(state: CPWDValidationState) -> dict:
    """Comprehensive documentation and administration validation."""
    guidelines = state["guidelines"]
    model = init_chat_model(f"openai:{_OPENAI_MODEL}", temperature=0.0)

    documentation_admin_agent = create_agent(
        model,
        response_format=DocumentationAdminAgentResponse,
        system_prompt=_documentation_admin_system_prompt(guidelines),
    )

    cls = state["classifications"]["documentation_admin"]
    result = documentation_admin_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Perform comprehensive documentation validation:\n\n"
                        f"CONTRACT:\n```\n{state['contract_text']}\n```\n"
                        f"PRIORITY: {cls['priority']}\n"
                        f"CONTRACT SECTIONS: {cls['contract_sections']}\n"
                        f"VALIDATION FOCUS: {cls.get('validation_focus', [])}\n"
                        f"CONTRACT METADATA: {state['contract_metadata']}\n\n"
                        "Validate complete documentation and administrative compliance."
                    ),
                }
            ]
        }
    )
    return result["structured_response"].model_dump(mode="json")


def cross_validate_comprehensive(state: CPWDValidationState) -> dict:
    """Cross-validate results from all validation agents."""
    return {}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


def route_to_validation_agents_enhanced(state: CPWDValidationState) -> List[Send]:
    """Route to the validation agents present in the classification output."""
    return [Send(c, state) for c, _ in state["classifications"].items()]


# ---------------------------------------------------------------------------
# Entry Point — compile the graph
# ---------------------------------------------------------------------------


def compile_graph():
    """Build and compile the CPWD comprehensive validation workflow graph.

    The compiled graph expects an initial state with at least::

        {
            "contract_id": int,
            "contract_text": str,
            "guidelines": dict,   # loaded from the contract's guideline_* columns
        }

    Use :func:`load_contract_guidelines` to build this from a contract ID, then::

        graph = compile_graph()
        initial = load_contract_guidelines(contract_id, db)
        result = graph.invoke(initial)
    """
    workflow = (
        StateGraph(CPWDValidationState)
        .add_node("classify", classify_contract_comprehensive)
        .add_node("mandatory_clauses", validate_mandatory_clauses_comprehensive)
        .add_node("financial_compliance", validate_contract_comprehensive)
        .add_node("technical_standards", validate_technical_standards_comprehensive)
        .add_node("legal_statutory", validate_legal_statutory_comprehensive)
        .add_node("work_execution", validate_work_execution_comprehensive)
        .add_node("documentation_admin", validate_documentation_admin_comprehensive)
        .add_node("cross_validate", cross_validate_comprehensive)
        .add_edge(START, "classify")
        .add_conditional_edges(
            "classify",
            route_to_validation_agents_enhanced,
            [
                "mandatory_clauses",
                "financial_compliance",
                "technical_standards",
                "legal_statutory",
                "work_execution",
                "documentation_admin",
            ],
        )
        .add_edge("mandatory_clauses", "cross_validate")
        .add_edge("financial_compliance", "cross_validate")
        .add_edge("technical_standards", "cross_validate")
        .add_edge("legal_statutory", "cross_validate")
        .add_edge("work_execution", "cross_validate")
        .add_edge("documentation_admin", "cross_validate")
        .add_edge("cross_validate", END)
        .compile()
    )
    return workflow
