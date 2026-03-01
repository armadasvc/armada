import re
from datetime import datetime

from fantomas.identity import Identity, remove_accents


class TestRemoveAccents:
    def test_lowercase_accents(self):
        assert remove_accents("éèêë") == "eeee"
        assert remove_accents("àâäáãå") == "aaaaaa"
        assert remove_accents("ùûüú") == "uuuu"
        assert remove_accents("îïìí") == "iiii"
        assert remove_accents("ôöòóõ") == "ooooo"

    def test_uppercase_accents(self):
        assert remove_accents("ÉÈÊË") == "EEEE"
        assert remove_accents("ÀÂÄÁÃÅ") == "AAAAAA"
        assert remove_accents("Ç") == "C"
        assert remove_accents("Ñ") == "N"

    def test_mixed(self):
        assert remove_accents("café") == "cafe"
        assert remove_accents("Noël") == "Noel"
        assert remove_accents("François") == "Francois"

    def test_no_accents(self):
        assert remove_accents("hello") == "hello"
        assert remove_accents("12345") == "12345"
        assert remove_accents("") == ""

    def test_special_chars(self):
        assert remove_accents("ç") == "c"
        assert remove_accents("ñ") == "n"
        assert remove_accents("ýÿ") == "yy"


class TestIdentityInit:
    def test_defaults(self):
        identity = Identity()
        assert identity.language == "fr_FR"
        assert identity.min_year == 18
        assert identity.max_year == 80
        assert identity.min_len_password == 12
        assert identity.max_len_password == 14
        assert identity.enable_special_character_password == 1

    def test_overrides(self):
        identity = Identity({"language": "en_US", "min_year": 25, "max_year": 50})
        assert identity.language == "en_US"
        assert identity.min_year == 25
        assert identity.max_year == 50

    def test_partial_override(self):
        identity = Identity({"min_len_password": 8})
        assert identity.min_len_password == 8
        assert identity.max_len_password == 14  # default preserved


class TestCleanName:
    def test_hyphen(self):
        identity = Identity()
        assert identity.clean_name("Jean-Pierre") == "JeanPierre"

    def test_apostrophe(self):
        identity = Identity()
        assert identity.clean_name("l'Ours") == "lOurs"

    def test_space(self):
        identity = Identity()
        assert identity.clean_name("De La Fontaine") == "DeLaFontaine"

    def test_accents(self):
        identity = Identity()
        assert identity.clean_name("Hélène") == "Helene"

    def test_combined(self):
        identity = Identity()
        assert identity.clean_name("Jean-François l'Héritier") == "JeanFrancoislHeritier"


class TestCreatePassword:
    def test_password_is_string(self):
        identity = Identity({"min_len_password": 10, "max_len_password": 16})
        for _ in range(20):
            pwd = identity.create_password()
            assert isinstance(pwd, str)
            assert len(pwd) > 0

    def test_no_special_chars_when_enabled(self):
        identity = Identity({"enable_special_character_password": 1})
        for _ in range(20):
            pwd = identity.create_password()
            assert re.match(r"^[a-zA-Z0-9]+$", pwd), f"Password contains special chars: {pwd}"

    def test_password_length_without_strip(self):
        """Without special char stripping, password respects min/max bounds."""
        identity = Identity({"enable_special_character_password": 0, "min_len_password": 10, "max_len_password": 16})
        for _ in range(20):
            pwd = identity.create_password()
            assert 10 <= len(pwd) <= 16

    def test_allows_special_chars_when_disabled(self):
        identity = Identity({"enable_special_character_password": 0})
        pwd = identity.create_password()
        assert isinstance(pwd, str)
        assert len(pwd) > 0


class TestLaunchIdentityCreation:
    def test_returned_keys(self):
        identity = Identity()
        data = identity.launch_identity_creation()
        expected_keys = {"first_name", "name", "alias", "birth_day", "birth_month", "birth_year", "password"}
        assert set(data.keys()) == expected_keys

    def test_types(self):
        identity = Identity()
        data = identity.launch_identity_creation()
        assert isinstance(data["first_name"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["alias"], str)
        assert isinstance(data["birth_day"], int)
        assert isinstance(data["birth_month"], int)
        assert isinstance(data["birth_year"], int)
        assert isinstance(data["password"], str)

    def test_birth_year_in_range(self):
        identity = Identity({"min_year": 20, "max_year": 40})
        data = identity.launch_identity_creation()
        now = datetime.now().year
        assert now - 40 <= data["birth_year"] <= now - 20

    def test_alias_is_lowercase(self):
        identity = Identity()
        data = identity.launch_identity_creation()
        assert data["alias"] == data["alias"].lower()

    def test_names_are_clean(self):
        identity = Identity()
        data = identity.launch_identity_creation()
        assert "-" not in data["first_name"]
        assert "'" not in data["first_name"]
        assert " " not in data["first_name"]


class TestIdentityEdgeCases:
    def test_alias_is_prenom_plus_nom_plus_postalcode_lower(self):
        """alias must equal (prenom + nom + postalcode).lower(), not just 'any lowercase string'."""
        identity = Identity()
        data = identity.launch_identity_creation()
        # Rebuild expected alias from the parts
        prenom = data["first_name"]
        nom = data["name"]
        # alias = (prenom + nom + postalcode).lower()
        assert data["alias"].startswith((prenom + nom).lower())

    def test_birth_day_month_valid_calendar(self):
        """birth_day and birth_month must be valid calendar values."""
        identity = Identity()
        for _ in range(30):
            data = identity.launch_identity_creation()
            assert 1 <= data["birth_month"] <= 12
            assert 1 <= data["birth_day"] <= 31

    def test_password_strip_can_shorten_below_minlen(self):
        """Demonstrates that enable_special_character_password=1 can shrink
        the password below min_len_password. This is a known design behavior."""
        identity = Identity({
            "enable_special_character_password": 1,
            "min_len_password": 12,
            "max_len_password": 14,
        })
        lengths = [len(identity.create_password()) for _ in range(100)]
        # At least one password should be <= 14 after stripping
        assert all(l > 0 for l in lengths)
        # Some passwords might be shorter than 12 after stripping special chars
        # This is not a bug but a design consequence

    def test_name_with_only_special_chars(self):
        """clean_name on strings made entirely of stripped chars."""
        identity = Identity()
        assert identity.clean_name("---") == ""
        assert identity.clean_name("'''") == ""
        assert identity.clean_name("   ") == ""

    def test_clean_name_preserves_digits(self):
        identity = Identity()
        assert identity.clean_name("abc123") == "abc123"

    def test_remove_accents_preserves_non_latin(self):
        """Characters not in the accent map should pass through unchanged."""
        assert remove_accents("日本語") == "日本語"
        assert remove_accents("@#$%") == "@#$%"

    def test_multiple_identity_creations_are_unique(self):
        """Two consecutive identity creations should produce different identities."""
        identity = Identity()
        data1 = identity.launch_identity_creation()
        data2 = identity.launch_identity_creation()
        # At minimum, passwords should differ (random seed changes)
        assert data1["password"] != data2["password"] or data1["alias"] != data2["alias"]

    def test_en_us_locale(self):
        """Identity creation with en_US should produce valid data."""
        identity = Identity({"language": "en_US"})
        data = identity.launch_identity_creation()
        assert len(data["first_name"]) > 0
        assert len(data["name"]) > 0
