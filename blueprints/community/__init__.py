from flask import Blueprint

community_bp = Blueprint(
    "community_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/community"
)

from . import routes  # noqa
