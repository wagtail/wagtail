
import pytest

from glom import glom, Spec, T, S


def test_spec():
    assert glom(5, T) == 5  # check assumption about echo behavior
    echo = Spec(T)
    assert echo.glom(5) == 5
    assert glom(5, echo) == 5
    echo2 = Spec(echo)
    assert echo2.glom(5) == 5

    with pytest.raises(TypeError, match='expected spec to be'):
        glom({}, object())
    return

def test_scope_spec():
    scope_spec = Spec(S)
    assert scope_spec.glom(5, scope={'cat': 1})['cat'] == 1
    cat_scope_spec = Spec(scope_spec, scope={'cat': 1})
    assert 'cat' in repr(cat_scope_spec)
    assert cat_scope_spec.glom(5)['cat'] == 1

    # test that Spec overrides the scope for its sub-tree
    assert glom(5, cat_scope_spec, scope={'cat': 2})['cat'] == 1
