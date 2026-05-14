from flask import Blueprint, jsonify, request

from di.container import Container
from web.mapper.game_mapper import from_domain, game_from_dict, game_to_dict, to_domain


def create_game_blueprint(container: Container) -> Blueprint:
    blueprint = Blueprint("game", __name__)

    @blueprint.route("/game/<game_id>", methods=["POST"])
    def play_game(game_id: str):
        try:
            data = request.get_json(silent=True)
            if data is None:
                raise ValueError("Invalid JSON body.")
            web_game = game_from_dict(data, game_id)
            domain_game = to_domain(web_game)
            result = container.game_service.get_next_move(domain_game)
            response_game = from_domain(result)
            return jsonify(game_to_dict(response_game)), 200
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception:
            return jsonify({"error": "Internal server error."}), 500

    return blueprint
