from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from base64 import encodebytes

class KeyCertificate:
	key = None

	def GetPrivateBytes(self, encoding=crypto_serialization.Encoding.PEM, format=crypto_serialization.PrivateFormat.PKCS8, encryption=crypto_serialization.NoEncryption() ) -> bytes:
		return self.key.private_bytes(encoding, format, encryption)

	def GetPublicBytes(self) -> bytes:
		return self.key.public_key()

	def GetPrivateBase64(self, encoding=crypto_serialization.Encoding.PEM, format=crypto_serialization.PrivateFormat.PKCS8, encryption=crypto_serialization.NoEncryption() ) -> str:
		return encodebytes(self.GetPrivateBytes(encoding=encoding, format=format, encryption=encryption)).decode("utf-8")

	def GetPublicBase64(self) -> str:
		return encodebytes(self.GetPublicBytes()).decode("utf-8")

	def __init__(self, backend=crypto_default_backend(), public_exponent=65537, key_size=4096):
		self.key = rsa.generate_private_key( backend=backend, public_exponent=public_exponent, key_size=key_size )

def ToBase64(data : bytes) -> str:
	return encodebytes(data).decode("utf-8")

def GenerateDefaultCertificateBase64() -> tuple[str, str]:
	return (KeyCertificate().GetPrivateBase64(), KeyCertificate().GetPublicBase64())

def GenerateDefaultCertificateBytes() -> tuple[bytes, bytes]:
	return (KeyCertificate().GetPrivateBytes(), KeyCertificate().GetPublicBytes())
