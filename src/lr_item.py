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

if __name__=="__main__":

    productions = [
        ("L", ["*", "R"]),
        ("R", ["L"])
    ]

    lr_item_1 = LRItem(productions[0], 0, None)
    lr_item_1_diff_dot_pos = LRItem(productions[0], 1, None)
    lr_item_2 = LRItem(productions[1], 1, None)

    lr_item_3 = LRItem(productions[1], 1, ["$"])
    lr_item_3_diff_look_ahead = LRItem(productions[1], 1, ["="])

    assert(lr_item_1 != lr_item_2)
    assert(lr_item_1 == lr_item_1)
    assert(lr_item_1 != lr_item_1_diff_dot_pos)
    assert(lr_item_2 != lr_item_3)
    assert(lr_item_3_diff_look_ahead != lr_item_3)

    duplicate_lr_item_3 = LRItem(productions[1], 1, ["$"])
    lr_items = set([lr_item_3])

    assert(duplicate_lr_item_3 in lr_items)
