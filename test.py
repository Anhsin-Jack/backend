from cryptography.fernet import Fernet

# Generate a key for encryption and decryption
key = Fernet.generate_key()

# Create a Fernet cipher object with the key
cipher = Fernet(key)

# Define a function to encrypt a string
def encrypt_string(data):
    encrypted_data = cipher.encrypt(data.encode())
    return encrypted_data

# Define a function to decrypt an encrypted string
def decrypt_string(encrypted_data):
    decrypted_data = cipher.decrypt(encrypted_data).decode()
    return decrypted_data

# Example usage
original_string = "Hello, World!"

# Encrypt the string
encrypted_string_1 = encrypt_string(original_string)
encrypted_string_2 = encrypt_string(original_string)
print("Encrypted_1:", encrypted_string_1)
print("Encrypted_2:", encrypted_string_2)

# # Decrypt the string
# decrypted_string = decrypt_string(encrypted_string)
# print("Decrypted:", decrypted_string)

# print()
