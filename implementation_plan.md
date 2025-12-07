# Implementation Plan: Permanent Token Limit Fix

## 🔴 The Problem

**Error:** `413 - Request too large for model`
- **Token Limit:** Groq Free Tier = 12,000 TPM (tokens per minute)
- **Your Request:** 28,887 tokens (2.4x over limit!)
- **Query:** "story of musa and khidr"

---

## 🔍 Root Cause Analysis

### Current Data Flow
```
User Query → MizanEngine → Qdrant (100 candidates) → Reranker (Top 5) → mizan_rag.py → Build Context (NO LIMIT!) → Groq API → 💥 413 ERROR
```

### Why It Crashes
| Component | Content Size |
|-----------|--------------|
| Arabic Verse | ~50-100 tokens |
| Translation | ~50-150 tokens |
| **Tafsir** | **2,000-5,000 tokens** ← KILLER |
| **5 Results** | **10,000-25,000 tokens** |
| System Prompt | ~200 tokens |
| **Total** | **~28,000+ tokens** |

### The Culprit Code (mizan_rag.py:72-82)

```python
# CURRENT - NO TOKEN LIMIT!
for res in results:
    payload = res['payload']
    original_id = payload.get('id', str(res['id']))
    content = payload.get('content', '')  # ← Can be 5000+ tokens!
    context_text += f"Source ID: <{original_id}>\nContent: {content}\n\n"
```

---

## ✅ Proposed Solution

### Architecture Change

```
User Query → MizanEngine → Qdrant (100) → Reranker (Top 5) → NEW: TokenBudgetManager → Smart Truncation → Context ≤ 8000 tokens → Groq API → ✅ SUCCESS
```

---

## Proposed Changes

### [MODIFY] mizan_rag.py

#### 1. Add Token Estimation Function
```python
def estimate_tokens(text: str) -> int:
    """
    Estimate token count using word-based heuristic.
    ~1.3 tokens per word for English, ~2 for Arabic.
    """
    if not text:
        return 0
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    words = len(text.split())
    return int(words * 1.3 + arabic_chars * 0.5)
```

#### 2. Add Smart Context Builder

- MAX_CONTEXT_TOKENS = 8000 (safe budget)
- MAX_SINGLE_DOC_TOKENS = 2000 (no single doc can exceed this)
- Truncate long tafsir intelligently
- Stop adding documents when budget is reached

---

## Verification Plan

1. Test with the problematic query: "story of musa and khidr"
2. Verify no 413 error
3. Verify answer quality is maintained

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Token Control | ❌ None | ✅ 8000 token budget |
| Single Doc Limit | ❌ Unlimited | ✅ 2000 tokens max |
| Error Handling | ❌ Crash | ✅ Graceful truncation |

This is a **permanent architectural fix** that will work for ANY query.
