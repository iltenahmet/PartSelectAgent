import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage, resetSession } from "../api/api";
import { marked } from "marked";

function ChatWindow() {

  const defaultMessage = [{
    role: "assistant",
    content: "Hi, how can I help you today?"
  }];

  const [enableBrowsing, setEnableBrowsing] = useState(false);

  const [messages, setMessages] = useState(defaultMessage)
  const [input, setInput] = useState("");

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const toggleBrowsing = () => {
    setEnableBrowsing(prevState => !prevState);
  };

  const handleSend = async (input) => {
    if (input.trim() !== "") {
      // Set user message
      setMessages(prevMessages => [...prevMessages, { role: "user", content: input }]);
      setInput("");

      // Call API & set assistant message
      const newMessage = await getAIMessage(input, enableBrowsing);
      setMessages(prevMessages => [...prevMessages, newMessage]);
    }
  };

  const handleResetMemory = async () => {
      await resetSession();
      setMessages([]); 
  };

  return (
    <div className="messages-container">
      {messages.map((message, index) => (
        <div key={index} className={`${message.role}-message-container`}>
          {message.content && (
            <div className={`message ${message.role}-message`}>
              <div dangerouslySetInnerHTML={{ __html: marked(message.content).replace(/<p>|<\/p>/g, "") }}></div>
            </div>
          )}
        </div>
      ))}
      <div ref={messagesEndRef} />
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          onKeyPress={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              handleSend(input);
              e.preventDefault();
            }
          }}
          rows="3"
        />
        <button className="send-button" onClick={() => handleSend(input)}>
          Send
        </button>
        <button onClick={handleResetMemory}>Reset Memory</button>
        <div className="slider-container">
          <label htmlFor="browsing-toggle">Enable Browsing</label>
          <input
            type="checkbox"
            id="browsing-toggle"
            checked={enableBrowsing}
            onChange={toggleBrowsing}
          />
        </div>
      </div>
    </div>
  );
}

export default ChatWindow;
