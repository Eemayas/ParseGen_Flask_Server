from flask import Flask, request, jsonify
from flask_cors import CORS
from cannonical_lr_parser import CanonicalLRParser

app = Flask(__name__)
CORS(app)

# Global parser instance and current grammar
parser = None
current_grammar = None


def sets_to_lists(data):
    """Converts sets in nested structures to lists for JSON serialization."""
    if isinstance(data, dict):
        return {k: sets_to_lists(v) for k, v in data.items()}
    elif isinstance(data, set):
        return list(data)
    return data


def initialize_parser_if_needed(grammar):
    """Initializes the parser if it's not already initialized or if the grammar has changed."""
    global parser, current_grammar
    formatted_grammar = [(item[0], item[1]) for item in grammar]
    if not parser or formatted_grammar != current_grammar:
        parser = CanonicalLRParser(formatted_grammar)
        current_grammar = formatted_grammar


@app.route("/", methods=["GET"])
def home():
    return "Welcome to the Flask Server!"


@app.route("/api", methods=["GET"])
def api():
    return jsonify({"message": "Hello, World!", "status": "success"})


# Route to initialize the parser with a given grammar
@app.route("/initialize", methods=["POST"])
def initialize_parser():
    try:
        grammar = request.json.get("grammar", [])
        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400

        initialize_parser_if_needed(grammar)
        return jsonify(
            {"message": "Parser initialized successfully", "status": "success"}
        )
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


# Route to compute FIRST and FOLLOW sets for the grammar
@app.route("/first-follow-sets", methods=["POST"])
def get_first_follow_sets():
    try:
        grammar = request.json.get("grammar", [])
        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400

        initialize_parser_if_needed(grammar)

        result = {
            "FIRST": sets_to_lists(parser.first_sets),
            "FOLLOW": sets_to_lists(parser.follow_sets),
        }
        return jsonify(result)
    except Exception as e:
        return (
            jsonify({"error": f"Error fetching FIRST and FOLLOW sets: {str(e)}"}),
            500,
        )


# Route to compute the canonical collection of LR(1) items
@app.route("/canonical_collection", methods=["POST"])
def get_canonical_collection_sets():
    try:
        grammar = request.json.get("grammar", [])
        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400

        initialize_parser_if_needed(grammar)

        # Serialize the canonical collection and transitions
        canonical_collection_serialized = [
            {
                f"I{i}": {
                    "items": [str(item) for item in state],
                    "transitions": {
                        symbol: f"I{parser.goto_table[(i, symbol)]}"
                        for symbol in parser.non_terminals + parser.terminals
                        if (i, symbol) in parser.goto_table
                    },
                }
            }
            for i, state in enumerate(parser.canonical_collection)
        ]

        return jsonify({"canonical_collection": canonical_collection_serialized})
    except Exception as e:
        return (
            jsonify({"error": f"Error fetching canonical collection sets: {str(e)}"}),
            500,
        )


# Route to generate parsing tables
@app.route("/parsing_tables", methods=["POST"])
def get_parsing_tables():
    try:
        grammar = request.json.get("grammar", [])
        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400

        initialize_parser_if_needed(grammar)

        # Generate headers and rows for parsing tables
        terminals = list(parser.terminals) + ["$"]
        non_terminals = [nt for nt in parser.non_terminals if nt != "S'"]

        headers = ["State"] + terminals + non_terminals
        rows = [
            {
                "State": state,
                **{
                    symbol: parser.action_table.get((state, symbol), None)
                    for symbol in terminals
                },
                **{
                    symbol: parser.goto_table.get((state, symbol), None)
                    for symbol in non_terminals
                },
            }
            for state in range(len(parser.canonical_collection))
        ]

        return jsonify({"headers": headers, "rows": rows})
    except Exception as e:
        return jsonify({"error": f"Error fetching parsing tables: {str(e)}"}), 500


# Route to parse an input string using the grammar
@app.route("/parse", methods=["POST"])
def parse_input():
    try:
        grammar = request.json.get("grammar", [])
        input_string = request.json.get("input_string", "")

        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400
        if not isinstance(input_string, str):
            return jsonify({"error": "Input string must be a valid string"}), 400

        initialize_parser_if_needed(grammar)

        input_tokens = input_string.split() + ["$"]
        stack = [(0, "$")]
        input_pos = 0
        parse_steps = []

        while True:
            current_state = stack[-1][0]
            current_input = input_tokens[input_pos]

            # Fetch action from parsing table
            action_tuple = parser.action_table.get((current_state, current_input))
            if not action_tuple:
                return jsonify(
                    {
                        "success": False,
                        "error": f"Parsing error at position {input_pos}",
                        "steps": parse_steps,
                    }
                )

            action, value = action_tuple
            parse_steps.append(
                {
                    "stack": str(stack),
                    "input": " ".join(input_tokens[input_pos:]),
                    "action": f"{action} {value}",
                }
            )

            if action == "shift":
                stack.append((value, current_input))
                input_pos += 1
            elif action == "reduce":
                production = parser.grammar[value]
                for _ in range(len(production[1])):
                    stack.pop()
                goto_state = parser.goto_table[(stack[-1][0], production[0])]
                stack.append((goto_state, production[0]))
            elif action == "accept":
                return jsonify({"success": True, "steps": parse_steps})
    except Exception as e:
        return jsonify({"error": f"Error during parsing: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
