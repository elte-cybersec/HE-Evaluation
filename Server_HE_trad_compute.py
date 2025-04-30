import os
from flask import Flask, request, render_template, jsonify, send_file
from azure.storage.blob import BlobServiceClient
import time
import psutil
import pickle
import io
import tenseal as ts
from Crypto.Cipher import AES, Blowfish
from Crypto.PublicKey import RSA
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES, Blowfish, ChaCha20, PKCS1_OAEP
from os import cpu_count
from concurrent.futures import ProcessPoolExecutor


app = Flask(__name__)

# Azure Blob Storage Configuration
connect_str = 'DefaultEndpointsProtocol=https;AccountName=homomorphic;AccountKey=QyrFWEtexnrplRlDuvHqjF/gpH+fFy2pPodBUzw6EDHnJojMu3Wg8bu2P25408kaCAHxwz7rffG3+AStw3os0A==;EndpointSuffix=core.windows.net'
container_name = 'hom'

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client(container_name)


# Route to upload a file to Blob Storage
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')  # Get the file from the request

    if file:
        try:
            blob_client = container_client.get_blob_client(file.filename)
            blob_client.upload_blob(file)  # Upload file to Blob Storage
            return jsonify("File uploaded successfully!"), 200  # Success message
        except Exception as e:
            return jsonify({"error": str(e)}), 500  # Error if upload fails
    else:
        return jsonify({"error": "No file uploaded!"}), 400  # Error if no file is uploaded

@app.route('/optimized')
def optimized():
    return render_template('optimized.html')
def get_cpu_memory_usage_optimized():
    process = psutil.Process()
    memory_usage = process.memory_info().rss / (1024 ** 2)  # Convert to MB
    cpu_usage = psutil.cpu_percent(interval=1)  # Get the CPU usage over one second
    return memory_usage, cpu_usage

def compute_addition_and_multiplication_optimized(encrypted_vector, context):
    # Use NTT (Number Theoretic Transform) 
    if hasattr(encrypted_vector, 'ntt_transform'):
        encrypted_vector.ntt_transform()  # Apply NTT transform to optimize multiplication
    
    # Measure memory and CPU usage before computation
    memory_before, cpu_before = get_cpu_memory_usage_optimized()

    # Perform homomorphic operations
    start_time = time.time()
    result_add = encrypted_vector + encrypted_vector  # Homomorphic addition
    addition_time = time.time() - start_time

    start_time = time.time()
    result_mul = encrypted_vector * encrypted_vector  # Homomorphic multiplication
    # Apply Inverse NTT to bring data back to the standard representation
    if hasattr(result_mul, 'intt_transform'):
        result_mul.intt_transform()
    
    multiplication_time = time.time() - start_time

    # Measure memory and CPU usage after computation
    memory_after, cpu_after = get_cpu_memory_usage_optimized()

    # Calculate throughput
    
    data_size_in_mb = (len(encrypted_vector.serialize()) * 2) / (1024 ** 2)  
    total_time = addition_time + multiplication_time
    throughput = data_size_in_mb / total_time if total_time > 0 else 0

    return {
        "addition_time": addition_time,
        "multiplication_time": multiplication_time,
        "memory_before": memory_before,
        "memory_after": memory_after,
        "cpu_before": cpu_before,
        "cpu_after": cpu_after,
        "throughput": throughput
    }

@app.route('/compute_he_optimized', methods=['POST'])
def compute_he_optimized():
    file_name = request.form.get('file_name')

    if not file_name:
        return jsonify({"error": "No file selected"}), 400

    blob_client = container_client.get_blob_client(file_name)
    download_stream = blob_client.download_blob()
    file_data = download_stream.readall()

    data = pickle.loads(file_data)  # Deserialize the data
    if 'context' not in data or 'encrypted_data' not in data:
        return jsonify({"error": "Required data keys missing in the file."}), 400

    context = ts.context_from(data['context'])
    encrypted_vector = ts.bfv_vector_from(context, data['encrypted_data'])

    computation_result = compute_addition_and_multiplication_optimized(encrypted_vector, context)
    
    return jsonify(computation_result)

    
# Route to download file from Blob Storage
@app.route('/download', methods=['POST'])
def download_file():
    file_name = request.form['file_name']
    if file_name:
        blob_client = container_client.get_blob_client(file_name)
        # Download the blob to a byte stream
        download_stream = blob_client.download_blob()
        byte_data = download_stream.readall()
        return send_file(
            io.BytesIO(byte_data),
            as_attachment=True,
            download_name=file_name,
            mimetype='application/octet-stream'
        )
    return jsonify({"error": "No file selected"}), 400

