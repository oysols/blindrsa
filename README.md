# blindrsa

Implements blind signatures used in anonymous ecash/evotes implementations.

Python wrapper for [zig-blind-rsa-signatures](https://github.com/jedisct1/zig-blind-rsa-signatures).

Implements `BlindRsaPSSDeterministic(2048)`.

```python
import secrets

import blindrsa

# Generate keys in DER binary format (bytes)
sk_der, pk_der = blindrsa.generate_keypair()

# Initialize
secret_key = blindrsa.SecretKey(sk_der)
public_key = blindrsa.PublicKey(pk_der)

# CLIENT: Create and blind message
msg = secrets.token_bytes(32)
blinded_msg, secret = public_key.blind(msg)

# SERVER: Sign the blinded message
blind_sig = secret_key.sign(blinded_msg)

# CLIENT: Unblind to arrive at valid msg + msg_randomizer + signature
signature = public_key.finalize(blind_sig, blinded_msg, secret, msg)

# SERVER: Verify that signature is correct
public_key.verify(signature, msg)
print("Signature valid")
```
