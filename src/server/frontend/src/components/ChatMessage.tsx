/**
 * ChatMessage Component
 *
 * Displays a chat message with optional step indicators.
 */
import { type FC } from 'react';
import { StepData } from '../api/client';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  steps?: StepData[];
  isStreaming?: boolean;
}

export const ChatMessage: FC<ChatMessageProps> = ({
  role,
  content,
  steps = [],
  isStreaming = false,
}) => {
  const isUser = role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-2xl rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-900 border border-gray-200'
        }`}
      >
        {!isUser && steps.length > 0 && (
          <div className="mb-2 border-b border-gray-300 pb-2">
            <div className="text-xs font-medium text-gray-500 mb-1">Execution Steps:</div>
            {steps.map((step, index) => (
              <div key={index} className="text-xs text-gray-600 mb-1 last:mb-0">
                <span className="font-medium">{step.type}:</span> {step.content}
              </div>
            ))}
          </div>
        )}

        <div className={`whitespace-pre-wrap ${isStreaming && !isUser ? 'animate-pulse' : ''}`}>
          {content || (isStreaming && !isUser ? 'Thinking...' : '')}
        </div>
      </div>
    </div>
  );
};
