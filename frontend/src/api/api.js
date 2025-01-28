const API_URL = process.env.REACT_APP_API_URL;

export const getAIMessage = async (userQuery, enableBrowsing) => {
  try {
    const response = await fetch(`${API_URL}/api/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: userQuery, enable_browsing: enableBrowsing }),
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

export const resetSession = async () => {
  try {
    const response = await fetch(`${API_URL}/api/reset_session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to reset session');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error resetting session:', error);
  }
};