# Route to compute (perform computations on Blob)
@app.route('/compute_blob', methods=['POST'])
def compute_from_blob():
    selected_file = request.form.get('file_name')

    if selected_file:
        blob_client = container_client.get_blob_client(selected_file)
        download_stream = blob_client.download_blob()
        byte_data = download_stream.readall()
        computation_result = compute(byte_data)
        return jsonify(computation_result)
    
    return jsonify({"error": "No file selected"}), 400

def get_cpu_memory_usage():
    """ Function to get current process's CPU and memory usage. """
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / (1024 ** 2)  # Memory in MB
    cpu_usage = psutil.cpu_percent(interval=2)  # Increased interval for better accuracy
    return memory_usage, cpu_usage

# Function to parallelize the operations on data
def parallel_process(data, function):
    """Helper function to parallelize operations on data."""
    chunk_size = len(data) // psutil.cpu_count()
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(function, chunks))
    return np.concatenate(results)

# Function to calculate throughput
def calculate_throughput(data, total_computation_time):
    """ Improved throughput calculation accounting for faster operations. """
    data_size_in_mb = len(data) / (1024 ** 2)  # Size in MB
    if total_computation_time > 0:
        return data_size_in_mb / total_computation_time
    return 0  # Avoid division by zero

# AES encryption computation
def compute_aes(data):
    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_EAX)

    # Measure memory and CPU before computation
    memory_before, cpu_before = get_cpu_memory_usage()

    # Perform addition and multiplication in parallel
    start_time = time.time()
    result_add = parallel_process(data, lambda x: bytearray((i + 1) % 256 for i in x))  # Addition: (x + 1) % 256
    result_mul = parallel_process(data, lambda x: bytearray((i * 2) % 256 for i in x))  # Multiplication: (x * 2) % 256
    total_time = time.time() - start_time

    # Measure memory and CPU after computation
    memory_after, cpu_after = get_cpu_memory_usage()

    # Calculate throughput (MB/s)
    throughput = calculate_throughput(data, total_time)

    return total_time, total_time, memory_before, memory_after, cpu_before, cpu_after, throughput

# RSA encryption computation
def compute_rsa(data):
    rsa_key = RSA.generate(2048)
    cipher = PKCS1_OAEP.new(rsa_key.publickey())

    memory_before, cpu_before = get_cpu_memory_usage()
    start_time = time.time()
    result_add = parallel_process(data, lambda x: bytearray((i + 1) % 256 for i in x))  # Addition: (x + 1) % 256
    result_mul = parallel_process(data, lambda x: bytearray((i * 2) % 256 for i in x))  # Multiplication: (x * 2) % 256
    total_time = time.time() - start_time

    memory_after, cpu_after = get_cpu_memory_usage()
    throughput = calculate_throughput(data, total_time)

    return total_time, total_time, memory_before, memory_after, cpu_before, cpu_after, throughput

# Blowfish encryption computation
def compute_blowfish(data):
    key = get_random_bytes(16)
    cipher = Blowfish.new(key, Blowfish.MODE_CBC)

    memory_before, cpu_before = get_cpu_memory_usage()
    start_time = time.time()
    result_add = parallel_process(data, lambda x: bytearray((i + 1) % 256 for i in x))  # Addition: (x + 1) % 256
    result_mul = parallel_process(data, lambda x: bytearray((i * 2) % 256 for i in x))  # Multiplication: (x * 2) % 256
    total_time = time.time() - start_time

    memory_after, cpu_after = get_cpu_memory_usage()
    throughput = calculate_throughput(data, total_time)

    return total_time, total_time, memory_before, memory_after, cpu_before, cpu_after, throughput

# ChaCha20 encryption computation
def compute_chacha20(data):
    key = get_random_bytes(32)
    cipher = ChaCha20.new(key=key)

    memory_before, cpu_before = get_cpu_memory_usage()
    start_time = time.time()
    result_add = parallel_process(data, lambda x: bytearray((i + 1) % 256 for i in x))  # Addition: (x + 1) % 256
    result_mul = parallel_process(data, lambda x: bytearray((i * 2) % 256 for i in x))  # Multiplication: (x * 2) % 256
    total_time = time.time() - start_time

    memory_after, cpu_after = get_cpu_memory_usage()
    throughput = calculate_throughput(data, total_time)

    return total_time, total_time, memory_before, memory_after, cpu_before, cpu_after, throughput

