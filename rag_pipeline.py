"""
RAG Pipeline
------------
Ye file RAG (Retrieval Augmented Generation) ka core logic handle karti hai:

1. CHUNKING: Articles ko chhote pieces mein todna (bahut lamba text ek saath
   process karna mushkil hai, aur chote chunks se relevant info dhoondhna easy hota hai)

2. EMBEDDING: Har chunk ko ek vector (numbers ki list) mein convert karna.
   Ye vector text ka 'meaning' capture karta hai - similar meaning wale
   texts ke vectors bhi similar hote hain (chahe words alag ho).
   Hum 'sentence-transformers' library use karenge - ye FREE hai aur
   local (aapke computer) pe hi chalta hai, koi API key nahi chahiye.

3. VECTOR STORE (FAISS): Saare vectors ko ek searchable index mein store karna.
   FAISS Facebook ki library hai jo lakhs vectors mein se bhi milliseconds
   mein sabse similar vectors dhoond leti hai.

4. RETRIEVAL: User ke sawaal ka vector banake, us se sabse milte-julte
   chunks nikalna.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Ye model chhota (80MB) aur fast hai, phir bhi accurate embeddings deta hai
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


class NewsRAGStore:
    def __init__(self, model=None):
        # Agar pehle se loaded model diya gaya hai (caching ke liye), use karo.
        # Warna naya load karo (ye slow step hai - isliye caching zaroori hai).
        self.model = model if model is not None else SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.index = None
        self.chunks = []  # Har chunk ka actual text yahan store hoga
        self.chunk_metadata = []  # Har chunk kis article se aaya, wo info

    @staticmethod
    def chunk_article(article, chunk_size=300):
        """
        Ek article ko chunks mein todta hai.
        Simple approach: title + summary ko ek chunk maan lete hain
        (news summaries usually already chhote hote hain, isliye
        complex splitting ki zaroorat nahi).
        """
        text = f"{article['title']}. {article['summary']}"
        return [text]

    def build_index(self, articles):
        """
        Saare articles se chunks banake, unke embeddings nikalke,
        FAISS index mein store karta hai.
        """
        self.chunks = []
        self.chunk_metadata = []

        for article in articles:
            article_chunks = self.chunk_article(article)
            for chunk_text in article_chunks:
                self.chunks.append(chunk_text)
                self.chunk_metadata.append({
                    "source": article["source"],
                    "link": article["link"],
                    "title": article["title"],
                })

        if not self.chunks:
            return

        # Saare chunks ko ek saath embeddings mein convert karo (batch processing - fast)
        embeddings = self.model.encode(self.chunks, show_progress_bar=False)
        embeddings = np.array(embeddings).astype("float32")

        # FAISS index banao - IndexFlatL2 sabse simple type hai (exact search, chhote data ke liye perfect)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

    def retrieve(self, query, top_k=5):
        """
        User ke query se sabse relevant top_k chunks nikalta hai,
        har ek ke saath ek 'confidence score' (0-100%) jo batata hai
        kitna relevant hai ye chunk query ke liye.
        """
        if self.index is None or len(self.chunks) == 0:
            return []

        query_embedding = self.model.encode([query]).astype("float32")
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                # FAISS L2 distance ko ek approximate 0-100% confidence score
                # mein convert kar rahe hain - jitni kam distance, utna zyada
                # relevant. Ye exact probability nahi hai, ek relative measure hai.
                confidence = round(100 / (1 + float(dist)), 1)
                results.append({
                    "text": self.chunks[idx],
                    "metadata": self.chunk_metadata[idx],
                    "score": confidence,
                })
        return results
