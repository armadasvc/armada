import json
import pytest

from src.crypto import BDACrypto


class TestPadUnpad:
    def test_roundtrip(self):
        # pad() takes a string (despite the bytes type hint) because it uses chr()
        data = "Hello World"
        padded = BDACrypto.pad(data)
        assert len(padded) % 16 == 0
        unpadded = BDACrypto.unpad(padded.encode())
        assert unpadded == data.encode()

    def test_exact_block_size(self):
        data = "A" * 16
        padded = BDACrypto.pad(data)
        # Exact block should still add a full padding block
        assert len(padded) == 32

    def test_single_byte(self):
        data = "X"
        padded = BDACrypto.pad(data)
        assert len(padded) == 16

    def test_unpad_removes_correct_bytes(self):
        data = b"Hello World" + bytes([5]) * 5
        assert BDACrypto.unpad(data) == b"Hello World"


class TestEncryptDecryptRoundtrip:
    def test_roundtrip(self):
        crypto = BDACrypto("test_key_user_agent_1234567890ab")
        original_data = '{"key":"value","nested":[1,2,3]}'

        # Generate a valid salt and IV for testing
        import os
        salt = os.urandom(8).hex()
        iv = os.urandom(16).hex()

        fp_data = {"iv": iv, "s": salt, "ct": ""}
        encrypted = crypto.re_encrypt(original_data, fp_data)
        decrypted = crypto.decrypt(encrypted).decode()
        assert decrypted == original_data

    def test_roundtrip_with_json(self):
        crypto = BDACrypto("Mozilla/5.0_ua_string_key_12345")
        original = {"browser": "Chrome", "version": 120, "features": ["webgl", "canvas"]}
        original_str = json.dumps(original, separators=(",", ":"))

        import os
        salt = os.urandom(8).hex()
        iv = os.urandom(16).hex()

        fp_data = {"iv": iv, "s": salt, "ct": ""}
        encrypted = crypto.re_encrypt(original_str, fp_data)
        decrypted = crypto.decrypt(encrypted).decode()
        assert json.loads(decrypted) == original

    def test_preserves_salt_and_iv(self):
        crypto = BDACrypto("some_key_for_test")
        import os
        salt = os.urandom(8).hex()
        iv = os.urandom(16).hex()

        fp_data = {"iv": iv, "s": salt, "ct": ""}
        encrypted = crypto.re_encrypt("data", fp_data)
        assert encrypted["s"] == salt
        assert encrypted["iv"] == iv


class TestDifferentKeys:
    def test_different_keys_different_output(self):
        import os
        salt = os.urandom(8).hex()
        iv = os.urandom(16).hex()

        crypto1 = BDACrypto("key_aaaaaaaaaaaaaaaaaaaaaa")
        crypto2 = BDACrypto("key_bbbbbbbbbbbbbbbbbbbbbb")

        fp_data = {"iv": iv, "s": salt, "ct": ""}
        enc1 = crypto1.re_encrypt("same data", fp_data.copy())
        enc2 = crypto2.re_encrypt("same data", fp_data.copy())
        assert enc1["ct"] != enc2["ct"]


