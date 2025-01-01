from flask import Flask, request, jsonify
from cannonical_lr_parser import CanonicalLRParser
from lr_item import LRItem
from flask_cors import CORS
from tabulate import tabulate

app = Flask(__name__)
CORS(app)

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
    global parser, current_grammar
    try:
        # Get the grammar from the request body
        grammar = request.json.get("grammar", [])

        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400

        # Convert the grammar to a tuple for easier comparison
        formatted_grammar = [(item[0], item[1]) for item in grammar]

        # Check if parser needs reinitialization
        if not parser or formatted_grammar != current_grammar:
            # Initialize parser with new grammar
            parser = CanonicalLRParser(formatted_grammar)
            current_grammar = formatted_grammar  # Update the current grammar

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
    global parser, current_grammar  # Track the parser and the last used grammar
    try:
        # Get the grammar from the request body
        grammar = request.json.get("grammar", [])

        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400

        # Convert the grammar to a tuple for easier comparison
        formatted_grammar = [(item[0], item[1]) for item in grammar]

        # Reinitialize the parser if it doesn't exist or if the grammar has changed
        if not parser or formatted_grammar != current_grammar:
            parser = CanonicalLRParser(formatted_grammar)
            current_grammar = formatted_grammar

        # Serialize the canonical collection
        canonical_collection_serialized = []
        for i, state in enumerate(parser.canonical_collection):
            state_info = {
                f"I{i}": {
                    "items": [str(item) for item in state],
                    "transitions": {
                        symbol: f"I{parser.goto_table[(i, symbol)]}"
                        for symbol in parser.non_terminals + parser.terminals
                        if (i, symbol) in parser.goto_table
                    },
                }
            }
            canonical_collection_serialized.append(state_info)

        return jsonify({"canonical_collection": canonical_collection_serialized})

    except Exception as e:
        return (
            jsonify({"error": f"Error fetching canonical collection sets: {str(e)}"}),
            500,
        )


@app.route("/parsing_tables", methods=["POST"])
def get_parsing_tables():
    global parser, current_grammar  # Track the parser and the last used grammar
    try:
        # Get the grammar from the request body
        grammar = request.json.get("grammar", [])

        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400

        # Convert the grammar to a tuple for easier comparison
        formatted_grammar = [(item[0], item[1]) for item in grammar]

        # Reinitialize the parser if it doesn't exist or if the grammar has changed
        if not parser or formatted_grammar != current_grammar:
            parser = CanonicalLRParser(formatted_grammar)
            current_grammar = formatted_grammar

        # Extract terminals and non-terminals
        terminals = list(parser.terminals) + ["$"]
        non_terminals = [nt for nt in parser.non_terminals if nt != "S'"]

        # Prepare headers for the action and goto tables
        action_headers = ["State"] + terminals
        goto_headers = non_terminals
        combined_headers = action_headers + goto_headers

        # Generate rows for the tables
        action_rows = []
        goto_rows = []
        combined_rows = []

        max_state = len(parser.canonical_collection) - 1

        for state in range(max_state + 1):
            # Populate action table row
            action_row = {"State": state}
            for symbol in terminals:
                action = parser.action_table.get((state, symbol), "")
                action_row[symbol] = action if action else None
            action_rows.append(action_row)

            # Populate goto table row
            goto_row = {"State": state}
            for symbol in non_terminals:
                goto_state = parser.goto_table.get((state, symbol), "")
                goto_row[symbol] = goto_state if goto_state else None
            goto_rows.append(goto_row)

            # Populate combined table row
            combined_row = {"State": state}
            for symbol in terminals:
                action = parser.action_table.get((state, symbol), "")
                combined_row[symbol] = action if action else None
            for symbol in non_terminals:
                goto_state = parser.goto_table.get((state, symbol), "")
                combined_row[symbol] = goto_state if goto_state else None
            combined_rows.append(combined_row)

        # Combine headers and rows into JSON format
        tables = {
            "action_table": {
                "headers": action_headers,
                "rows": action_rows,
            },
            "goto_table": {
                "headers": goto_headers,
                "rows": goto_rows,
            },
            "combined_table": {
                "headers": combined_headers,
                "rows": combined_rows,
            },
        }
        return jsonify(tables)

    except Exception as e:
        return jsonify({"error": f"Error parsing input: {str(e)}"}), 500


@app.route("/parse", methods=["POST"])
def parse_input():
    global parser, current_grammar  # Track the parser and grammar state
    try:
        # Get the grammar and input_string from the request body
        grammar = request.json.get("grammar", [])
        input_string = request.json.get("input_string", "")

        # Validate input
        if not isinstance(input_string, str):
            return jsonify({"error": "input_string must be a string"}), 400
        if not grammar:
            return jsonify({"error": "Grammar is required"}), 400
        if not input_string:
            return jsonify({"error": "input_string is required"}), 400

        # Format the grammar
        formatted_grammar = [(item[0], item[1]) for item in grammar]

        # Reinitialize the parser if grammar changes or parser is not initialized
        if not parser or formatted_grammar != current_grammar:
            parser = CanonicalLRParser(formatted_grammar)
            current_grammar = formatted_grammar

        # Add end marker to input
        input_tokens = input_string.split()
        input_tokens.append("$")

        # Initialize stack with state 0
        stack = [(0, "$")]
        input_pos = 0

        # Store parsing steps
        parse_steps = []
        headers = ["Stack", "Input", "Action"]

        while True:
            current_state = stack[-1][0]
            current_input = input_tokens[input_pos]

            if (current_state, current_input) not in parser.action_table:
                # Format current state
                stack_str = str(stack)
                input_str = " ".join(input_tokens[input_pos:])
                action_str = "error"

                # Store step
                parse_steps.append([stack_str, input_str, action_str])
                return jsonify(
                    {
                        "success": False,
                        "error": f"Parsing error at position {input_pos}",
                        "steps": [
                            {
                                "stack": stack_str,
                                "input": input_str,
                                "action": action_str,
                            }
                            for stack_str, input_str, action_str in parse_steps
                        ],
                    }
                )

            action, value = parser.action_table[(current_state, current_input)]

            # Format current state
            stack_str = str(stack)
            input_str = " ".join(input_tokens[input_pos:])
            action_str = f"{action} {value}"

            # Store step
            parse_steps.append([stack_str, input_str, action_str])

            if action == "shift":
                stack.append((value, current_input))
                input_pos += 1
            elif action == "reduce":
                production = parser.grammar[value]
                for _ in range(len(production[1])):
                    stack.pop()
                prev_state = stack[-1][0]
                goto_state = parser.goto_table[(prev_state, production[0])]
                stack.append((goto_state, production[0]))
            elif action == "accept":
                # Return final result
                return jsonify(
                    {
                        "success": True,
                        "steps": [
                            {
                                "stack": stack_str,
                                "input": input_str,
                                "action": action_str,
                            }
                            for stack_str, input_str, action_str in parse_steps
                        ],
                    }
                )
    except Exception as e:
        return jsonify({"error": f"Error during parsing: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
