import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from Crypto.Cipher import AES, Blowfish, ChaCha20
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import os
import time
import pickle


class TraditionalEncryptionApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def encrypt_file(self):
        algorithm = simpledialog.askstring("Encryption Algorithm",
                                           "Enter algorithm (AES, RSA-AES, Blowfish, ChaCha20):")
        if not algorithm or algorithm.upper() not in ['AES', 'RSA-AES', 'BLOWFISH', 'CHACHA20']:
            messagebox.showinfo("Info", "Invalid or no algorithm selected.")
            return

        file_path = filedialog.askopenfilename(title="Select file to encrypt")
        if not file_path:
            messagebox.showinfo("Info", "No file selected.")
            return

        with open(file_path, 'rb') as f:
            data = f.read()

        start_time = time.time()
        encrypted_data = None
        key_data = {}

        if algorithm.upper() == 'AES':
            key = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_EAX)
            ciphertext, tag = cipher.encrypt_and_digest(pad(data, AES.block_size))
            encrypted_data = {'ciphertext': ciphertext, 'nonce': cipher.nonce, 'tag': tag}
            key_data = {'key': key}

        elif algorithm.upper() == 'RSA-AES':
            rsa_key = RSA.generate(2048)
            aes_key = get_random_bytes(16)
            cipher_rsa = PKCS1_OAEP.new(rsa_key.publickey())
            enc_aes_key = cipher_rsa.encrypt(aes_key)
            cipher_aes = AES.new(aes_key, AES.MODE_EAX)
            ciphertext, tag = cipher_aes.encrypt_and_digest(pad(data, AES.block_size))
            encrypted_data = {
                'ciphertext': ciphertext,
                'nonce': cipher_aes.nonce,
                'tag': tag,
                'enc_aes_key': enc_aes_key
            }
            key_data = {'rsa_private_key': rsa_key.export_key()}

        elif algorithm.upper() == 'BLOWFISH':
            key = get_random_bytes(16)
            cipher = Blowfish.new(key, Blowfish.MODE_ECB)
            ciphertext = cipher.encrypt(pad(data, Blowfish.block_size))
            encrypted_data = {'ciphertext': ciphertext}
            key_data = {'key': key}

        elif algorithm.upper() == 'CHACHA20':
            key = get_random_bytes(32)
            cipher = ChaCha20.new(key=key)
            ciphertext = cipher.encrypt(data)
            encrypted_data = {'ciphertext': ciphertext, 'nonce': cipher.nonce}
            key_data = {'key': key}

        encryption_time = time.time() - start_time

        base_name, ext = os.path.splitext(file_path)
        encrypted_file_path = f"{base_name}_{algorithm.lower()}_encrypted{ext}"
        key_path = f"{base_name}_{algorithm.lower()}_key.pkl"

        with open(encrypted_file_path, 'wb') as ef:
            pickle.dump(encrypted_data, ef)

        with open(key_path, 'wb') as kf:
            pickle.dump(key_data, kf)

        messagebox.showinfo("Encryption Complete",
                            f"File encrypted using {algorithm}.\n"
                            f"Saved as: {encrypted_file_path}\n"
                            f"Encryption Time: {encryption_time:.4f} seconds\n"
                            f"Key saved as: {key_path}\n"
                            "Keep this file secure!")

    def decrypt_file(self):
        algorithm = simpledialog.askstring("Decryption Algorithm",
                                           "Enter algorithm (AES, RSA-AES, Blowfish, ChaCha20):")
        if not algorithm or algorithm.upper() not in ['AES', 'RSA-AES', 'BLOWFISH', 'CHACHA20']:
            messagebox.showinfo("Info", "Invalid or no algorithm selected.")
            return

        enc_file_path = filedialog.askopenfilename(title="Select encrypted file")
        key_path = filedialog.askopenfilename(title="Select key file")

        if not enc_file_path or not key_path:
            messagebox.showinfo("Info", "File or key not selected.")
            return

        with open(enc_file_path, 'rb') as f:
            encrypted_data = pickle.load(f)
        with open(key_path, 'rb') as f:
            key_data = pickle.load(f)

        try:
            start_time = time.time()
            if algorithm.upper() == 'AES':
                cipher = AES.new(key_data['key'], AES.MODE_EAX, nonce=encrypted_data['nonce'])
                data = unpad(cipher.decrypt_and_verify(encrypted_data['ciphertext'], encrypted_data['tag']), AES.block_size)

            elif algorithm.upper() == 'RSA-AES':
                rsa_key = RSA.import_key(key_data['rsa_private_key'])
                cipher_rsa = PKCS1_OAEP.new(rsa_key)
                aes_key = cipher_rsa.decrypt(encrypted_data['enc_aes_key'])
                cipher_aes = AES.new(aes_key, AES.MODE_EAX, nonce=encrypted_data['nonce'])
                data = unpad(cipher_aes.decrypt_and_verify(encrypted_data['ciphertext'], encrypted_data['tag']), AES.block_size)

            elif algorithm.upper() == 'BLOWFISH':
                cipher = Blowfish.new(key_data['key'], Blowfish.MODE_ECB)
                data = unpad(cipher.decrypt(encrypted_data['ciphertext']), Blowfish.block_size)

            elif algorithm.upper() == 'CHACHA20':
                cipher = ChaCha20.new(key=key_data['key'], nonce=encrypted_data['nonce'])
                data = cipher.decrypt(encrypted_data['ciphertext'])
            decryption_time = time.time() - start_time

            output_path = enc_file_path.replace('_encrypted', '_decrypted')
            with open(output_path, 'wb') as f:
                f.write(data)

            messagebox.showinfo("Success",
                            f"File decrypted successfully.\n"
                            f"Saved as: {output_path}\n"
                            f"Decryption Time: {decryption_time:.4f} seconds")

        except Exception as e:
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")

    def run(self):
        choice = simpledialog.askinteger("Select Option", "1. Encrypt\n2. Decrypt", minvalue=1, maxvalue=2)
        if choice == 1:
            self.encrypt_file()
        elif choice == 2:
            self.decrypt_file()
        else:
            messagebox.showinfo("Info", "Invalid option selected.")


if __name__ == "__main__":
    try:
        app = TraditionalEncryptionApp()
        app.run()
    except Exception as e:
        tk.messagebox.showerror("App Error", str(e))
