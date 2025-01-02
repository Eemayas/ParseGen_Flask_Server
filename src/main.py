from src.cannonical_lr_parser import CanonicalLRParser


# Example usage
def main():
    # Define the grammar
    grammar = [
    ("S", ["L", "=", "R"]),  # Assignment statement
    ("S", ["R"]),            # Expression statement
    ("R", [ "R", "*", "R"]),  # Multiplication
    ("R", ["L"]),           # R can be L
    ("L", ["id"])           # L is an identifier
]

    # Create parser
    parser = CanonicalLRParser(grammar)
    # Test string
    test_string = "id = id * id"
    print(f"Parsing string: {test_string}")
    try:
        try:
            result = parser.parse(test_string)
            print("the final all values are:")
            
            # Process first_sets_and_follow_sets
            first_follow_sets = []
            for sets_data in parser.parsing_data["first_sets_and_follow_sets"]:
                processed_sets = []
                for symbol, first_set, follow_set in sets_data:
                    processed_sets.append({
                        "symbol": symbol,
                        "first": list(first_set) if isinstance(first_set, set) else first_set,
                        "follow": list(follow_set) if isinstance(follow_set, set) else follow_set
                    })
                first_follow_sets.append(processed_sets)

            # Process canonical collection - Fixed processing
            canonical_collection = []
            for collection in parser.parsing_data["cannonical_collection"]:
                state_items = []
                for state in collection:
                    # Don't split the string representation of LRItems
                    state_items.append([item.__str__() for item in state])
                canonical_collection.append(state_items)

            # Process parsing table
            parsing_table = []
            for row in parser.parsing_data["parsing_table"]:
                processed_row = []
                for item in row:
                    if isinstance(item, tuple):
                        processed_row.append(f"{item[0]} {item[1]}")
                    else:
                        processed_row.append(str(item))
                parsing_table.append(processed_row)

            return {
                "status": "success",
                "parsing_data": {
                    "first_sets_and_follow_sets": first_follow_sets,
                    "parsing_table": parsing_table,
                    "canonical_collection": canonical_collection
                }
            }
            
        except ValueError as e:
            return {
                "status": "error",
                "message": str(e)
            }
    except ValueError as e:
        print(f"Error: {e}")

# if __name__ == "__main__":
#     main()