class TestCryptoEdgeCases:
    def test_wrong_key_produces_garbage(self):
        """Decrypting with wrong key must not silently return valid JSON."""
        import os
        crypto_correct = BDACrypto("correct_key_xxxxxxxxxxxxxxxxx")
        salt = os.urandom(8).hex()
        iv = os.urandom(16).hex()
        fp_data = {"iv": iv, "s": salt, "ct": ""}
        encrypted = crypto_correct.re_encrypt('{"valid":"json"}', fp_data)

        crypto_wrong = BDACrypto("wrong_key_xxxxxxxxxxxxxxxxxxx")
        decrypted = crypto_wrong.decrypt(encrypted)
        # With the wrong key, the result should be garbage, not parseable JSON
        try:
            parsed = json.loads(decrypted)
            # If it somehow parses, it should not be the original
            assert parsed != {"valid": "json"}
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass  # Expected: garbage bytes

    def test_empty_string_encrypt_decrypt(self):
        """Empty plaintext should survive the roundtrip."""
        import os
        crypto = BDACrypto("key_for_empty_test_xxxxxxxxxxxx")
        salt = os.urandom(8).hex()
        iv = os.urandom(16).hex()
        fp_data = {"iv": iv, "s": salt, "ct": ""}
        encrypted = crypto.re_encrypt("", fp_data)
        decrypted = crypto.decrypt(encrypted).decode()
        assert decrypted == ""

    def test_large_payload(self):
        """Encrypt/decrypt a large payload (multiple AES blocks)."""
        import os
        crypto = BDACrypto("key_for_large_test_xxxxxxxxxxxx")
        salt = os.urandom(8).hex()
        iv = os.urandom(16).hex()
        # 10 KB of data — well beyond a single 16-byte block
        large_data = json.dumps({"data": "x" * 10000})
        fp_data = {"iv": iv, "s": salt, "ct": ""}
        encrypted = crypto.re_encrypt(large_data, fp_data)
        decrypted = crypto.decrypt(encrypted).decode()
        assert decrypted == large_data

    def test_unicode_payload_multibyte_breaks_padding(self):
        """pad() counts characters, not bytes — multi-byte UTF-8 chars break AES block alignment.
        This documents a real limitation of the implementation."""
        import os
        crypto = BDACrypto("key_for_unicode_xxxxxxxxxxxx")
        salt = os.urandom(8).hex()
        iv = os.urandom(16).hex()
        unicode_data = '{"emoji":"🔥","cjk":"日本語"}'
        fp_data = {"iv": iv, "s": salt, "ct": ""}
        with pytest.raises(ValueError, match="padded to 16 byte boundary"):
            crypto.re_encrypt(unicode_data, fp_data)

    def test_ascii_special_chars_roundtrip(self):
        """ASCII-safe special characters should encrypt/decrypt correctly."""
        import os
        crypto = BDACrypto("key_for_ascii_special_xxxxx")
        salt = os.urandom(8).hex()
        iv = os.urandom(16).hex()
        data = '{"special":"!@#$%^&*()","tabs":"\\t\\n","quotes":"\\"hi\\""}'
        fp_data = {"iv": iv, "s": salt, "ct": ""}
        encrypted = crypto.re_encrypt(data, fp_data)
        decrypted = crypto.decrypt(encrypted).decode()
        assert decrypted == data

    def test_same_key_same_iv_same_salt_is_deterministic(self):
        """Same inputs must produce the same ciphertext (CBC is deterministic with fixed IV)."""
        crypto = BDACrypto("deterministic_key_xxxxxxxxx")
        fp_data = {"iv": "aa" * 16, "s": "bb" * 8, "ct": ""}
        enc1 = crypto.re_encrypt("hello", fp_data.copy())
        enc2 = crypto.re_encrypt("hello", fp_data.copy())
        assert enc1["ct"] == enc2["ct"]

    def test_different_salt_different_ciphertext(self):
        """Different salt with same key/IV must produce different ciphertext."""
        import os
        crypto = BDACrypto("same_key_for_salt_test_xxxxxx")
        iv = "cc" * 16
        enc1 = crypto.re_encrypt("hello", {"iv": iv, "s": "aa" * 8, "ct": ""})
        enc2 = crypto.re_encrypt("hello", {"iv": iv, "s": "bb" * 8, "ct": ""})
        assert enc1["ct"] != enc2["ct"]

    def test_pad_all_block_sizes(self):
        """Pad must always produce output that is a multiple of BLOCK_SIZE."""
        for length in range(0, 50):
            data = "a" * length
            padded = BDACrypto.pad(data)
            assert len(padded) % 16 == 0
            assert len(padded) >= length + 1  # at least 1 byte of padding
