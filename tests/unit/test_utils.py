import pytest

from utils import is_absolute_address


class TestUtils:
    @pytest.mark.parametrize('astr, expected', (
            ('100', True),
            ('abc1', False),
            ('', False),

    ))
    def test_is_absolute_address(self, astr, expected):
        assert is_absolute_address(astr) == expected
