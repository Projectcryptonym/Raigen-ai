from flask import Blueprint, jsonify
from plan_builder import generate_30_day_plan

plan_bp = Blueprint("plan", __name__)

@plan_bp.route("/plan/<user_id>", methods=["GET"])
def run_plan(user_id):
    result = generate_30_day_plan(user_id)
    return jsonify(result)
