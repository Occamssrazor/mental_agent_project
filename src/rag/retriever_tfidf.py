import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class MentalRetriever:
    def __init__(self, database_path: str):
        with open(database_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.texts = [
            f"{x.get('title','')} {x.get('description','')} {' '.join(x.get('tags',[]))} {x.get('when_to_use','')}"
            for x in self.data
        ]
        self.vectorizer = TfidfVectorizer(stop_words=None)
        self.vectors = self.vectorizer.fit_transform(self.texts)

    def retrieve(self, query: str, top_k: int = 5):
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.vectors)[0]
        idx = np.argsort(sims)[::-1][:top_k]
        return [self.data[i] for i in idx]
