import json
from searchPartTool import search_partselect


tools = [
    {
        "type": "function",
        "function": {
            "name": "search_partselect",
            "description": "Search PartSelect for information about a specific part number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "part_number": {
                        "type": "string",
                        "description": "The part number to search for.",
                    }
                },
                "required": ["part_number"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]

success_agent_message = {
    "role": "system",
    "content": (
        "You are a customer success agent for the PartSelect e-commerce website. "
        "Your role is to provide accurate information and assistance related to refrigerator and dishwasher parts. "
        "If the user provides a part number, use the search_partselect function to find information about it. "
        "You can help customers identify compatible parts, provide installation instructions, offer troubleshooting advice, and assist with transactions. "
        "Do not answer questions outside this scope. Focus on providing efficient, clear, user-friendly, and concise responses."
        "Return your output in plain text format, don't use any markdown elements, make sure your answer doesn't have extra newline elements"
    ),
}


def query_customer_agent(query: str, llm_client):
    messages = [
        success_agent_message,
        {"role": "user", "content": query},
    ]
    completion = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    response = completion.choices[0].message
    if not response.tool_calls:
        return response.content

    args = json.loads(response.tool_calls[0].function.arguments)
    result = search_partselect(args["part_number"])
    messages.append(response)
    messages.append(
        {
            "role": "tool",
            "tool_call_id": response.tool_calls[0].id,
            "content": result,
        }
    )
    completion_after_search = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )

    return completion_after_search.choices[0].message.content
