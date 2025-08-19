import os
import json
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

class InventoryRAG:
    """Builds a vector index over inventory data and retrieves relevant products."""
    def __init__(self, inventory_path: str, embedding_model_path: str, index_dir: str, use_gpu: bool = True):
        with open(inventory_path, 'r') as f:
            self.items = json.load(f)

        if not os.path.isdir(embedding_model_path):
            raise FileNotFoundError(
                f"Embedding model not found at {embedding_model_path}. Download a SentenceTransformers model to this folder."
            )

        # ✅ Force SentenceTransformer to use GPU if available
        device = "cuda" if (use_gpu and faiss.get_num_gpus() > 0) else "cpu"
        self.model = SentenceTransformer(embedding_model_path, device=device)

        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)
        self.index_path = os.path.join(index_dir, "faiss.index")
        self.meta_path = os.path.join(index_dir, "meta.json")

        if os.path.isfile(self.index_path) and os.path.isfile(self.meta_path):
            self._load_index()
        else:
            self._build_index()

    def _texts(self) -> List[str]:
        return [f"{it['name']} | {it['description']} | price {it['price']}" for it in self.items]

    def _build_index(self):
        emb = self.model.encode(
            self._texts(),
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True
        )

        dim = emb.shape[1]
        cpu_index = faiss.IndexFlatIP(dim)

        # ✅ Move FAISS index to GPU with pre-allocated memory if available
        if faiss.get_num_gpus() > 0:
            res = faiss.StandardGpuResources()
            res.setTempMemory(512 * 1024 * 1024)  # 512MB pinned memory
            self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
        else:
            self.index = cpu_index

        self.index.add(emb.astype('float32'))
        faiss.write_index(faiss.index_gpu_to_cpu(self.index) if faiss.get_num_gpus() > 0 else self.index, self.index_path)

        with open(self.meta_path, 'w') as f:
            json.dump({"dim": dim}, f)

    def _load_index(self):
        cpu_index = faiss.read_index(self.index_path)

        # ✅ Move FAISS index to GPU with pre-allocated memory if available
        if faiss.get_num_gpus() > 0:
            res = faiss.StandardGpuResources()
            res.setTempMemory(512 * 1024 * 1024)  # 512MB pinned memory
            self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
        else:
            self.index = cpu_index

    def search(self, query: str, k: int = 3) -> List[Tuple[Dict, float]]:
        q = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        if not hasattr(self, 'index'):
            self._load_index()

        D, I = self.index.search(q.astype('float32'), k)
        results = []
        for idx, score in zip(I[0], D[0]):
            if idx == -1:
                continue
            results.append((self.items[idx], float(score)))
        return results
