import tenseal as ts
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import pickle
import zlib
import time
import psutil

class HomomorphicEncryptionApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window

    def setup_context(self, poly_modulus_degree, plain_modulus):
        self.context = ts.context(
            ts.SCHEME_TYPE.BFV,
            poly_modulus_degree=poly_modulus_degree,
            plain_modulus=plain_modulus
        )
        self.context.generate_galois_keys()
        self.context.global_scale = 2 ** 40

    def encrypt_file(self):
        file_paths = filedialog.askopenfilenames(title="Select files to encrypt", filetypes=[("PDF files", "*.pdf")])
        if not file_paths:
            messagebox.showinfo("Info", "No file selected.")
            return

        try:
            # Ask user to input encryption parameters
            poly_modulus_degree = simpledialog.askinteger("Input", "Enter poly_modulus_degree (4096, 8192, 16384, 32768):", minvalue=4096)
            plain_modulus = simpledialog.askinteger("Input", "Enter plain_modulus (e.g., 1032193, 114689, etc.):", minvalue=2)

            self.setup_context(poly_modulus_degree, plain_modulus)

            for file_path in file_paths:
                with open(file_path, 'rb') as f:
                    data = f.read()

                # Compress before encryption
                compressed_data = zlib.compress(data)
                compressed_data_int = [b for b in compressed_data]

                # Monitor CPU and memory before encryption
                process = psutil.Process(os.getpid())
                start_mem = process.memory_info().rss / (1024 * 1024)  # in MB
                start_cpu = psutil.cpu_percent(interval=1)

                start_time = time.time()
                encrypted_data = ts.bfv_vector(self.context, compressed_data_int)
                encrypted_data_serialized = encrypted_data.serialize()
                end_time = time.time()

                # Monitor CPU and memory after encryption
                end_mem = process.memory_info().rss / (1024 * 1024)
                end_cpu = psutil.cpu_percent(interval=1)

                encryption_time = end_time - start_time

                # Create output filename
                base_name, ext = os.path.splitext(file_path)
                encrypted_file_path = f"{base_name}_he{ext}.encrypted"

                with open(encrypted_file_path, 'wb') as f:
                    pickle.dump({
                        'encrypted_data': encrypted_data_serialized,
                        'context': self.context.serialize(save_secret_key=False),
                        'original_ext': ext,
                        'poly_modulus_degree': poly_modulus_degree,
                        'plain_modulus': plain_modulus,
                        'encryption_time': encryption_time,
                        'start_mem_MB': start_mem,
                        'end_mem_MB': end_mem,
                        'start_cpu_percent': start_cpu,
                        'end_cpu_percent': end_cpu
                    }, f)

                messagebox.showinfo("Success", f"File encrypted successfully.\nSaved as: {encrypted_file_path}\n\nEncryption time: {encryption_time:.2f} seconds\nMemory usage increased by {(end_mem - start_mem):.2f} MB")

            # Save secret key separately
            context_with_sk = self.context.serialize(save_secret_key=True)
            key_path = f"{base_name}_he_keys.key"
            with open(key_path, 'wb') as f:
                f.write(context_with_sk)
            messagebox.showinfo("Key Saved", f"Decryption key saved as:\n{key_path}\nKeep it secure!")

        except Exception as e:
            messagebox.showerror("Error", f"Encryption failed: {str(e)}")

    def decrypt_file(self):
        encrypted_file_path = filedialog.askopenfilename(title="Select encrypted file", filetypes=[("Encrypted files", "*_he*.encrypted")])
        if not encrypted_file_path:
            messagebox.showinfo("Info", "No file selected.")
            return

        key_path = filedialog.askopenfilename(title="Select the decryption key file")
        if not key_path:
            messagebox.showinfo("Info", "No key file selected.")
            return

        try:
            with open(encrypted_file_path, 'rb') as f:
                data_dict = pickle.load(f)

            with open(key_path, 'rb') as f:
                context_with_sk_bytes = f.read()

            context = ts.context_from(context_with_sk_bytes)
            start_time = time.time()
            encrypted_data = ts.bfv_vector_from(context, data_dict['encrypted_data'])
            decrypted_data = encrypted_data.decrypt()

            decrypted_bytes = bytes(decrypted_data)

            decompressed_data = zlib.decompress(decrypted_bytes)
            end_time = time.time()
            decryption_time = end_time - start_time

            base_name = os.path.splitext(encrypted_file_path)[0]
            decrypted_file_path = f"{base_name}_decrypted{data_dict['original_ext']}"

            with open(decrypted_file_path, 'wb') as f:
                f.write(decompressed_data)

            messagebox.showinfo("Success", f"File decrypted successfully.\nSaved as: {decrypted_file_path}\nDecryption time: {decryption_time:.4f} seconds")

        except Exception as e:
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")

    def run(self):
        option = simpledialog.askinteger("Option", "Select operation:\n1. Encrypt\n2. Decrypt", minvalue=1, maxvalue=2)
        if option == 1:
            self.encrypt_file()
        elif option == 2:
            self.decrypt_file()
        else:
            messagebox.showinfo("Info", "No valid option selected.")

if __name__ == "__main__":
    try:
        app = HomomorphicEncryptionApp()
        app.run()
    except Exception as e:
        tk.messagebox.showerror("Error", f"Application error: {str(e)}")
