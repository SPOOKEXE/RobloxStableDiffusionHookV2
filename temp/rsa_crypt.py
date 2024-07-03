import math

# Helper function: Compute the greatest common divisor
def gcd(a, b):
	while b != 0:
		a, b = b, a % b
	return a

# Helper function: Compute the modular multiplicative inverse
def mod_inverse(e, phi):
	t, new_t = 0, 1
	r, new_r = phi, e

	while new_r != 0:
		quotient = r // new_r
		t, new_t = new_t, t - quotient * new_t
		r, new_r = new_r, r - quotient * new_r

	if r > 1:
		raise ValueError("e is not invertible")
	if t < 0:
		t += phi

	return t

# Helper function: Compute the power modulo
def mod_pow(base, exp, mod):
	result = 1
	base = base % mod
	while exp > 0:
		if exp % 2 == 1:
			result = (result * base) % mod
		exp = exp // 2
		base = (base * base) % mod
	return result

# Function: Generate RSA keys
def generate_keys(p, q):
	n = p * q
	phi = (p - 1) * (q - 1)
	e = 3

	# Ensure e and phi are coprime
	while gcd(e, phi) != 1:
		e += 2

	d = mod_inverse(e, phi)

	return {'publicKey': {'e': e, 'n': n}, 'privateKey': {'d': d, 'n': n}}

# Function: Encrypt message chunks using RSA encryption
def encrypt_string_chunks(public_key, message, chunk_size):
	e, n = public_key['e'], public_key['n']
	cipher_text = []

	for i in range(0, len(message), chunk_size):
		chunk = message[i:i+chunk_size]
		encrypted_chunk = []

		for char in chunk:
			m = ord(char)
			encrypted_chunk.append(mod_pow(m, e, n))

		cipher_text.append(encrypted_chunk)

	return cipher_text

# Function: Decrypt message chunks using RSA decryption
def decrypt_string_chunks(private_key, cipher_text):
	d, n = private_key['d'], private_key['n']
	message = []

	for encrypted_chunk in cipher_text:
		decrypted_chunk = []

		for c in encrypted_chunk:
			m = mod_pow(c, d, n)
			decrypted_chunk.append(chr(m))

		message.append(''.join(decrypted_chunk))

	return ''.join(message)

# Example usage
p = 61  # Choose two prime numbers
q = 53
chunk_size = 4  # Example chunk size

keys = generate_keys(p, q)
public_key = keys['publicKey']
private_key = keys['privateKey']

message = "Hello, Roblox!"
encrypted_chunks = encrypt_string_chunks(public_key, message, chunk_size)
decrypted_message = decrypt_string_chunks(private_key, encrypted_chunks)

print("Original Message:", message)
print("Encrypted Chunks:")
for i, chunk in enumerate(encrypted_chunks):
	print(i, ' '.join(map(str, chunk)))
print("Decrypted Message:", decrypted_message)
