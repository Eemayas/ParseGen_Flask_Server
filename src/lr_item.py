class LRItem:
    def __init__(self, production, dot_position, lookahead=None):
        self.production = tuple(production)  # (left_side, right_side)
        self.dot_position = dot_position
        self.lookahead = set(lookahead) if lookahead else set()

    def __str__(self):
        right = list(self.production[1])
        right.insert(self.dot_position, "•")
        return f"{self.production[0]} → {' '.join(right)}, {'/'.join(self.lookahead)}"

    def __eq__(self, other):
        return (
            self.production == other.production
            and self.dot_position == other.dot_position
            and self.lookahead == other.lookahead
        )

    @staticmethod
    def convert_rhs_to_tuple(single_production):
        return (single_production[0], tuple(single_production[1]))

    def __hash__(self):
        return hash(
            (
                self.convert_rhs_to_tuple(self.production),
                self.dot_position,
                frozenset(self.lookahead),
            )
        )


if __name__ == "__main__":

    productions = [("L", ["*", "R"]), ("R", ["L"])]

    lr_item_1 = LRItem(productions[0], 0, None)
    lr_item_1_diff_dot_pos = LRItem(productions[0], 1, None)
    lr_item_2 = LRItem(productions[1], 1, None)

    lr_item_3 = LRItem(productions[1], 1, ["$"])
    lr_item_3_diff_look_ahead = LRItem(productions[1], 1, ["="])

    duplicate_lr_item_3 = LRItem(productions[1], 1, ["$"])

    multiple_lookahead = LRItem(productions[1], 1, ["$", "="])

    assert lr_item_1 != lr_item_2
    assert lr_item_1 == lr_item_1
    assert lr_item_1 != lr_item_1_diff_dot_pos
    assert lr_item_2 != lr_item_3
    assert lr_item_3_diff_look_ahead != lr_item_3

    lr_items = set([lr_item_3])

    assert duplicate_lr_item_3 in lr_items

    print("LR Item 1 (LRItem(productions[0], 0, None)):\n", lr_item_1, "\n")
    print(
        "LR Item 1 with different dot position (LRItem(productions[1], 1, None)):\n",
        lr_item_1_diff_dot_pos,
        "\n",
    )
    print("LR Item 2 (LRItem(productions[1], 1, None)):\n", lr_item_2, "\n")
    print("LR Item 3 (LRItem(productions[1], 1, {'$'}))\n:", lr_item_3, "\n")
    print("LR Item 3 with different lookahead:\n", lr_item_3_diff_look_ahead, "\n")
    print(
        "Duplicate LR Item 3 (LRItem(productions[1], 1, ['$'])):\n",
        duplicate_lr_item_3,
        "\n",
    )
    print("Set of LR Items containing LR Item 3:\n", lr_items, "\n")
    print(
        "Multiple lookahead LR Item (LRItem(productions[1], 1, {'$', '='})):\n",
        multiple_lookahead,
        "\n",
    )

    print("LR Item 1 is not equal to LR Item 2:", lr_item_1 != lr_item_2, "\n")
    print("LR Item 1 is equal to itself:", lr_item_1 == lr_item_1, "\n")
    print(
        "LR Item 1 is not equal to LR Item 1 with different dot position:",
        lr_item_1 != lr_item_1_diff_dot_pos,
        "\n",
    )
    print("LR Item 2 is not equal to LR Item 3:", lr_item_2 != lr_item_3, "\n")
    print(
        "LR Item 3 with different lookahead is not equal to LR Item 3:",
        lr_item_3_diff_look_ahead != lr_item_3,
        "\n",
    )
    print(
        "Duplicate LR Item 3 is in the set of LR Items:",
        duplicate_lr_item_3 in lr_items,
        "\n",
    )
