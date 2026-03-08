# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.scraper import test_extract, LIBRARIES

tools_bp = Blueprint("tools", __name__)


@tools_bp.route("/test-extract", methods=["GET", "POST"])
@login_required
def test_extract_page():
    if request.method == "POST":
        url = (request.form.get("url") or request.json.get("url") or "").strip()
        library = request.form.get("library") or request.json.get("library") or "parsel"
        selector_type = request.form.get("selector_type") or request.json.get("selector_type") or "xpath"
        selector = (request.form.get("selector") or request.json.get("selector") or "").strip()
        if not url:
            if request.is_json:
                return jsonify({"ok": False, "error": "URL obligatoriu.", "values": []}), 400
            return render_template("tools/test_extract.html", libraries=LIBRARIES, error="URL obligatoriu.")
        values, err = test_extract(url, library=library, selector_type=selector_type, selector=selector)
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            if err:
                return jsonify({"ok": False, "error": err, "values": values})
            return jsonify({"ok": True, "values": values, "count": len(values)})
        return render_template(
            "tools/test_extract.html",
            libraries=LIBRARIES,
            url=url,
            library=library,
            selector_type=selector_type,
            selector=selector,
            values=values,
            error=err,
        )
    return render_template("tools/test_extract.html", libraries=LIBRARIES)
