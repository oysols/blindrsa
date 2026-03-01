import ctypes
from pathlib import Path

from blindrsa import zig

_lib = ctypes.CDLL((Path(__file__).parent / "_lib.so").absolute())

exports = zig.ZigExports(_lib, "exports", strip=["brsa.BlindRsaCustom(2048,.sha384,.pss,.deterministic)."])


def generate_keypair() -> tuple[bytes, bytes]:
    # Manual:
    # openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -outform PEM -out sk.pem
    # openssl rsa -in sk.pem -outform DER -out sk.der
    # openssl rsa -in sk.pem -RSAPublicKey_out -outform DER -out pk.der
    sk = bytearray(2048)
    sk_len = zig.usize()
    pk = bytearray(2048)
    pk_len = zig.usize()
    exports.assert_fn("generate_keypair(*[2048]u8, *usize, *[2048]u8, *usize) ?[*:0]const u8")
    _lib.generate_keypair.restype = zig.c_char_p
    if err := _lib.generate_keypair(
        zig.pointer_to_bytearray(sk),
        zig.pointer_to_value(sk_len),
        zig.pointer_to_bytearray(pk),
        zig.pointer_to_value(pk_len),
    ):
        raise zig.ZigError(err)
    return (bytes(sk[0 : sk_len.value]), bytes(pk[0 : pk_len.value]))


class SecretKey:
    def __init__(self, sk_der: bytes) -> None:
        exports.assert_fn("sk_init([*]u8, usize) ?*SecretKey")
        _lib.sk_init.restype = zig.pointer
        self._ptr = _lib.sk_init(
            zig.pointer_to_bytes(sk_der),
            zig.usize(len(sk_der)),
        )
        if not self._ptr:
            raise zig.ZigError(b"Init failed")

    def __del__(self) -> None:
        if hasattr(self, "ptr") and self._ptr:
            exports.assert_fn("sk_deinit(*SecretKey) void")
            _lib.sk_deinit.restype = None
            self._ptr = _lib.sk_deinit(zig.pointer(self._ptr))

    def sign(self, blinded_msg: bytes) -> bytes:
        assert len(blinded_msg) == 256
        signed = bytearray(256)
        exports.assert_fn("sk_sign(*SecretKey, *const [256]u8, *[256]u8) ?[*:0]const u8")
        _lib.sk_sign.restype = zig.c_char_p
        if err := _lib.sk_sign(
            zig.pointer(self._ptr),
            zig.pointer_to_bytes(blinded_msg),
            zig.pointer_to_bytearray(signed),
        ):
            raise zig.ZigError(err)
        return bytes(signed)


class PublicKey:
    def __init__(self, pk_der: bytes) -> None:
        exports.assert_fn("pk_init([*]u8, usize) ?*PublicKey")
        _lib.pk_init.restype = zig.pointer
        self._ptr = _lib.pk_init(
            zig.pointer_to_bytes(pk_der),
            zig.usize(len(pk_der)),
        )
        if not self._ptr:
            raise zig.ZigError(b"Init failed")

    def __del__(self) -> None:
        if hasattr(self, "ptr") and self._ptr:
            _lib.sk_deinit.restype = None
            exports.assert_fn("pk_deinit(*PublicKey) void")
            _lib.pk_deinit(zig.pointer(self._ptr))

    def blind(self, msg: bytes) -> tuple[bytes, bytes]:
        blinded_msg = bytearray(256)
        secret = bytearray(256)
        # msg_randomizer = bytearray(32)
        exports.assert_fn("pk_blind(*PublicKey, [*]const u8, usize, *[256]u8, *[256]u8) ?[*:0]const u8")
        _lib.pk_blind.restype = zig.c_char_p
        if err := _lib.pk_blind(
            zig.pointer(self._ptr),
            zig.pointer_to_bytes(msg),
            zig.usize(len(msg)),
            zig.pointer_to_bytearray(blinded_msg),
            zig.pointer_to_bytearray(secret),
            # zig.pointer_to_bytearray(msg_randomizer),
        ):
            raise zig.ZigError(err)
        return bytes(blinded_msg), bytes(secret)  # ,bytes(msg_randomizer)

    def finalize(
        self,
        signed: bytes,
        blinded: bytes,
        secret: bytes,
        # msg_randomizer: bytes,
        msg: bytes,
    ) -> bytes:
        assert len(signed) == 256
        assert len(blinded) == 256
        assert len(secret) == 256
        # assert len(msg_randomizer) == 32
        signature = bytearray(256)
        exports.assert_fn(
            "pk_finalize(*PublicKey, *[256]u8, *[256]u8, *[256]u8, [*]u8, usize, *[256]u8) ?[*:0]const u8"
        )
        _lib.pk_finalize.restype = zig.c_char_p
        if err := _lib.pk_finalize(
            zig.pointer(self._ptr),
            zig.pointer_to_bytes(signed),
            zig.pointer_to_bytes(blinded),
            zig.pointer_to_bytes(secret),
            # zig.pointer_to_bytes(msg_randomizer),
            zig.pointer_to_bytes(msg),
            zig.usize(len(msg)),
            zig.pointer_to_bytearray(signature),
        ):
            raise zig.ZigError(err)
        return bytes(signature)

    def verify(
        self,
        signature: bytes,
        # msg_randomizer: bytes,
        msg: bytes,
    ) -> None:
        assert len(signature) == 256
        # assert len(msg_randomizer) == 32
        exports.assert_fn("pk_verify(*PublicKey, *[256]u8, [*]u8, usize) ?[*:0]const u8")
        _lib.pk_verify.restype = zig.c_char_p
        if err := _lib.pk_verify(
            zig.pointer(self._ptr),
            zig.pointer_to_bytes(signature),
            # zig.pointer_to_bytes(msg_randomizer),
            zig.pointer_to_bytes(msg),
            zig.usize(len(msg)),
        ):
            raise zig.ZigError(err)


if __name__ == "__main__":
    # sk_der = Path("sk.der").read_bytes()
    # pk_der = Path("pk.der").read_bytes()
    sk_der, pk_der = generate_keypair()
    sk = SecretKey(sk_der)
    pk = PublicKey(pk_der)
    msg = b"hello"
    blinded_msg, secret = pk.blind(msg)
    signed = sk.sign(blinded_msg)
    signature = pk.finalize(signed, blinded_msg, secret, msg)
    pk.verify(signature, msg)
    print("OK")
