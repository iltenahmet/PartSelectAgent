'''
This file is responsible for handling queries and insertions to our vector database: ChromaDB
It is also responsible for making the necessary LLM calls to extract product information before inserting data into the database.
'''

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

# Make sure all the information is in strict YAML format for ease of processing
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
    '''
    Add product information to the database, given the product information in markdown format, and the product url
    '''

    # LLM call to get the product information
    product_info = extract_product_info(product_markdown, url, llm_client)
    print("adding to vector db " + product_info["Product Name"])

    # Create the document to add to the database
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

    # Create and add the embedding and the metadata
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

    print(
        f"Add {product_info['Product Name']}, vector-db now has {collection.count()} items."
    )


def is_in_vector_db(url: str) -> bool:
    '''
    Returns whether a product is in the database or not
    Takes in a url and extracts the product number to check for an exact match
    '''
    match = re.search(r"PS(\d{8})", url)
    if not match:
        return False

    result = collection.get(ids=match.group(0))
    return len(result.get("ids")) > 0


def query_chroma(query, top_n=4):
    '''
    Query the the database
    '''
    query_embedding = embedding_model.encode(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_n,
    )

    return results


def query_chroma_with_exact_id(id: str) -> str:
    '''
    Query the database with an exact product number
    '''
    result = collection.get(ids=id)
    if result and "documents" in result and len(result["documents"]) > 0:
        first_document = result["documents"][0]
        return str(first_document)
    else:
        return ""


def extract_product_info(markdown_content, url, llm_client) -> dict:
    '''
    Queries the LLM to extract product information. Expects the LLM response to be in strict YAML format.
    Then validates and parses the YAML text.

    NOTE: LLM call to extract each product information is costly and slow, this can be optimized by manual string parsing instead. 
    However, then the parsing algorithm may need to be updated if there are changes to the way the website is organized. 
    '''
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
