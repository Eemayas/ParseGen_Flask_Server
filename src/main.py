from cannonical_lr_parser import CanonicalLRParser


# Example usage
def main():
    # Define the grammar
    grammar = [
        ("S", ["L", "=", "R"]),
        ("S", ["R"]),
        ("L", ["R", "*", "R"]),
        ("L", ["id"]),
        ("R", ["L"]),
    ]

    # Create parser
    parser = CanonicalLRParser(grammar)

    # Test string
    test_string = "id = id * id"
    print(f"Parsing string: {test_string}")
    try:
        result = parser.parse(test_string)
        print(f"Parsing {'successful' if result else 'failed'}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
