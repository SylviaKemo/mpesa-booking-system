"""
Kenyan mobile numbers, stored in one canonical shape.

Clients type 0712 345 678, +254 712 345 678 or 254712345678. M-Pesa wants
254712345678, and a reminder needs to reach the same person however they typed
it, so everything is normalised on the way in.
"""

import re

_NON_DIGITS = re.compile(r"[^\d+]")

#: Safaricom and Airtel ranges are 7xx and 1xx after the country code.
_NATIONAL = re.compile(r"^0([71]\d{8})$")
_INTERNATIONAL = re.compile(r"^(?:\+?254)([71]\d{8})$")
_BARE = re.compile(r"^([71]\d{8})$")


class InvalidPhoneNumber(ValueError):
    pass


def normalise(raw: str) -> str:
    """
    Return the number as 2547XXXXXXXX / 2541XXXXXXXX.

    Raises InvalidPhoneNumber if it is not a Kenyan mobile, so an unreachable
    number is refused at the door rather than when the deposit request fails.
    """
    cleaned = _NON_DIGITS.sub("", (raw or "").strip())

    for pattern in (_NATIONAL, _INTERNATIONAL, _BARE):
        match = pattern.match(cleaned)
        if match:
            return f"254{match.group(1)}"

    raise InvalidPhoneNumber(
        "Enter a Kenyan mobile number, for example 0712 345 678."
    )
