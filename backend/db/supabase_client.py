import copy
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

try:
    from supabase import create_client, Client
except Exception:  # pragma: no cover - dependency fallback
    create_client = None
    Client = object

from backend.utils.ai_utils import safe_cosine_similarity


_LOCAL_TABLES: dict[str, list[dict]] = defaultdict(list)
_LOCAL_COUNTERS: dict[str, int] = defaultdict(int)


def _clone_rows(rows: list[dict]) -> list[dict]:
    return [copy.deepcopy(row) for row in rows]


def _next_id(table_name: str) -> str:
    _LOCAL_COUNTERS[table_name] += 1
    return f"{table_name}-{_LOCAL_COUNTERS[table_name]}"


class _LocalResponse:
    def __init__(self, data: list[dict]):
        self.data = data


class _LocalQuery:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self._filters: list[tuple[str, object]] = []
        self._limit: int | None = None
        self._order_by: str | None = None
        self._order_desc: bool = False
        self._select_columns: str | None = None
        self._record: dict | None = None
        self._mode: str = "select"
        self._on_conflict: str | None = None

    def select(self, columns: str = "*", count: str | None = None):
        self._mode = "select"
        self._select_columns = columns
        return self

    def insert(self, record: dict):
        self._mode = "insert"
        self._record = copy.deepcopy(record)
        return self

    def upsert(self, record: dict, on_conflict: str | None = None):
        self._mode = "upsert"
        self._record = copy.deepcopy(record)
        self._on_conflict = on_conflict
        return self

    def eq(self, field: str, value: object):
        self._filters.append((field, value))
        return self

    def order(self, field: str, desc: bool = False):
        self._order_by = field
        self._order_desc = desc
        return self

    def limit(self, count: int):
        self._limit = count
        return self

    def _apply_filters(self, rows: list[dict]) -> list[dict]:
        filtered = rows
        for field, value in self._filters:
            filtered = [row for row in filtered if row.get(field) == value]
        if self._order_by:
            filtered = sorted(filtered, key=lambda row: row.get(self._order_by), reverse=self._order_desc)
        if self._limit is not None:
            filtered = filtered[: self._limit]
        return filtered

    def _project(self, rows: list[dict]) -> list[dict]:
        if not self._select_columns or self._select_columns == "*":
            return _clone_rows(rows)
        columns = [column.strip() for column in self._select_columns.split(",")]
        return [{column: row.get(column) for column in columns} for row in rows]

    def execute(self):
        rows = _LOCAL_TABLES[self.table_name]

        if self._mode == "insert" and self._record is not None:
            record = copy.deepcopy(self._record)
            record.setdefault("id", _next_id(self.table_name))
            rows.append(record)
            return _LocalResponse([copy.deepcopy(record)])

        if self._mode == "upsert" and self._record is not None:
            record = copy.deepcopy(self._record)
            record.setdefault("id", _next_id(self.table_name))
            if self._on_conflict:
                conflict_fields = [field.strip() for field in self._on_conflict.split(",")]
                for index, existing in enumerate(rows):
                    if all(existing.get(field) == record.get(field) for field in conflict_fields):
                        merged = {**existing, **record}
                        rows[index] = merged
                        return _LocalResponse([copy.deepcopy(merged)])
            rows.append(record)
            return _LocalResponse([copy.deepcopy(record)])

        filtered = self._apply_filters(rows)
        return _LocalResponse(self._project(filtered))


class _LocalRpc:
    def __init__(self, function_name: str, payload: dict):
        self.function_name = function_name
        self.payload = payload

    def execute(self):
        if self.function_name != "match_jobs":
            return _LocalResponse([])

        query_embedding = self.payload.get("query_embedding") or []
        match_threshold = float(self.payload.get("match_threshold", 0.6))
        match_count = int(self.payload.get("match_count", 15))

        jobs = _LOCAL_TABLES.get("jobs", [])
        embeddings = {row.get("job_id"): row.get("embedding", []) for row in _LOCAL_TABLES.get("job_embeddings", [])}

        scored_jobs: list[dict] = []
        for job in jobs:
            embedding = embeddings.get(job.get("id"))
            if not embedding:
                text = " ".join(str(job.get(field, "")) for field in ["title", "company", "description"])
                embedding = [0.0] * max(len(query_embedding), 64)
                if query_embedding:
                    embedding = [0.0] * len(query_embedding)
                    tokens = text.lower().split()
                    for token in tokens:
                        index = hash(token) % len(embedding)
                        embedding[index] += 1.0

            similarity = safe_cosine_similarity(query_embedding, embedding)
            if similarity >= match_threshold or not query_embedding:
                scored_jobs.append({**job, "similarity": similarity})

        scored_jobs.sort(key=lambda row: row.get("similarity", 0.0), reverse=True)
        return _LocalResponse(scored_jobs[:match_count])


