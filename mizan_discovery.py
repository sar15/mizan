import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings

# Suppress UMAP/HDBSCAN warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Stability Constants
MIN_SAMPLES_FOR_CLUSTERING = 6  # UMAP n_neighbors=5 requires at least 6 samples

class DiscoveryEngine:
    """
    Phase 3 Discovery Engine: Clusters search results into themes.
    Tech: UMAP (dimensionality reduction) + HDBSCAN (clustering) + TF-IDF (labeling)
    """
    
    def __init__(self):
        self._umap = None
        self._hdbscan = None
        
    def _get_umap(self):
        if self._umap is None:
            import umap
            self._umap = umap.UMAP(
                n_components=5,
                n_neighbors=5,
                min_dist=0.1,
                metric='cosine',
                random_state=42
            )
        return self._umap
        
    def _get_hdbscan(self):
        if self._hdbscan is None:
            import hdbscan
            self._hdbscan = hdbscan.HDBSCAN(
                min_cluster_size=2,
                min_samples=1,
                metric='euclidean',
                cluster_selection_epsilon=0.5
            )
        return self._hdbscan

    def cluster_results(
        self, 
        results: List[Dict[str, Any]], 
        vectors: List[List[float]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Clusters search results into themes.
        
        STABILITY FIX: Skips clustering if < 6 results (UMAP requirement).
        """
        # STABILITY: Check minimum samples for UMAP
        if len(results) < MIN_SAMPLES_FOR_CLUSTERING:
            return {"All Results": results}
            
        if len(vectors) != len(results):
            return {"All Results": results}
            
        try:
            # 1. Dimensionality Reduction (1024D -> 5D)
            vectors_np = np.array(vectors)
            umap_model = self._get_umap()
            reduced = umap_model.fit_transform(vectors_np)
            
            # 2. Clustering
            hdbscan_model = self._get_hdbscan()
            labels = hdbscan_model.fit_predict(reduced)
            
            # 3. Group results by cluster
            clusters: Dict[int, List[Dict[str, Any]]] = {}
            for idx, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(results[idx])
            
            # 4. Generate labels using TF-IDF
            themed_clusters: Dict[str, List[Dict[str, Any]]] = {}
            
            for cluster_id, cluster_results in clusters.items():
                if cluster_id == -1:
                    theme_name = "Uncategorized"
                else:
                    texts = [r['payload'].get('content', '') for r in cluster_results]
                    theme_name = self._generate_theme_label(texts, cluster_id)
                    
                themed_clusters[theme_name] = cluster_results
                
            return themed_clusters
            
        except Exception as e:
            print(f"[DISCOVERY] Clustering failed: {e}")
            return {"All Results": results}
    
    def _generate_theme_label(self, texts: List[str], cluster_id: int) -> str:
        """Generate a theme label using TF-IDF keywords."""
        if not texts:
            return f"Theme {cluster_id + 1}"
            
        try:
            combined = " ".join(texts)
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2)
            )
            vectorizer.fit(texts)
            tfidf_matrix = vectorizer.transform([combined])
            
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            top_indices = scores.argsort()[-3:][::-1]
            top_keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
            
            if top_keywords:
                return f"Theme: {', '.join(top_keywords[:2]).title()}"
            else:
                return f"Theme {cluster_id + 1}"
                
        except Exception:
            return f"Theme {cluster_id + 1}"


if __name__ == "__main__":
    discovery = DiscoveryEngine()
    
    # Test with < 6 results (should NOT crash)
    mock_results = [
        {"payload": {"content": "Patience", "id": "v1"}},
        {"payload": {"content": "Prayer", "id": "v2"}},
    ]
    mock_vectors = [[0.1] * 1024, [0.9] * 1024]
    
    clusters = discovery.cluster_results(mock_results, mock_vectors)
    print(f"Small dataset test: {list(clusters.keys())}")  # Should be "All Results"
