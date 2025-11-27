import sys
import mlx_lm.utils
import mlx_lm.tuner.utils
from mlx_lm.fuse import main as fuse_main

# Monkey patch to fix the num_layers bug
original_load_adapters = mlx_lm.tuner.utils.load_adapters

def patched_load_adapters(model, adapter_path):
    print(f"🔧 patched_load_adapters called for {adapter_path}")
    
    # Check for 'args' which is likely the config object in mlx models
    if hasattr(model, "args"):
        print("✅ Model has 'args' attribute.")
        config = model.args
        # Check if it's a SimpleNamespace or similar
        print(f"Config type: {type(config)}")
        
        if not hasattr(config, "num_layers"):
            print("⚠️ Config MISSING 'num_layers'")
            if hasattr(config, "num_hidden_layers"):
                print("found 'num_hidden_layers', patching...")
                config.num_layers = config.num_hidden_layers
                print("✅ Patched 'num_layers'")
            else:
                print("❌ 'num_hidden_layers' also missing!")
        else:
            print("✅ Config already has 'num_layers'")
            
    elif hasattr(model, "config"):
        # Fallback to config if args is not present (unlikely given previous run)
        print("✅ Model has 'config' attribute.")
        config = model.config
        if not hasattr(config, "num_layers") and hasattr(config, "num_hidden_layers"):
            config.num_layers = config.num_hidden_layers
            print("✅ Patched 'num_layers' on config")
            
    else:
        print("❌ Model does NOT have 'args' or 'config' attribute.")
            
    return original_load_adapters(model, adapter_path)

# Apply the patch to BOTH locations
mlx_lm.tuner.utils.load_adapters = patched_load_adapters
mlx_lm.utils.load_adapters = patched_load_adapters

if __name__ == "__main__":
    sys.argv = [
        "mlx_lm.fuse",
        "--model", "mlx-community/Meta-Llama-3-8B-Instruct-4bit",
        "--adapter-path", "mizan_scholar_adapter",
        "--save-path", "mizan_fused"
    ]
    
    print("🚀 Starting patched fuse process...")
    try:
        fuse_main()
    except Exception as e:
        print(f"❌ Fuse failed with error: {e}")
