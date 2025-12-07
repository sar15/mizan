import os
from huggingface_hub import snapshot_download

def download_models():
    print("Starting Model Downloads...")
    
    # 1. BGE-M3
    print("\n[1/2] Downloading BAAI/bge-m3...")
    snapshot_download(repo_id="BAAI/bge-m3", resume_download=True)
    print("BGE-M3 Downloaded.")
    
    # 2. BGE-Reranker-v2-m3
    print("\n[2/2] Downloading BAAI/bge-reranker-v2-m3...")
    # This is the big one (~2.2GB)
    snapshot_download(repo_id="BAAI/bge-reranker-v2-m3", resume_download=True)
    print("BGE-Reranker Downloaded.")
    
    print("\nAll models ready.")

if __name__ == "__main__":
    download_models()
