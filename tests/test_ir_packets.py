import base64
import unittest

from sony_trinitron_remote import CODES, EXTRA_BUTTONS, ir_packet, is_valid_b64


class IrPacketTests(unittest.TestCase):
    def test_all_builtin_codes_are_broadlink_packets(self):
        for key, encoded in CODES.items():
            with self.subTest(key=key):
                self.assertTrue(is_valid_b64(encoded))
                packet = base64.b64decode(encoded)
                self.assertEqual(0x26, packet[0])
                self.assertGreaterEqual(len(packet), 10)

    def test_repetition_count_updates_broadlink_header(self):
        for repeats in (1, 3, 5, 8):
            with self.subTest(repeats=repeats):
                packet = ir_packet("info", {}, repeats=repeats)
                self.assertEqual(packet[1], repeats - 1)

    def test_custom_code_takes_precedence(self):
        code = CODES["menu"]
        self.assertEqual(
            ir_packet("source", {"source": code}, repeats=3),
            ir_packet("menu", {}, repeats=3),
        )

    def test_missing_special_code_is_not_guessed(self):
        key = next(iter(EXTRA_BUTTONS))
        with self.assertRaises(LookupError):
            ir_packet(key, {}, repeats=3)

    def test_invalid_repeat_count_is_rejected(self):
        for val in (0, 9):
            with self.assertRaises(ValueError):
                ir_packet("power", {}, repeats=val)

    def test_invalid_base64_code_is_rejected(self):
        self.assertFalse(is_valid_b64("not-base64"))
        self.assertFalse(is_valid_b64(base64.b64encode(b"1234567890").decode()))

    def test_all_expected_controls_present(self):
        for key in ("source", "tv", "info", "menu", "vol+", "vol-", "power", "red", "green", "white"):
            self.assertIn(key, CODES)


if __name__ == "__main__":
    unittest.main()
