"""
Service layer for orchestrating candidate screening, ranking, and human decision tracking.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Job, Resume, ScreeningSession, ScreeningResult, AuditLog
from api.schemas.screenings import ScreeningRunRequest
from src.core.hybrid_ranker import HybridRanker
from src.core.explainable_ai import ExplainableAI
from src.core.quality_analyzer import ResumeQualityAnalyzer
from src.core.bias_filter import BiasFilter


def utc_now() -> datetime:
    """Helper returning timezone-naive UTC datetime for database compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ScreeningService:
    """Orchestrates candidate evaluation against job specifications."""

    def __init__(
        self,
        ranker: Optional[HybridRanker] = None,
        xai: Optional[ExplainableAI] = None,
        quality_analyzer: Optional[ResumeQualityAnalyzer] = None,
        bias_filter: Optional[BiasFilter] = None
    ):
        self.ranker = ranker or HybridRanker()
        self.xai = xai or ExplainableAI()
        self.quality_analyzer = quality_analyzer or ResumeQualityAnalyzer()
        self.bias_filter = bias_filter or BiasFilter()

    def run_screening(self, db: Session, request: ScreeningRunRequest) -> ScreeningSession:
        """
        Executes a complete screening batch:
        - Loads Job and target Resumes
        - Applies optional Blind Screening PII anonymization
        - Scores each candidate across the 7 hybrid dimensions
        - Generates XAI rationale and recommendations
        - Ranks candidates and persists results with an audit log
        """
        job = db.get(Job, request.job_id)
        if not job:
            raise ValueError(f"Job with ID {request.job_id} not found.")

        # Convert Job model into dictionary expected by core ranker
        jd_data = {
            "job_title": job.title,
            "department": job.department,
            "min_experience_years": job.min_experience,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
            "preferred_degrees": job.preferred_degrees,
            "raw_text": job.description_text or f"{job.title} in {job.department}"
        }

        # Select target resumes
        if request.resume_ids:
            resumes = list(db.scalars(
                select(Resume).where(Resume.id.in_(request.resume_ids))
            ).all())
        else:
            resumes = list(db.scalars(select(Resume)).all())

        if not resumes:
            raise ValueError("No resumes available to screen.")

        # Configure custom weights if provided
        active_weights = request.weights or self.ranker.DEFAULT_WEIGHTS
        self.ranker.weights = active_weights

        # Evaluate each resume
        evaluated_candidates = []
        for idx, resume in enumerate(resumes, start=1):
            candidate_payload = dict(resume.parsed_data)
            candidate_payload["raw_text"] = resume.raw_text
            candidate_payload["file_name"] = resume.file_name

            # Optional Blind Screening Redaction
            if request.blind_screening:
                candidate_payload = self.bias_filter.anonymize_candidate(candidate_payload, candidate_index=idx)

            # Analyze ATS quality
            qa_res = self.quality_analyzer.analyze_resume_quality(candidate_payload)
            quality_score = qa_res.get("overall_quality_score", 75.0)

            # Evaluate with HybridRanker
            eval_res = self.ranker.evaluate_candidate(candidate_payload, jd_data, quality_score=quality_score)

            # Generate XAI reasoning
            explanation = self.xai.generate_explanation(eval_res, jd_data)
            eval_res["explanation"] = explanation
            eval_res["resume_id"] = resume.id

            evaluated_candidates.append(eval_res)

        # Sort candidates descending by score and assign ranks
        evaluated_candidates.sort(key=lambda x: x["overall_score"], reverse=True)
        for rank_idx, cand in enumerate(evaluated_candidates, start=1):
            cand["rank"] = rank_idx

        # Create ScreeningSession
        session_name = request.session_name or f"Screening Batch - {job.title} ({utc_now().strftime('%Y-%m-%d %H:%M')})"
        session = ScreeningSession(
            job_id=job.id,
            session_name=session_name,
            recruiter_email=request.recruiter_email,
            weights=active_weights
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Create ScreeningResults
        for cand in evaluated_candidates:
            result = ScreeningResult(
                session_id=session.id,
                resume_id=cand.get("resume_id"),
                candidate_name=cand.get("candidate_name", "Unknown"),
                overall_score=cand.get("overall_score", 0.0),
                rank=cand.get("rank", 1),
                breakdown=cand.get("breakdown", {}),
                gap_results=cand.get("gap_results", {}),
                candidate_data=cand.get("candidate_data", {}),
                rubric_scores=cand.get("explanation", {}),
                evidence=[],
                is_verified=False,
                decision=None,
                decision_timestamp=None
            )
            db.add(result)

        db.commit()
        db.refresh(session)

        # Audit log entry
        audit = AuditLog(
            action="SCREENING_RUN",
            actor=request.recruiter_email,
            details={
                "session_id": session.id,
                "job_id": job.id,
                "job_title": job.title,
                "total_candidates": len(evaluated_candidates),
                "top_score": evaluated_candidates[0]["overall_score"] if evaluated_candidates else 0.0,
                "blind_screening": request.blind_screening
            }
        )
        db.add(audit)
        db.commit()

        return session

    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[ScreeningSession]:
        """Retrieves a screening session with its results."""
        return db.get(ScreeningSession, session_id)

    @staticmethod
    def list_sessions(db: Session, skip: int = 0, limit: int = 100) -> List[ScreeningSession]:
        """Lists screening sessions ordered by newest first."""
        stmt = select(ScreeningSession).order_by(ScreeningSession.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def update_candidate_decision(
        db: Session,
        result_id: int,
        decision: str,
        actor: str = "recruiter",
        notes: Optional[str] = None
    ) -> Optional[ScreeningResult]:
        """
        Updates human decision (shortlist / reject) with UTC timestamp and logs audit record.
        """
        result = db.get(ScreeningResult, result_id)
        if not result:
            return None

        result.decision = decision.lower()
        result.decision_timestamp = utc_now()
        db.commit()
        db.refresh(result)

        # Audit log for human decision
        audit = AuditLog(
            action="DECISION_UPDATED",
            actor=actor,
            details={
                "result_id": result.id,
                "session_id": result.session_id,
                "candidate_name": result.candidate_name,
                "decision": result.decision,
                "decision_timestamp": result.decision_timestamp.isoformat(),
                "notes": notes
            }
        )
        db.add(audit)
        db.commit()

        return result
