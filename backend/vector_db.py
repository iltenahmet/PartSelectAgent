import re
import copy
import yaml
from chromadb import chromadb
from sentence_transformers import SentenceTransformer

persist_directory = "./chroma_persistent_data"
client = chromadb.PersistentClient(path=persist_directory)

collection_name = "product_support"
collection = client.get_or_create_collection(collection_name)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

messages_template = [
    {
        "role": "user",
        "content": (
            """
            Extract the following information from the product page markdown content. Return the data in a strict YAML format, don't put ```:

            Product Name:
            Product Description:
            PartSelect Number:
            Manufacturer Part Number:
            Manufactured by:
            Manufactured for:
            This part fixes the following symptoms:
            This part works with the following products:
            Part replaces these:

            Markdown content:
            ---
            {markdown_content}

            Strict YAML format:
            ---
            Product Name: "..."
            Product Description: "..."
            PartSelect Number: "..."
            Manufacturer Part Number: "..."
            Manufactured by: "..."
            Manufactured for:
            - "..."
            - "..."
            This part fixes the following symptoms:
            - "..."
            - "..."
            This part works with the following products:
            - "..."
            - "..."
            Part replaces these:
            - "..."
            - "..."
            """
        ),
    }
]


def add_to_vector_db(product_markdown: str, url: str, llm_client):
    match = re.search(r"PS(\d{8})", url)
    if match and collection.get(ids=match.group(0)):
        print(f"Product with id {match.group(0)} already exists in the database, skipping!")
        return

    product_info = extract_product_info(product_markdown, url, llm_client)

    document = f"""
    Product Name: {product_info['Product Name']}
    Product Description: {product_info['Product Description']}
    PartSelect Number: {product_info['PartSelect Number']}
    Manufacturer Part Number: {product_info['Manufacturer Part Number']}
    Manufactured by: {product_info['Manufactured by']}
    Manufactured for: {', '.join(product_info['Manufactured for'])}
    This part fixes the following symptoms: {', '.join(product_info['This part fixes the following symptoms'])}
    This part works with the following products: {', '.join(product_info['This part works with the following products'])}
    Part replaces these: {', '.join(product_info['Part replaces these'])}
    URL: {product_info['URL']}
    """

    embedding = embedding_model.encode(document)

    collection.add(
        documents=[document],
        embeddings=[embedding],
        metadatas=[
            {
                "partselect_number": product_info["PartSelect Number"],
                "manufacturer_part_number": product_info["Manufacturer Part Number"],
                "manufacturer": product_info["Manufactured by"],
                "url": product_info["URL"],
            }
        ],
        ids=[product_info["PartSelect Number"]],
    )

    print(f"Add {product_info['Product Name']}, vector-db now has {collection.count()} items.")


def query_chroma(query, top_n=2):
    query_embedding = embedding_model.encode(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_n,  # Number of results to retrieve
    )

    print(f"Top {top_n} results for the query: '{query}'")
    for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
        print(f"\nResult {i+1}:")
        print(f"Document:\n{doc}")
        print(f"Metadata:\n{meta}")


def extract_product_info(markdown_content, url, llm_client) -> dict:
    messages = copy.deepcopy(messages_template)
    messages[0]["content"] = messages[0]["content"].format(
        markdown_content=markdown_content
    )

    completion = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    result = completion.choices[0].message.content

    data = validate_and_parse_yaml(result)
    if data:
        data["URL"] = url

    return data


def validate_and_parse_yaml(text):
    try:
        data = yaml.safe_load(text)
        return data
    except yaml.YAMLError as e:
        print("YAML Parsing Error:", e)
        return None
