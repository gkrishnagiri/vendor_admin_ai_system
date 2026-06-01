from rag.retriever import search

query = "how to create a user"

result = search(query, top_k=5)

print("\nQUERY:", result["query"])

print("\n--- ANSWER ---\n")
print(result["answer"])

print("\n--- SOURCES ---\n")
for s in result["sources"]:
    print(s)