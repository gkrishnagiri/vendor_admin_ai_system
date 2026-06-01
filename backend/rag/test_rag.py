from retriever import search

results = search("how to start backend")

for r in results:
    print("\n---\n", r)