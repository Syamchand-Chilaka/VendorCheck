from pydantic import BaseModel


class MetricsSummaryResponse(BaseModel):
    total_vendors: int
    total_documents: int
    total_checks: int
    open_review_tasks: int
    approved_checks: int
    held_checks: int
    rejected_checks: int
