from flask import Blueprint, render_template, request
from ..models import Sermon

sermon = Blueprint("sermon", __name__)


@sermon.route("/")
def sermons():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    sermons_query = Sermon.query.order_by(Sermon.created_at.desc())

    if query:
        sermons_query = sermons_query.filter(Sermon.title.ilike(f"%{query}%"))
    if category:
        sermons_query = sermons_query.filter(Sermon.category == category)

    sermons_data = sermons_query.all()
    categories = sorted({s.category for s in Sermon.query.all()})

    return render_template(
        "sermons.html",
        sermons=sermons_data,
        query=query,
        category=category,
        categories=categories,
    )
