from flask import Flask, jsonify
import importlib
import os
import sys

app = Flask(__name__)

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@app.route("/get_parsing_result", methods=["GET"])
def get_parsing_result():
    try:
        # Import the src.main module
        main_module = importlib.import_module("src.main")
        
        # Check if the main function exists
        if hasattr(main_module, "main"):
            result = main_module.main()  # Call the main function
            return jsonify({"status": "success", "result": result})
        else:
            return jsonify({"status": "error", "message": "Main function not found in main.py"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0", debug=True)