# Function to compute metrics for all algorithms
def compute(data):
    # Compute metrics for each algorithm
    aes_metrics = compute_aes(data)
    rsa_metrics = compute_rsa(data)
    blowfish_metrics = compute_blowfish(data)
    chacha20_metrics = compute_chacha20(data)

    return {
        "aes_addition_time": aes_metrics[0],
        "aes_multiplication_time": aes_metrics[1],
        "rsa_addition_time": rsa_metrics[0],
        "rsa_multiplication_time": rsa_metrics[1],
        "blowfish_addition_time": blowfish_metrics[0],
        "blowfish_multiplication_time": blowfish_metrics[1],
        "chacha20_addition_time": chacha20_metrics[0],
        "chacha20_multiplication_time": chacha20_metrics[1],
        "aes_memory_before": aes_metrics[2],
        "aes_memory_after": aes_metrics[3],
        "rsa_memory_before": rsa_metrics[2],
        "rsa_memory_after": rsa_metrics[3],
        "blowfish_memory_before": blowfish_metrics[2],
        "blowfish_memory_after": blowfish_metrics[3],
        "chacha20_memory_before": chacha20_metrics[2],
        "chacha20_memory_after": chacha20_metrics[3],
        "aes_cpu_before": aes_metrics[4],
        "aes_cpu_after": aes_metrics[5],
        "rsa_cpu_before": rsa_metrics[4],
        "rsa_cpu_after": rsa_metrics[5],
        "blowfish_cpu_before": blowfish_metrics[4],
        "blowfish_cpu_after": blowfish_metrics[5],
        "chacha20_cpu_before": chacha20_metrics[4],
        "chacha20_cpu_after": chacha20_metrics[5],
        "aes_throughput": aes_metrics[6],
        "rsa_throughput": rsa_metrics[6],
        "blowfish_throughput": blowfish_metrics[6],
        "chacha20_throughput": chacha20_metrics[6],
    }

# Compute function for traditional algorithms
@app.route('/compute', methods=['POST'])
def compute_file():
    file = request.files.get('file')
    selected_file = request.form.get('file_name')

    if file:
        computation_result = compute(file.read())  
    elif selected_file:
        blob_client = container_client.get_blob_client(selected_file)
        download_stream = blob_client.download_blob()
        byte_data = download_stream.readall()
        computation_result = compute(byte_data)
    else:
        return jsonify({"error": "No file uploaded or selected."})

    return jsonify(computation_result)

# Function to get CPU and memory usage for Homomorphic Encryption (HE)
def get_cpu_memory_usage_he():
    process = psutil.Process()
    memory_usage = process.memory_info().rss / (1024 ** 2)  # Memory in MB
    cpu_usage = psutil.cpu_percent(interval=1)  # CPU usage in percentage
    return memory_usage, cpu_usage

@app.route('/compute_he', methods=['POST'])
def compute_he():
    selected_file = request.form.get('file_name')  # Extract the file name from form data
    
    if selected_file:
        # Retrieve the file from Blob Storage
        blob_client = container_client.get_blob_client(selected_file)
        download_stream = blob_client.download_blob()
        file_data = download_stream.readall()  # Read the file content

        # Perform computation on the file data
        computation_result = compute_addition_and_multiplication(file_data)
        return jsonify(computation_result)
    else:
        return jsonify({"error": "No file selected!"}), 400


# Simulate Addition Time and Multiplication Time using Homomorphic Encryption (BFV scheme)
def compute_addition_and_multiplication(data):
    # Convert the byte data to a list of integers
    data_int = [int(byte) for byte in data]  # Convert byte data to integers

    # Measure memory and CPU usage before computation for HE
    memory_before, cpu_before = get_cpu_memory_usage_he()

    # Perform addition: Adding 1 to each byte
    start_addition_time = time.time()
    result_add = [x + 1 for x in data_int]
    addition_time = time.time() - start_addition_time

    # Perform multiplication: Multiply each byte by 2
    start_multiplication_time = time.time()
    result_mul = [x * 2 for x in data_int]
    multiplication_time = time.time() - start_multiplication_time

    # Measure memory and CPU usage after computation for HE
    memory_after, cpu_after = get_cpu_memory_usage_he()

    # Calculate throughput (MB/s)
    data_size_in_mb = len(data_int) / (1024 ** 2)  # File size in MB
    total_computation_time = addition_time + multiplication_time
    throughput = data_size_in_mb / total_computation_time if total_computation_time > 0 else 0

    return {
        "addition_time": addition_time,
        "multiplication_time": multiplication_time,
        "memory_before": memory_before,
        "memory_after": memory_after,
        "cpu_before": cpu_before,
        "cpu_after": cpu_after,
        "throughput": throughput
    }




# Route to render the index page (Homomorphic Encryption)
@app.route('/')
def index():
    # List all blob files in the container
    blob_list = container_client.list_blobs()
    files = [blob.name for blob in blob_list]
    return render_template('index.html', files=files)

# Route to render the traditional page
@app.route('/traditional')
def traditional():
    return render_template('traditional.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