class _LocalSupabaseClient:
    def table(self, table_name: str):
        return _LocalQuery(table_name)

    def rpc(self, function_name: str, payload: dict):
        return _LocalRpc(function_name, payload)


class _FallbackQuery:
    def __init__(self, remote_query, local_query):
        self._remote_query = remote_query
        self._local_query = local_query

    def select(self, columns: str = "*", count: str | None = None):
        self._remote_query = self._remote_query.select(columns, count=count)
        self._local_query.select(columns, count=count)
        return self

    def insert(self, record: dict):
        self._remote_query = self._remote_query.insert(record)
        self._local_query.insert(record)
        return self

    def upsert(self, record: dict, on_conflict: str | None = None):
        self._remote_query = self._remote_query.upsert(record, on_conflict=on_conflict)
        self._local_query.upsert(record, on_conflict=on_conflict)
        return self

    def eq(self, field: str, value: object):
        self._remote_query = self._remote_query.eq(field, value)
        self._local_query.eq(field, value)
        return self

    def order(self, field: str, desc: bool = False):
        self._remote_query = self._remote_query.order(field, desc=desc)
        self._local_query.order(field, desc=desc)
        return self

    def limit(self, count: int):
        self._remote_query = self._remote_query.limit(count)
        self._local_query.limit(count)
        return self

    def execute(self):
        try:
            remote_result = self._remote_query.execute()
        except Exception:
            return self._local_query.execute()

        try:
            local_result = self._local_query.execute()
        except Exception:
            return remote_result

        remote_data = getattr(remote_result, "data", None)
        local_data = getattr(local_result, "data", None)
        if (not remote_data) and local_data:
            return local_result
        return remote_result


class _FallbackRpc:
    def __init__(self, remote_rpc, local_rpc):
        self._remote_rpc = remote_rpc
        self._local_rpc = local_rpc

    def execute(self):
        try:
            remote_result = self._remote_rpc.execute()
        except Exception:
            return self._local_rpc.execute()

        try:
            local_result = self._local_rpc.execute()
        except Exception:
            return remote_result

        remote_data = getattr(remote_result, "data", None)
        local_data = getattr(local_result, "data", None)
        if (not remote_data) and local_data:
            return local_result
        return remote_result


class _FallbackSupabaseClient:
    def __init__(self, remote_client, local_client):
        self._remote_client = remote_client
        self._local_client = local_client

    def table(self, table_name: str):
        return _FallbackQuery(self._remote_client.table(table_name), self._local_client.table(table_name))

    def rpc(self, function_name: str, payload: dict):
        return _FallbackRpc(self._remote_client.rpc(function_name, payload), self._local_client.rpc(function_name, payload))


def get_supabase_client() -> object:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key or create_client is None:
        return _LocalSupabaseClient()

    try:
        remote_client = create_client(url, key)
        return _FallbackSupabaseClient(remote_client, _LocalSupabaseClient())
    except Exception:
        return _LocalSupabaseClient()


def update_analysis_status(
    student_id: str,
    current_agent: str,
    completed_agents: list[str],
    percentage: int,
    status: str = "running"
) -> None:
    """Update the analysis status for a student in Supabase."""
    client = get_supabase_client()
    client.table("analysis_status").upsert({
        "student_id": student_id,
        "current_agent": current_agent,
        "completed_agents": completed_agents,
        "percentage": percentage,
        "status": status
    }, on_conflict="student_id").execute()


def save_job(job: dict) -> dict:
    """Save a job listing to Supabase and return the saved record with id."""
    client = get_supabase_client()
    # Assuming url is unique for jobs
    result = client.table("jobs").upsert(job, on_conflict="url").execute()
    return result.data[0] if result.data else job


def save_student_profile(student_id: str, profile_data: dict) -> None:
    """Save student profile data (skill graph, domain scores, etc.) to Supabase."""
    client = get_supabase_client()
    client.table("student_profiles").upsert({
        "student_id": student_id,
        **profile_data
    }, on_conflict="student_id").execute()


def save_job_embedding(job_id: str, embedding: list[float]) -> None:
    """Save a job listing's 768-dim embedding to Supabase pgvector."""
    client = get_supabase_client()
    client.table("job_embeddings").upsert({
        "job_id": job_id,
        "embedding": embedding
    }).execute()


def search_similar_jobs(embedding: list[float], threshold: float = 0.6, top_k: int = 15) -> list[dict]:
    """Search for semantically similar jobs using pgvector."""
    client = get_supabase_client()
    result = client.rpc("match_jobs", {
        "query_embedding": embedding,
        "match_threshold": threshold,
        "match_count": top_k
    }).execute()
    return result.data


def save_job_match(match: dict) -> None:
    """Save a student-job match to Supabase."""
    client = get_supabase_client()
    client.table("job_matches").upsert(match, on_conflict="student_id,job_id").execute()


