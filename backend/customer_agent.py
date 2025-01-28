import json
import re
from search_part_tool import search_partselect
from vector_db import query_chroma, query_chroma_with_exact_id

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


system_prompt = {
    "role": "system",
    "content": """
    You are a customer success agent for the PartSelect e-commerce website.
    Your role is to provide accurate information and assistance related to refrigerator and dishwasher parts.
    You can help customers identify compatible parts, provide installation instructions, offer troubleshooting advice, and assist with transactions.
    Do not answer questions outside this scope. Focus on providing accurate, clear, user-friendly, and concise responses.
    Format all answers concisely without extra spaces or line breaks.

    Here are some example interactions:

    Question: "How can I install part number PS11701542?
    Answer:
    The W10864081 is a door gasket or seal for your dishwasher. It forms a watertight barrier between the door and the dishwasher tub, preventing water from leaking during the wash cycle. If you're installing this seal, follow these general steps:
        1) Remove the Old Seal: Simply pull the old seal out of the groove around the dishwasher tub opening.
        2) 2) Clean the Area: Before installing the new seal, clean the area to remove any food particles or debris to ensure a proper fit.
        3) Install the New Seal: Start by pressing the new seal into the groove at the top center of the dishwasher tub and work your way around, ensuring it is seated evenly.
        4) Check the Fit: Close the dishwasher door to make sure the new seal fits correctly and doesn't impede the door from closing.
    This repair is considered to be easy and typically takes 30 to 60 minutes. Make sure to check that the seal is snug throughout and is not twisted. If you encounter any issues with leaks continuing, ensure the seal is seated properly and consider checking other areas for wear.

    Question: The ice maker on my Whirlpool fridge is not working. How can I fix it?",
    Answer:
    If your Whirlpool fridge's ice maker is not working, here's a troubleshooting guide to help you fix it:
    Check the Water Supply: Ensure that the water supply valve is turned on and that there are no kinks in the water line. If the water line becomes blocked or frozen, it could prevent water from reaching the ice maker.
    Inspect the Water Filter: If the water filter is clogged, it can reduce water flow to the ice maker. Consider replacing the filter every 6 months or sooner if you notice reduced water flow. For your Whirlpool fridge, compatible water filter replacements include models like EDR1RXD1 (PartSelect Number PS11701542, link: Whirlpool EDR1RXD1) or EDR4RXD1 (PartSelect Number PS11722130, link: Whirlpool EDR4RXD1).
    Examine the Ice Maker Unit: Check for any visible obstructions or ice clogs in the ice maker unit. Sometimes, cubes that fail to eject can jam the ice maker.
    Evaluate the Temperature: Ensure that the temperature inside the freezer is set correctly. If it's too high, the ice maker may not produce ice.
    Test the Ice Maker Components: Consider testing components such as the ice maker control module, door switch, and water inlet valve. These parts can fail and prevent ice production.
    Reset the Ice Maker: Some ice makers have a reset button. Follow the manufacturer's instructions to reset the unit if available.
    If you've tried these steps and the ice maker is still not working, the issue may require professional service to diagnose and repair any internal faults.
    """,
}

search_prompt = {
    "role": "system",
    "content": "You can use the search_partselect function to find information about a part if the user provides the part number. Only use this if you don't have any information about the part.",
}

no_search_prompt = {
    "role": "system",
    "content": "A tool that would help you browse PartSelect for information about a specific part number is disabled. If you can't find any relevant information about the specified part, instruct user to enable the browsing functionality, so that you can browse the PartSelect website to retrieve what they need.",
}


def query_customer_agent(query: str, chat_history, llm_client, enable_browse: bool):
    chroma_context = ""

    match = re.search(r'PS\d{8}', query)
    if match:
        chroma_context += query_chroma_with_exact_id(match.group())

    results = query_chroma(query, 25)
    if results["documents"]:
        flattened_documents = [
            doc for sublist in results["documents"] for doc in sublist
        ]
        chroma_context += "\n\n".join(flattened_documents)

    if len(chroma_context) > 0:
        context_message = f"The following context was retrieved from the database to assist with the query:\n{chroma_context}"
    else:
        context_message = "No relevant context was found in the database for the query."

    messages = [
        system_prompt,
        search_prompt if enable_browse else no_search_prompt,
        *chat_history,
        {"role": "system", "content": context_message},
        {"role": "user", "content": query},
    ]

    completion = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools if enable_browse else None,
        tool_choice="auto" if enable_browse else None,
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
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
    )

    return completion_after_search.choices[0].message.content
