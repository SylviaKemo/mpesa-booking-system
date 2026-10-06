import pytest

from app.services.phone import InvalidPhoneNumber, normalise


@pytest.mark.parametrize(
    "raw",
    [
        "0712 345 678",
        "0712345678",
        "+254712345678",
        "254712345678",
        "712345678",
        "+254 (712) 345-678",
    ],
)
def test_every_format_a_client_might_type_normalises_the_same(raw: str) -> None:
    """M-Pesa needs one shape, however the client typed it."""
    assert normalise(raw) == "254712345678"


def test_airtel_prefix_is_accepted() -> None:
    assert normalise("0112345678") == "254112345678"


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "0812345678", "071234567", "07123456789", "abc", "254812345678"],
)
def test_a_number_that_cannot_receive_mpesa_is_refused(raw: str) -> None:
    """Refusing here beats discovering it when the deposit request fails."""
    with pytest.raises(InvalidPhoneNumber):
        normalise(raw)
