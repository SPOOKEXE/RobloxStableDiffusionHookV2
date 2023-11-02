
from base64 import encodebytes, decodebytes
from string import ascii_letters, digits
from random import randint
from Cryptodome.Cipher import AES

CHARACTERS = list(ascii_letters + digits)

KEY_LENGTHS = [ 16, 32 ]
KEY_LENGTH_ERROR = 'Key must be one of lengths: ' + ", ".join( [ str(v) for v in KEY_LENGTHS] )

def generate_random_key( length : int = 16 ) -> str:
	'''
	Generate a random string of length comprised of ascii letters and digits.
	'''
	return "".join([ CHARACTERS[randint(0, len(CHARACTERS)-1)] for _ in range(length) ])

def encode_base64_hex( value : str | bytes, encoding : str = 'utf-8' ) -> str:
	'''
	Encode value to base64 hex
	'''
	if type(value) == str: value = bytes( value, encoding=encoding )
	return encodebytes(value).hex()

def decode_base64_hex( value : str | bytes, encoding : str = 'utf-8' ) -> str:
	'''
	Decode base64 hex
	'''
	if type(value) == str: value = bytes.fromhex( value )
	return decodebytes( value ).decode( encoding=encoding )

def aes_encrypt( plaintext : str | bytes, key : str, encoding : str ='utf-8' ) -> tuple[str, str, str]:
	'''
	Advanced Encryption Standard Encrypt Function
	'''
	if type(plaintext) == bytes:
		plaintext = plaintext.decode(encoding)
	assert type(plaintext) == str, 'Plaintext must be a string.'
	assert type(key) == str, 'Key must be a string.'
	assert KEY_LENGTHS.count( len(key) ) != 0, KEY_LENGTH_ERROR
	system = AES.new( key=bytes(key, encoding=encoding), mode=AES.MODE_EAX )
	ciphertext, tag = system.encrypt_and_digest( bytes(plaintext, encoding=encoding) )
	return system.nonce.hex(), tag.hex(), ciphertext.hex()

def aes_decrypt( nonce : str, tag : str, ciphertext : str, key : str, encoding : str = 'utf-8' ) -> str:
	'''
	Advanced Encryption Standard Decrypt Function
	'''
	assert type(nonce) == str, 'Nonce must be a string.'
	assert type(tag) == str, 'Tag must be a string.'
	assert type(ciphertext) == str, 'Ciphertext must be a string.'
	assert type(key) == str, 'Key must be a string.'
	system = AES.new( key=bytes(key, encoding=encoding), mode=AES.MODE_EAX, nonce=bytes.fromhex(nonce) )
	plaintext : bytes = system.decrypt_and_verify( bytes.fromhex(ciphertext), bytes.fromhex(tag) )
	return plaintext.decode(encoding=encoding)

def test_B64( ):
	plaintext_in : str = 'hello friend!' * 39
	bytes_in : bytes = bytes( plaintext_in, encoding='utf-8' )

	plaintext_b64 : str = encode_base64_hex( plaintext_in )
	bytes_b64 : str = encode_base64_hex( bytes_in )

	plaintext_out : str = decode_base64_hex( plaintext_b64 )
	bytes_out : bytes = bytes( decode_base64_hex( bytes_b64 ), encoding='utf-8' )

	assert plaintext_in == plaintext_out, 'Plaintext failed to encode and decode to the same value.'
	assert bytes_in == bytes_out, 'Bytes failed to encode and decode to the same value.'

def test_AES( ):
	key : str = generate_random_key( length=32 )

	plain_in : str = 'hello friend!' * 39
	plain_nonce, plain_tag, plain_ciphertext = aes_encrypt( plain_in, key )
	plain_out = aes_decrypt( plain_nonce, plain_tag, plain_ciphertext, key )
	assert plain_in == plain_out, 'Plaintext failed to encrypt and decrypt to the same value.'

	bytes_in : bytes = bytes( plain_in, encoding='utf-8' )
	bytes_nonce, bytes_tag, bytes_ciphertext = aes_encrypt( bytes_in, key )
	bytes_out = aes_decrypt( bytes_nonce, bytes_tag, bytes_ciphertext, key )
	assert bytes_in == bytes(bytes_out, encoding='utf-8' ), 'Bytes failed to encrypt and decrypt to the same value.'

def test_random_key( ):
	assert len( generate_random_key( length=8 ) ) == 8, 'Generate random key did not produce key of length 8.'
	assert len( generate_random_key( length=16 ) ) == 16, 'Generate random key did not produce key of length 16.'
	assert len( generate_random_key( length=32 ) ) == 32, 'Generate random key did not produce key of length 32.'
	assert len( generate_random_key( length=64 ) ) == 64, 'Generate random key did not produce key of length 64.'

if __name__ == '__main__':
	test_random_key( )
	print('Random Key Passed')
	test_AES( )
	print('AES Passed')
	test_B64( )
	print('Base64 Passed')
	pass
