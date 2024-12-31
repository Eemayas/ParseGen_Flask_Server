from flask import Flask, request, jsonify
from cannonical_lr_parser import CanonicalLRParser
from lr_item import LRItem

app = Flask(__name__)
parser = None  # Global parser instance


def sets_to_lists(data):
    if isinstance(data, dict):
        return {k: sets_to_lists(v) for k, v in data.items()}
    elif isinstance(data, set):
        return list(data)
    return data


@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Flask Server!"


@app.route("/api", methods=["GET"])
def api():
    return jsonify({"message": "Hello, World!", "status": "success"})


@app.route("/initialize", methods=["POST"])
def initialize_parser():
    global parser
    try:
        # Get the grammar from the request body
        grammar = request.json.get("grammar", [])

        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400
        formatted_gramnmer = [(item[0], item[1]) for item in grammar]
        # Initialize parser
        parser = CanonicalLRParser(formatted_gramnmer)

        return jsonify(
            {"message": "Parser initialized successfully", "status": "success"}
        )
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


# Endpoint to get the first and follow sets
@app.route("/first-follow-sets", methods=["POST"])
def get_first_follow_sets():
    global parser
    try:
        if not parser:
            # Get the grammar from the request body
            grammar = request.json.get("grammar", [])

            if not grammar:
                return jsonify({"error": "Grammar is required"}), 400
            formatted_gramnmer = [(item[0], item[1]) for item in grammar]
            # Initialize parser
            parser = CanonicalLRParser(formatted_gramnmer)

        # Convert sets to lists for JSON serialization
        result = {
            "FIRST": sets_to_lists(parser.first_sets),
            "FOLLOW": sets_to_lists(parser.follow_sets),
        }

        return jsonify(result)
    except Exception as e:
        return (
            jsonify({"error": f"Error fetching FIRST and FOLLOW sets: {str(e)}"}),
            500,
        )  # Endpoint to get the first and follow sets


@app.route("/canonical_collection", methods=["POST"])
def get_canonical_collection_sets():
    global parser
    try:
        if not parser:
            # Get the grammar from the request body
            grammar = request.json.get("grammar", [])

            if not grammar:
                return jsonify({"error": "Grammar is required"}), 400
            formatted_grammar = [(item[0], item[1]) for item in grammar]
            # Initialize parser
            parser = CanonicalLRParser(formatted_grammar)

        # Debugging: Convert sets to lists for JSON serialization
        canonical_collection_serialized = []
        for item in parser.canonical_collection:
            if isinstance(item, set):
                # Flatten the set and convert each LRItem to a serializable format
                canonical_collection_serialized.extend(
                    [
                        {
                            "production": lr_item.production,
                            "dot_position": lr_item.dot_position,
                            "lookahead": list(lr_item.lookahead),
                        }
                        for lr_item in item
                    ]
                )
            elif isinstance(item, LRItem):
                canonical_collection_serialized.append(
                    {
                        "production": item.production,
                        "dot_position": item.dot_position,
                        "lookahead": list(item.lookahead),
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "error": f"Unexpected item in canonical_collection: {type(item)}"
                        }
                    ),
                    500,
                )

        return jsonify({"canonical_collection": canonical_collection_serialized})
    except Exception as e:
        return (
            jsonify({"error": f"Error fetching canonical collection sets: {str(e)}"}),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True)
