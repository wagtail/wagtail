from wagtail.blocks import ChoiceBlock


def test_choice_block_preserves_integer_type():
    block = ChoiceBlock(choices=[(1, "One"), (2, "Two")])

    value = block.to_python("2")

    assert value == 2
    assert isinstance(value, int)


def test_choice_block_string_choices_unchanged():
    block = ChoiceBlock(choices=[("a", "A"), ("b", "B")])

    value = block.to_python("b")

    assert value == "b"


def test_choice_block_optgroup_preserves_type():
    block = ChoiceBlock(
        choices=[
            ("Numbers", [(1, "One"), (2, "Two")]),
        ]
    )

    value = block.to_python("1")

    assert value == 1
