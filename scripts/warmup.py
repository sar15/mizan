#!/usr/bin/env python3
"""
Warmup Script: Pre-loads heavy ML models into RAM.
Run this BEFORE starting Streamlit to eliminate cold-start latency.
"""
import os
import sys
import time

def warmup():
    print("=" * 50)
    print("🔥 WARMUP: Pre-loading models into RAM...")
    print("=" * 50)
    
    start_time = time.time()
    
    # Force CPU mode
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    # 1. Warm up MizanEngine (BGE-M3 + Reranker)
    print("\n[1/3] Loading MizanEngine...")
    try:
        from mizan_engine import MizanEngine
        engine = MizanEngine()
        
        # Run dummy search to fully initialize
        print("      Running dummy search...")
        _ = engine.search("test warmup query", limit=1)
        print("      ✅ MizanEngine ready")
    except Exception as e:
        print(f"      ⚠️ MizanEngine warmup failed: {e}")
    
    # 2. Warm up DiscoveryEngine (UMAP + HDBSCAN)
    print("\n[2/3] Loading DiscoveryEngine...")
    try:
        from mizan_discovery import DiscoveryEngine
        discovery = DiscoveryEngine()
        
        # Trigger lazy imports
        _ = discovery._get_umap()
        _ = discovery._get_hdbscan()
        print("      ✅ DiscoveryEngine ready")
    except Exception as e:
        print(f"      ⚠️ DiscoveryEngine warmup failed: {e}")
    
    # 3. Verify Groq API (optional)
    print("\n[3/3] Verifying Groq API connection...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            print("      ✅ GROQ_API_KEY found")
        else:
            print("      ⚠️ GROQ_API_KEY not set")
    except Exception as e:
        print(f"      ⚠️ Groq check failed: {e}")
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"🚀 WARMUP COMPLETE in {elapsed:.1f}s")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = warmup()
    sys.exit(0 if success else 1)
