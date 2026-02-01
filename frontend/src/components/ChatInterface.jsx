import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../api/client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';


/**
 * Chat Interface Component (GPS-001, GPS-002)
 * Handles conversation view and input.
 */
function ChatInterface({ sessionId, onSourceClick, onPartClick }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    // Initial load
    useEffect(() => {
        if (sessionId) {
            loadHistory(sessionId);
        }
    }, [sessionId]);

    const loadHistory = async (id) => {
        try {
            const session = await chatAPI.getSession(id);
            setMessages(session.messages || []);
        } catch (error) {
            console.error("Failed to load history:", error);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Core message sending logic
    const submitMessage = async (content) => {
        if (!content.trim() || !sessionId || loading) return;

        const userMsg = { role: 'user', content: content, created_at: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const response = await chatAPI.sendMessage(sessionId, userMsg.content);
            setMessages(prev => [...prev, response]);
        } catch (error) {
            console.error("Send failed:", error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "Error: Failed to get response.",
                isError: true
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        submitMessage(input);
    };

    // Custom renderer for code blocks to detect part numbers
    const CodeRenderer = ({ node, inline, className, children, ...props }) => {
        const text = String(children).replace(/\n$/, '');
        // Match D38999 or M39029 part numbers
        const isPartNumber = /^(D38999\/|M39029\/)/.test(text);

        if (inline && isPartNumber && onPartClick) {
            return (
                <button
                    className="part-link-btn"
                    onClick={() => onPartClick(text)}
                    title="Click to view details"
                >
                    {children}
                </button>
            );
        }

        return (
            <code className={className} {...props}>
                {children}
            </code>
        );
    };

    // Custom renderer for table rows to detect interactive options (GPS-010)
    const TableRowRenderer = ({ node, children, ...props }) => {
        // Safe recursive text extractor
        const getText = (n) => {
            if (!n) return '';
            if (typeof n === 'string') return n;
            if (n.value) return n.value; // Text node
            if (n.children) {
                return n.children.map(getText).join('');
            }
            return '';
        };

        // Check first cell content for marker
        const firstCell = node.children && node.children.find(c => c.tagName === 'td');
        if (!firstCell) return <tr {...props}>{children}</tr>; // Skip headers (th)

        const firstCellText = getText(firstCell);
        const isOption = firstCellText.includes('⚪');

        if (isOption && onPartClick) {
            // Extract description and code from other cells
            // Structure: | ⚪ | Code | Description |
            // children array in render contains the React elements, node.children has AST
            // We use node.children AST to get text content reliably
            const cells = node.children.filter(c => c.tagName === 'td');
            const code = cells[1] ? getText(cells[1]) : "";
            const description = cells[2] ? getText(cells[2]) : "this option";

            const handleOptionClick = () => {
                console.log("Selected Option:", code, description);
                submitMessage(`I need ${description} (${code})`);
            };

            return (
                <tr
                    className="interactive-option-row"
                    onClick={handleOptionClick}
                    title="Click to select this option"
                    {...props}
                >
                    {children}
                </tr>
            );
        }
        return <tr {...props}>{children}</tr>;
    };

    // Render message content with Markdown
    const renderContent = (msg) => {
        return (
            <div className="message-content markdown-body">
                <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                        code: CodeRenderer,
                        tr: TableRowRenderer
                    }}
                >
                    {msg.content}
                </ReactMarkdown>
            </div>
        );
    };

    return (
        <div className="chat-interface">
            <div className="messages-area">
                {messages.length === 0 && (
                    <div className="empty-state">
                        <div className="empty-icon">👋</div>
                        <h3>Welcome to Part Selector</h3>
                        <p>I can help you find D38999 connectors, decode part numbers, or answer technical questions.</p>

                        <div className="starter-prompts">
                            <button onClick={() => submitMessage("Help me find a D38999 connector")}>
                                🔍 Find a Connector
                            </button>
                            <button onClick={() => submitMessage("What is the difference between Series I, II, and III?")}>
                                📚 Explain Series Differences
                            </button>
                            <button onClick={() => submitMessage("I need a jam nut receptacle with 20 pins")}>
                                🔩 Specific Requirements
                            </button>
                            <button onClick={() => submitMessage("Start the Part Builder")}>
                                🔧 Open Part Builder
                            </button>
                        </div>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        <div className="message-bubble">
                            {renderContent(msg)}
                            {/* Render Citations if present (GPS-005) */}
                            {msg.meta_data && msg.meta_data.citations && (
                                <div className="citations">
                                    <small>Sources:</small>
                                    {msg.meta_data.citations.map((cite, i) => (
                                        <button
                                            key={i}
                                            className="citation-link"
                                            onClick={() => onSourceClick(cite)}
                                        >
                                            {cite.label || `Source ${i + 1}`}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="message-time">
                            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="message assistant loading">
                        <div className="typing-indicator">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="input-area" onSubmit={handleSend}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about parts (e.g., 'Find a jam nut receptacle...')"
                    disabled={loading || !sessionId}
                />
                <button type="submit" disabled={loading || !sessionId || !input.trim()} title="Send message">
                    ➤
                </button>
            </form>

            <style>{`
                .chat-interface {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    background: var(--bg-primary);
                }
                .messages-area {
                    flex: 1;
                    overflow-y: auto;
                    padding: 1rem;
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                }
                .message {
                    display: flex;
                    flex-direction: column;
                    max-width: 85%;
                }
                .message.user {
                    align-self: flex-end;
                    align-items: flex-end;
                }
                .message.assistant {
                    align-self: flex-start;
                    align-items: flex-start;
                }
                .message-bubble {
                    padding: 0.75rem 1rem;
                    border-radius: 12px;
                    background: var(--bg-tertiary);
                    color: var(--text-primary);
                    position: relative;
                    word-wrap: break-word;
                    font-size: 0.9rem;
                    line-height: 1.5;
                }
                .message.user .message-bubble {
                    background: var(--accent-primary);
                    color: white;
                    border-radius: 12px 12px 0 12px;
                }
                .message.assistant .message-bubble {
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-subtle);
                    border-radius: 12px 12px 12px 0;
                }

                .empty-state {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                    text-align: center;
                    padding: 2rem;
                    color: var(--text-secondary);
                }
                .empty-icon {
                    font-size: 3rem;
                    margin-bottom: 1rem;
                }
                .empty-state h3 {
                    margin-bottom: 0.5rem;
                    color: var(--text-primary);
                }
                .starter-prompts {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 0.75rem;
                    margin-top: 2rem;
                    width: 100%;
                    max-width: 500px;
                }
                .starter-prompts button {
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-subtle);
                    padding: 1rem;
                    border-radius: var(--radius-lg);
                    color: var(--text-primary);
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                    text-align: left;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    font-size: 0.9rem;
                }
                .starter-prompts button:hover {
                    background: var(--bg-tertiary);
                    border-color: var(--accent-primary);
                    transform: translateY(-2px);
                    box-shadow: var(--shadow-sm);
                }
                
                /* Markdown Styles */
                .markdown-body table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1rem 0;
                    font-size: 0.85rem;
                }
                .markdown-body th, .markdown-body td {
                    border: 1px solid var(--border-subtle);
                    padding: 0.5rem;
                    text-align: left;
                }
                .markdown-body th {
                    background: var(--bg-tertiary);
                    font-weight: 600;
                }
                .markdown-body p {
                    margin-bottom: 0.75rem;
                }
                .markdown-body p:last-child {
                    margin-bottom: 0;
                }
                .markdown-body ul, .markdown-body ol {
                    padding-left: 1.5rem;
                    margin-bottom: 0.75rem;
                }
                /* Code blocks in markdown */
                .markdown-body code {
                    background: rgba(0,0,0,0.2);
                    padding: 0.1rem 0.3rem;
                    border-radius: 3px;
                    font-family: var(--font-mono);
                    font-size: 0.85em;
                }
                .message.assistant .markdown-body code {
                    background: var(--bg-primary);
                    border: 1px solid var(--border-subtle);
                    color: var(--accent-primary);
                }
                .message.user .markdown-body code {
                    color: white;
                    background: rgba(255,255,255,0.2);
                }

                .message-time {
                    font-size: 0.7rem;
                    color: var(--text-muted);
                    margin-top: 0.25rem;
                }
                .input-area {
                    padding: 1rem;
                    border-top: 1px solid var(--border-subtle);
                    display: flex;
                    gap: 0.5rem;
                }
                .input-area input {
                    flex: 1;
                    padding: 0.75rem;
                    border-radius: 20px;
                    border: 1px solid var(--border-default);
                    background: var(--bg-secondary);
                    color: var(--text-primary);
                }
                .input-area button {
                    background: var(--accent-primary);
                    color: white;
                    border: none;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .input-area button:disabled {
                    background: var(--bg-tertiary);
                    cursor: not-allowed;
                }
                .citations {
                    margin-top: 0.5rem;
                    padding-top: 0.5rem;
                    border-top: 1px solid rgba(0,0,0,0.1);
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                    align-items: center;
                }
                .citation-link {
                    background: rgba(255,255,255,0.2);
                    border: 1px solid rgba(255,255,255,0.4);
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    cursor: pointer;
                    color: inherit;
                }
                .citation-link:hover {
                    background: rgba(255,255,255,0.3);
                }
                .typing-indicator span {
                    display: inline-block;
                    width: 6px;
                    height: 6px;
                    background: var(--text-muted);
                    border-radius: 50%;
                    margin: 0 2px;
                    animation: bounce 1s infinite;
                }
                .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
                .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
                @keyframes bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-5px); }
                }

                .part-link-btn {
                    background: rgba(99, 102, 241, 0.15);
                    border: 1px solid var(--accent-primary);
                    color: var(--accent-primary);
                    padding: 0 4px;
                    border-radius: 4px;
                    font-family: var(--font-mono);
                    font-size: 0.9em;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                .message.user .part-link-btn {
                    background: rgba(255, 255, 255, 0.2);
                    border-color: white;
                    color: white;
                }
                .part-link-btn:hover {
                    background: var(--accent-primary);
                    color: white;
                    text-decoration: none;
                }
                .message.user .part-link-btn:hover {
                    background: white;
                    color: var(--accent-primary);
                }

                /* Interactive Option Rows (GPS-010) */
                .interactive-option-row {
                    cursor: pointer;
                    transition: background-color 0.2s ease;
                }
                .interactive-option-row:hover {
                    background-color: rgba(99, 102, 241, 0.1) !important;
                }
                .interactive-option-row:active {
                    background-color: rgba(99, 102, 241, 0.2) !important;
                }
                .interactive-option-row td:first-child {
                    text-align: center;
                    font-size: 1.2em;
                }
            `}</style>
        </div>
    );
}

export default ChatInterface;
