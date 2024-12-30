from lr_item import LRItem
from tabulate import tabulate


class CanonicalLRParser:
    def __init__(self, grammar: list[tuple[str, list[str]]]):
        self.grammar: list[tuple[str, list[str]]] = grammar
        self.terminals = []
        self.non_terminals = []
        self.first_sets: dict[str, set] = {}
        self.follow_sets: dict[str, set] = {}
        self.canonical_collection: list[LRItem] = []
        self.goto_table = {}
        self.action_table = {}
        self.goto_and_action_table = {}
        self.initialize_grammar()
        self.compute_first_sets()
        self.compute_follow_sets()

        self.display_grammar()
        print(self.get_first_and_follow_sets_table())

        self.build_canonical_collection()

        self.build_parsing_table()

        self.print_parsing_tables()

    def get_first_sets_table(self):
        headers = ["Symbol", "First"]
        data: list[tuple[str, set[str]]] = []
        for symbol, symbols in self.first_sets.items():
            data.append((symbol, symbols))

        return tabulate(data, headers=headers, tablefmt="simple_grid")

    def get_follow_sets_table(self):
        headers = ["Symbol", "Follow"]
        data: list[tuple[str, set[str]]] = []
        for symbol, symbols in self.follow_sets.items():
            data.append((symbol, symbols))

        return tabulate(data, headers=headers, tablefmt="simple_grid")

    def get_first_and_follow_sets_table(self):
        headers = ["Symbol", "First", "Follow"]
        data: list[tuple[str, set[str], set[str]]] = []
        for symbol, symbols in self.first_sets.items():
            follow_set_val = self.follow_sets.get(
                symbol, " "
            )  # use space for non-terminals
            data.append((symbol, symbols, follow_set_val))

        return tabulate(data, headers=headers, tablefmt="simple_grid")

    def display_grammar(self):
        for symbol, production in self.grammar:
            print(f"{symbol} → {''.join(production)}")

    def initialize_grammar(self):
        # Add augmented production S' → S
        self.grammar.insert(0, ("S'", ["S"]))

        # identify the non-terminals
        # all items which appear in the left side are non-terminals
        for prod in self.grammar:
            if prod[0] not in self.non_terminals:
                self.non_terminals.append(prod[0])

        # Identify terminals
        for prod in self.grammar:
            for symbol in prod[1]:
                if symbol not in self.non_terminals:
                    if symbol not in self.terminals:
                        self.terminals.append(symbol)

    def compute_first_sets(self):
        # Initialize FIRST sets
        for symbol in self.non_terminals + self.terminals:
            self.first_sets[symbol] = set()
            if symbol in self.terminals:
                self.first_sets[symbol].add(symbol)

        while True:
            updated = False
            for prod in self.grammar:
                left = prod[0]
                right = prod[1]

                # For empty productions
                if not right:
                    if "ε" not in self.first_sets[left]:
                        self.first_sets[left].add("ε")
                        updated = True
                    continue

                # For each symbol in the right-hand side
                curr_first = set()
                all_nullable = True

                for symbol in right:
                    symbol_first = self.first_sets[symbol].copy()
                    if "ε" in symbol_first:
                        symbol_first.remove("ε")
                        curr_first.update(symbol_first)
                    else:
                        curr_first.update(symbol_first)
                        all_nullable = False
                        break

                if all_nullable:
                    curr_first.add("ε")

                if not curr_first.issubset(self.first_sets[left]):
                    self.first_sets[left].update(curr_first)
                    updated = True

            if not updated:
                break

    def compute_follow_sets(self):
        # Initialize FOLLOW sets
        for non_terminal in self.non_terminals:
            self.follow_sets[non_terminal] = set()

        # Add $ to start symbol's FOLLOW set
        self.follow_sets["S'"].add("$")

        while True:
            updated = False
            for prod in self.grammar:
                left = prod[0]
                right = prod[1]

                for i, symbol in enumerate(right):
                    if symbol in self.non_terminals:
                        # Get everything that can follow this symbol in the production
                        remaining = right[i + 1 :]
                        first_of_remaining = set()

                        if remaining:
                            all_nullable = True
                            for rem_symbol in remaining:
                                symbol_first = self.first_sets[rem_symbol].copy()
                                if "ε" in symbol_first:
                                    symbol_first.remove("ε")
                                else:
                                    all_nullable = False
                                first_of_remaining.update(symbol_first)
                                if not all_nullable:
                                    break

                            # Add computed FIRST set to FOLLOW set
                            if not first_of_remaining.issubset(
                                self.follow_sets[symbol]
                            ):
                                self.follow_sets[symbol].update(first_of_remaining)
                                updated = True

                            # If all remaining symbols can derive ε, add FOLLOW(left) to FOLLOW(symbol)
                            if all_nullable:
                                if not self.follow_sets[left].issubset(
                                    self.follow_sets[symbol]
                                ):
                                    self.follow_sets[symbol].update(
                                        self.follow_sets[left]
                                    )
                                    updated = True
                        else:
                            # If symbol is at the end, add FOLLOW(left) to FOLLOW(symbol)
                            if not self.follow_sets[left].issubset(
                                self.follow_sets[symbol]
                            ):
                                self.follow_sets[symbol].update(self.follow_sets[left])
                                updated = True

            if not updated:
                break

    def compute_first_of_string(self, symbols: list[str]):
        all_nullable = True
        first_set: set[str] = set()
        for symbol in symbols:
            if symbol == "$":  # for handling look ahead conditions
                all_nullable = False
                first_set.update(symbol)
            elif "ε" in self.first_sets[symbol]:
                first_set.update(self.first_sets[symbol] - {"ε"})
            else:
                all_nullable = False
                first_set.update(self.first_sets[symbol])

            if not all_nullable:
                break
        return first_set

    def closure(self, items: set[LRItem]):
        closure_set = items.copy()

        while True:
            new_items = set()
            for item in closure_set:
                # If dot is not at the end
                if item.dot_position < len(item.production[1]):
                    symbol_after_dot = item.production[1][item.dot_position]
                    # If symbol after dot is a non-terminal
                    if symbol_after_dot in self.non_terminals:
                        # Get the rest of the string after dot
                        beta = list(item.production[1][item.dot_position + 1 :])

                        # For each production with symbol_after_dot on the left
                        for prod in self.grammar:
                            if prod[0] == symbol_after_dot:
                                # Calculate lookahead for this new item
                                new_lookahead = set()
                                # If β is empty, lookahead is the same as the original item
                                if not beta:
                                    new_lookahead.update(item.lookahead)
                                else:
                                    # Compute FIRST(β)
                                    first_beta = self.compute_first_of_string(beta)
                                    # If β →* ε, include the lookahead of the original item
                                    if "ε" in first_beta:
                                        new_lookahead.update(item.lookahead)
                                        first_beta.remove("ε")
                                    new_lookahead.update(first_beta)
                                new_item = LRItem((prod[0], prod[1]), 0, new_lookahead)
                                if new_item not in closure_set:
                                    new_items.add(new_item)

            if not new_items:
                break

            closure_set.update(new_items)

        return closure_set

    def goto(self, items: set[LRItem], symbol: str):
        goto_set = set()
        for item in items:
            if (
                item.dot_position < len(item.production[1])
                and item.production[1][item.dot_position] == symbol
            ):
                new_item = LRItem(
                    item.production, item.dot_position + 1, item.lookahead
                )
                goto_set.add(new_item)

        return self.closure(goto_set) if goto_set else set()

    def build_canonical_collection(self):
        # Start with initial item [S' → •S, $]
        initial_item = LRItem((self.grammar[0][0], self.grammar[0][1]), 0, {"$"})
        initial_state = self.closure({initial_item})

        self.canonical_collection = [initial_state]
        symbols = self.non_terminals + self.terminals

        # Build the collection
        state_index = 0
        while state_index < len(self.canonical_collection):
            current_state = self.canonical_collection[state_index]

            for symbol in symbols:
                goto_set = self.goto(current_state, symbol)

                if goto_set:
                    if goto_set not in self.canonical_collection:
                        self.canonical_collection.append(goto_set)
                    goto_state_index = self.canonical_collection.index(goto_set)
                    if symbol in self.non_terminals:
                        self.goto_table[(state_index, symbol)] = goto_state_index
                    elif symbol in self.terminals:
                        self.action_table[(state_index, symbol)] = goto_state_index
                    self.goto_and_action_table[(state_index, symbol)] = goto_state_index

            state_index += 1

        for i, state in enumerate(self.canonical_collection):
            print(f"\nState I{i}:")
            for item in state:
                print(item)

    def print_parsing_tables(self):
        # Get headers and data for ACTION table
        terminals = list(self.terminals) + ["$"]
        action_headers = ["State"] + terminals
        action_rows = []

        # Get headers and data for GOTO table
        non_terminals = [nt for nt in self.non_terminals if nt != "S'"]

        goto_headers = non_terminals
        goto_rows = []

        max_state = len(self.canonical_collection) - 1

        # Build combined rows
        for state in range(max_state + 1):
            # Action part
            action_row = [state]
            for symbol in terminals:
                action = self.action_table.get((state, symbol), "")
                if isinstance(action, tuple):
                    action_row.append(action)
                else:
                    action_row.append(str(action) if action != "" else "")

            # Goto part
            goto_row = []
            for symbol in non_terminals:
                goto_state = self.goto_table.get((state, symbol), "")
                goto_row.append(goto_state)

            # Combine rows
            combined_row = action_row + ["||"] + goto_row
            action_rows.append(combined_row)

        # Combine headers
        combined_headers = action_headers + ["||"] + goto_headers

        print("\nParsing Tables (Action | Goto):")
        print(tabulate(action_rows, headers=combined_headers, tablefmt="simple_grid"))

    def build_parsing_table(self):
        for i, state in enumerate(self.canonical_collection):
            for item in state:
                # Case 1: Shift action
                if (
                    item.dot_position < len(item.production[1])
                    and item.production[1][item.dot_position] in self.terminals
                ):
                    symbol = item.production[1][item.dot_position]
                    if (i, symbol) in self.goto_table:
                        self.action_table[(i, symbol)] = (
                            "shift",
                            self.goto_table[(i, symbol)],
                        )

                # Case 2: Reduce action
                elif item.dot_position == len(item.production[1]):
                    for lookahead in item.lookahead:
                        if item.production[0] == "S'":  # Accept
                            self.action_table[(i, "$")] = ("accept", None)
                        else:
                            prod_index = self.grammar.index(item.production)
                            self.action_table[(i, lookahead)] = ("reduce", prod_index)

    # def parse(self, input_string):
    #     # Add end marker to input
    #     input_tokens = input_string.split()
    #     input_tokens.append("$")

    #     # Initialize stack with state 0
    #     stack = [(0, "$")]
    #     input_pos = 0

    #     while True:
    #         current_state = stack[-1][0]
    #         current_input = input_tokens[input_pos]

    #         if (current_state, current_input) not in self.action_table:
    #             raise ValueError(f"Parsing error at position {input_pos}")

    #         action, value = self.action_table[(current_state, current_input)]

    #         if action == "shift":
    #             stack.append((value, current_input))
    #             input_pos += 1
    #         elif action == "reduce":
    #             production = self.grammar[value]
    #             # Pop |β| symbols off the stack
    #             for _ in range(len(production[1])):
    #                 stack.pop()
    #             # Go to state found in goto table
    #             prev_state = stack[-1][0]
    #             goto_state = self.goto_table[(prev_state, production[0])]
    #             stack.append((goto_state, production[0]))
    #         elif action == "accept":
    #             return True

    #         print(f"Stack: {stack}")
    #         print(f"Input: {' '.join(input_tokens[input_pos:])}")
    #         print(f"Action: {action} {value}\n")
