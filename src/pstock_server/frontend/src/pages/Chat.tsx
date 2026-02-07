/**
 * Chat Page
 *
 * Interactive chat interface with an agent.
 */
import { type FC, useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { ConfigPanel } from '../components/ConfigPanel';
import { agentsApi, chatApi, AgentInfo, StepData } from '../api/client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  steps?: StepData[];
}

export const Chat: FC = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();

  const [agent, setAgent] = useState<AgentInfo | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentSteps, setCurrentSteps] = useState<StepData[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamEnabled, setStreamEnabled] = useState(true);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadAgent = async () => {
      if (!agentId) return;

      try {
        const data = await agentsApi.get(agentId);
        setAgent(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load agent');
      }
    };

    loadAgent();
  }, [agentId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentSteps]);

  const handleSendMessage = async (message: string) => {
    if (!agent || isStreaming) return;

    // Add user message
    const userMessage: Message = { role: 'user', content: message };
    setMessages((prev) => [...prev, userMessage]);

    // Reset streaming state
    setCurrentSteps([]);
    setIsStreaming(true);
    setError(null);

    try {
      if (streamEnabled) {
        // Streaming chat
        const stepsBuffer: StepData[] = [];

        chatApi.streamChat(
          agent.id,
          { message, session_id: sessionId },
          (event) => {
            if (event.type === 'step' && event.step) {
              stepsBuffer.push(event.step);
              setCurrentSteps((prev) => [...prev, event.step!]);
            } else if (event.type === 'final') {
              setMessages((prev) => [
                ...prev,
                {
                  role: 'assistant',
                  content: event.content,
                  steps: [...stepsBuffer],
                },
              ]);
              setCurrentSteps([]);
              stepsBuffer.length = 0;
              if (event.session_id) {
                setSessionId(event.session_id);
              }
            } else if (event.type === 'error') {
              setError(event.content);
            }
          },
          (err) => {
            setError(err.message);
            setIsStreaming(false);
          },
          () => {
            setIsStreaming(false);
          },
        );
      } else {
        // Non-streaming chat
        const response = await chatApi.chat(agent.id, { message, session_id: sessionId });
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.response,
            steps: response.steps,
          },
        ]);
        setSessionId(response.session_id);
        setIsStreaming(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setIsStreaming(false);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-2">Error</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Back to Marketplace
          </button>
        </div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col" style={{ marginRight: agent ? '320px' : '0' }}>
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => navigate('/')}
                className="text-blue-500 hover:text-blue-600 text-sm mb-1"
              >
                ← Back to Marketplace
              </button>
              <h1 className="text-2xl font-bold text-gray-900">{agent.name}</h1>
              <p className="text-sm text-gray-600">{agent.description}</p>
            </div>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={streamEnabled}
                  onChange={(e) => setStreamEnabled(e.target.checked)}
                  disabled={isStreaming}
                  className="rounded border-gray-300 text-blue-500 focus:ring-blue-500"
                />
                Streaming
              </label>
            </div>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-500">
                <div className="text-4xl mb-2">💬</div>
                <p>Start a conversation with {agent.name}</p>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, index) => (
                <ChatMessage key={index} {...msg} />
              ))}
              {isStreaming && currentSteps.length > 0 && (
                <ChatMessage
                  role="assistant"
                  content=""
                  steps={currentSteps}
                  isStreaming={true}
                />
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <ChatInput onSend={handleSendMessage} disabled={isStreaming} />
        </div>
      </div>

      {/* Config Panel */}
      <ConfigPanel
        name={agent.name}
        description={agent.description}
        config={agent.config}
        tools={agent.tools}
        skills={agent.skills}
        subagents={agent.subagents}
      />
    </div>
  );
};