def save_resume_version(student_id: str, job_id: str, version: dict) -> dict:
    """Save a tailored resume version to Supabase."""
    client = get_supabase_client()
    record = {
        "student_id": student_id,
        "job_id": job_id,
        **version,
    }
    # resume_versions doesn't have a simple unique constraint besides id, 
    # but we can use student_id, job_id if we want only one version per job per student
    result = client.table("resume_versions").upsert(record, on_conflict="student_id,job_id").execute()
    return result.data[0] if result.data else record


def save_skill_gap(student_id: str, gap_data: dict) -> None:
    """Save skill gap analysis to Supabase."""
    client = get_supabase_client()
    client.table("skill_gaps").upsert({
        "student_id": student_id,
        **gap_data,
    }, on_conflict="student_id").execute()


def save_interview_session(student_id: str, session_data: dict) -> dict:
    """Save an interview prep or mock session to Supabase."""
    client = get_supabase_client()
    record = {"student_id": student_id, **session_data}
    result = client.table("interview_sessions").insert(record).execute()
    return result.data[0] if result.data else record


def save_referral(student_id: str, referral_data: dict) -> None:
    """Save a referral strategy to Supabase."""
    client = get_supabase_client()
    client.table("referrals").insert({
        "student_id": student_id,
        "company": referral_data.get("company"),
        "target_role": referral_data.get("target_role"),
        "connection_type": ", ".join(referral_data.get("connection_types", [])),
        "outreach_templates": referral_data.get("outreach_templates"),
        "referral_pathway": referral_data.get("referral_pathway"),
    }).execute()


def save_career_strategy(student_id: str, strategy_data: dict) -> None:
    """Save career strategy to Supabase."""
    client = get_supabase_client()
    focus = strategy_data.get("focusRecommendation")
    
    client.table("career_strategies").upsert({
        "student_id": student_id,
        "target_companies": strategy_data.get("targetCompanies"),
        "focus_recommendation": focus,
        "placement_probability": strategy_data.get("placementProbability"),
        "milestones": strategy_data.get("milestones"),
        "skill_gaps": strategy_data.get("skillGaps"),
        "learning_recommendations": strategy_data.get("learningRecommendations"),
        "market_insights": strategy_data.get("marketInsights"),
        "package_projection": strategy_data.get("packageProjection"),
    }, on_conflict="student_id").execute()


def get_job_matches(student_id: str) -> list[dict]:
    """Fetch job matches for a student."""
    client = get_supabase_client()
    result = client.table("job_matches").select("*").eq("student_id", student_id).execute()
    return result.data or []


def get_applications(student_id: str) -> list[dict]:
    """Fetch applications for a student."""
    client = get_supabase_client()
    result = client.table("applications").select("*").eq("student_id", student_id).execute()
    return result.data or []


def get_skill_gaps(student_id: str) -> Optional[dict]:
    """Fetch skill gap report for a student."""
    client = get_supabase_client()
    result = (
        client.table("skill_gaps")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_interview_sessions(student_id: str) -> list[dict]:
    """Fetch interview sessions for a student."""
    client = get_supabase_client()
    result = (
        client.table("interview_sessions")
        .select("*")
        .eq("student_id", student_id)
        .execute()
    )
    return result.data or []


def get_career_strategy(student_id: str) -> Optional[dict]:
    """Fetch career strategy for a student."""
    client = get_supabase_client()
    result = (
        client.table("career_strategies")
        .select("*")
        .eq("student_id", student_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_resume_versions(student_id: str) -> list[dict]:
    """Fetch resume versions for a student."""
    client = get_supabase_client()
    result = (
        client.table("resume_versions")
        .select("*")
        .eq("student_id", student_id)
        .execute()
    )
    return result.data or []


def mark_analysis_complete(student_id: str, completed_agents: list[str]) -> None:
    """Mark the full analysis pipeline as completed."""
    client = get_supabase_client()
    client.table("analysis_status").upsert({
        "student_id": student_id,
        "current_agent": "tracking_agent",
        "completed_agents": completed_agents,
        "percentage": 100,
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def mark_analysis_failed(student_id: str, error: str) -> None:
    """Mark the analysis pipeline as failed."""
    client = get_supabase_client()
    try:
        client.table("analysis_status").upsert({
            "student_id": student_id,
            "status": "failed",
            "current_agent": "error",
            "percentage": 0,
            "error_message": error,
        }).execute()
    except Exception as e:
        # Fallback if error_message column is not yet created in the database
        logger.warning(f"Could not update error_message column, falling back to current_agent. Error: {e}")
        client.table("analysis_status").upsert({
            "student_id": student_id,
            "status": "failed",
            "current_agent": f"ERROR: {error[:200]}",
            "percentage": 0,
        }).execute()
