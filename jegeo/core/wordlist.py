"""A small, hand-written sample of extremely common passwords.

This is intentionally short (a few hundred entries, not millions) — it
exists purely so the Hash ID and Password Audit modules can demonstrate,
against your *own* test hashes or passwords, why trivially common secrets
are unsafe. It is not a credential-stuffing wordlist and is not meant to
scale into one.
"""

_BASE_COMMON = [
    "password", "123456", "12345678", "123456789", "12345", "1234567",
    "1234567890", "qwerty", "abc123", "111111", "123123", "letmein",
    "welcome", "admin", "iloveyou", "monkey", "dragon", "master",
    "sunshine", "princess", "football", "baseball", "shadow", "superman",
    "trustno1", "passw0rd", "starwars", "whatever", "freedom", "batman",
    "hello", "login", "solo", "666666", "photoshop", "michael", "jennifer",
    "jordan", "hunter", "charlie", "ashley", "michelle", "daniel", "andrew",
    "matthew", "george", "harley", "ranger", "buster", "thomas", "robert",
    "soccer", "hockey", "killer", "george", "asshole", "computer",
    "internet", "pepper", "banana", "flower", "summer", "winter", "autumn",
    "changeme", "letmein1", "qazwsx", "zaq1zaq1", "1q2w3e4r", "1qaz2wsx",
    "q1w2e3r4", "admin123", "root", "toor", "guest", "test", "user",
    "default", "temp", "temp123", "demo", "sample",
]

_KEYBOARD_WALKS = [
    "qwertyuiop", "asdfghjkl", "zxcvbnm", "qazwsxedc", "1qaz2wsx3edc",
    "qwerty123", "asdf1234", "zxcvbn123",
]

_SUFFIXED = [f"{w}{n}" for w in ("password", "admin", "letmein", "welcome",
                                  "qwerty", "iloveyou", "dragon")
             for n in ("1", "12", "123", "1234", "!", "01", "2023", "2024",
                       "2025")]

_YEARS = [str(y) for y in range(1980, 2027)]

COMMON_PASSWORDS = sorted(set(
    _BASE_COMMON + _KEYBOARD_WALKS + _SUFFIXED + _YEARS
))
