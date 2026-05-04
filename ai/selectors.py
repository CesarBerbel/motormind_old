from django.db.models import Count

from .models import AIPromptTemplate, AIRequest, AIRequestStatus, AIResponse, AIUsageLog


def get_active_prompt_templates():
    return AIPromptTemplate.objects.filter(is_active=True).order_by(
        "use_case", "code", "-version"
    )


def get_recent_ai_requests(limit=20):
    return AIRequest.objects.select_related("user", "prompt_template").order_by(
        "-created_at"
    )[:limit]


def get_recent_ai_responses(limit=20):
    return AIResponse.objects.select_related(
        "request", "request__user", "request__prompt_template"
    ).order_by("-created_at")[:limit]


def get_ai_usage_summary():
    total_requests = AIRequest.objects.count()
    completed_requests = AIRequest.objects.filter(
        status=AIRequestStatus.COMPLETED
    ).count()
    failed_requests = AIRequest.objects.filter(status=AIRequestStatus.FAILED).count()
    by_use_case = (
        AIRequest.objects.values("use_case")
        .annotate(total=Count("id"))
        .order_by("use_case")
    )
    return {
        "total_requests": total_requests,
        "completed_requests": completed_requests,
        "failed_requests": failed_requests,
        "by_use_case": by_use_case,
        "recent_logs": AIUsageLog.objects.select_related("user").order_by(
            "-created_at"
        )[:10],
    }
