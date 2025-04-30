README.md

Title: Performance Evaluation of Homomorphic Encryption Parameter Tuning for Secure Cloud Data ProcessingAuthor: Sanon IsoobaRepository: https://github.com/elte-cybersec/HE-Evaluation

# Project Motivation and Scope

This project demonstrates a practical implementation of client-cloud privacy-preserving data computation using Homomorphic Encryption (HE) and traditional cryptographic techniques. The goal is to evaluate how BFV scheme parameters affect the performance of HE under real cloud conditions (Azure) and compare it with AES, RSA-AES, Blowfish, and ChaCha20. The study contributes to ongoing research on balancing performance and security in secure cloud data processing.

## Key Features

HE Parameter Tuning: Enables testing various poly_modulus_degree and plain_modulus values using TenSEAL (based on Microsoft SEAL).

Traditional Cryptography Integration: Supports AES, RSA-AES, Blowfish, and ChaCha20 algorithms.

Cloud-Hosted Computation: Secure computation executed on encrypted or plaintext data using a web-based Azure-hosted app.

Performance Metrics: Captures encryption/decryption time, CPU/memory usage, and throughput.

Resource Monitoring: Integrated with psutil to monitor runtime CPU and memory usage.

# Repository Contents

- Item Client_HE_Parameter.py

Encrypts files using TenSEAL's BFV scheme.

Allows parameter tuning and uploads ciphertext/context to Azure Blob Storage.

- Item Client_traditionalweb.py

Encrypts/decrypts files using traditional cryptographic schemes.

GUI prompts user to select algorithm and measures encryption/decryption time.

- Item Server_HE_trad_compute.py

Web-based interface (Flask) hosted on Azure VM.

Downloads encrypted data from Azure Blob and runs either:

Homomorphic computation on ciphertext (with TenSEAL)

Plaintext computation after decryption (for traditional algorithms)

Logs performance metrics and returns to client.

## Setup Instructions

1. Create Python Virtual Environment

<pre> '''python -m venv venv '''</pre>
source venv/bin/activate  # On Windows: venv\Scripts\activate

2. Clone the Project

git clone https://github.com/elte-cybersec/HE-Evaluation.git
cd HE-Evaluation

3. Install Requirements

pip install -r requirements.txt

## Running the Project

Client-side Encryption

python Client_HE_Parameter.py  # For HE encryption
python Client_traditionalweb.py  # For AES, RSA-AES, etc.

Server-side (hosted in Azure VM)

python Server_HE_trad_compute.py

Navigate to http://<your_vm_ip>:80 in a browser to access the web UI.

## Performance Metrics Captured

Encryption Time (s)

Decryption Time (s)

Addition Time (s) and Multiplication Time (s)

CPU Usage (%) before and after computation

Memory Usage (MB) before and after computation

Throughput (MB/s)

## Practical Notes

Cloud Runtime: Hosted in a Windows Azure VM with 16GB RAM and 4 CPUs.

File Sizes Tested: Experiments were performed on 2MB and 5MB files.

Parameter Sets: BFV evaluated across 6 parameter sets with varying n and p values.

Security Advantage: HE preserves data privacy during computation; traditional schemes expose data during computation phase.
Add professional README.md with project structure and setup instructions
