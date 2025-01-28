import asyncio
import copy
import yaml
from crawl import *
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


def fill_vector_db(llm_client, num_products: int):
    start = time.time()
    urls, markdowns = find_products(num_products)
    end = time.time()
    print(f"time to find products: {end - start:.2f}s")

    start = time.time()
    products = []
    for i in range(0, len(urls)):
        product_info = extract_product_info(markdowns[i], urls[i], llm_client)
        if product_info:
            products.append(product_info)
    end = time.time()
    print(f"time spent extracting product info from llm: {end - start:.2f}s")

    start = time.time()
    for product in products:
        print("adding " + product["Product Name"])
        document = f"""
        Product Name: {product['Product Name']}
        Product Description: {product['Product Description']}
        PartSelect Number: {product['PartSelect Number']}
        Manufacturer Part Number: {product['Manufacturer Part Number']}
        Manufactured by: {product['Manufactured by']}
        Manufactured for: {', '.join(product['Manufactured for'])}
        This part fixes the following symptoms: {', '.join(product['This part fixes the following symptoms'])}
        This part works with the following products: {', '.join(product['This part works with the following products'])}
        Part replaces these: {', '.join(product['Part replaces these'])}
        URL: {product['URL']}
        """

        embedding = embedding_model.encode(document)

        collection.add(
            documents=[document],
            embeddings=[embedding],
            metadatas=[
                {
                    "partselect_number": product["PartSelect Number"],
                    "manufacturer_part_number": product["Manufacturer Part Number"],
                    "manufacturer": product["Manufactured by"],
                    "url": product["URL"],
                }
            ],
            ids=[product["PartSelect Number"]],
        )
    end = time.time()
    print(f"time spent adding products to chromadb: {end - start:.2f}s")


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


def extract_product_info(markdown_content, url, llm_client):
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
