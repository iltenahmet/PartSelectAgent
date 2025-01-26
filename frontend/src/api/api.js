const API_URL = process.env.REACT_APP_API_URL;

export const getAIMessage = async (userQuery) => {
  try {
    const response = await fetch(`${API_URL}/api/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: userQuery }),
    });

    if (!response.ok) {
      throw new Error(`Error: ${response.status}`);
    }

    const data = await response.json();
    console.log(data);
    return { role: "agent", content: data.response };
  } catch (error) {
    console.error('Error fetching AI message:', error);
    return { role: "agent", content: "Error fetching message!"};
  }
};

