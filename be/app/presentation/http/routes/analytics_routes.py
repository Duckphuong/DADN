from flask import Blueprint, g, jsonify, request

from app.application.common.exceptions import ApplicationError
from app.presentation.http.dependencies import get_container
from app.presentation.http.errors import map_application_error
from app.presentation.http.middleware.auth_middleware import jwt_required
from app.presentation.http.serializers.analytics_serializers import (
    serialize_analytics_trends,
)
from app.presentation.http.validators.analytics_validators import (
    validate_get_analytics_trends_request,
)


analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.get("/trends")
@jwt_required
def get_analytics_trends():
    """
    GET /api/analytics/trends

    Returns dashboard data for the requested date, or yesterday when `date`
    is omitted, for sensors owned by the authenticated user from the
    JWT access token.
    """
    try:
        query = validate_get_analytics_trends_request(
            g.current_user.id,
            requested_date=request.args.get("date"),
        )
        result = get_container().get_analytics_trends_use_case.execute(query)
        return jsonify(serialize_analytics_trends(result)), 200
    except ApplicationError as exc:
        payload, status_code = map_application_error(exc)
        return jsonify(payload), status_code
