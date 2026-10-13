import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ChatWindow from '../components/ChatWindow';
import { Message } from '../types/api';

describe('ChatWindow', () => {
  it('renders welcome screen and suggestion chips when messages array is empty', () => {
    render(
      <ChatWindow
        messages={[]}
        isLoading={false}
        onSendMessage={vi.fn()}
        onClear={vi.fn()}
        onFeedback={vi.fn()}
      />
    );

    expect(screen.getByText(/Welcome to MedLex/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Type your medical question here/i)).toBeInTheDocument();
  });

  it('allows user to type a question and submit it', () => {
    const handleSend = vi.fn();
    render(
      <ChatWindow
        messages={[]}
        isLoading={false}
        onSendMessage={handleSend}
        onClear={vi.fn()}
        onFeedback={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText(/Type your medical question here/i);
    fireEvent.change(input, { target: { value: 'What causes headaches?' } });

    const submitBtn = screen.getByRole('button', { name: '' }); // Send button with svg icon
    fireEvent.click(submitBtn);

    expect(handleSend).toHaveBeenCalledTimes(1);
    expect(handleSend).toHaveBeenCalledWith('What causes headaches?');
    expect(input).toHaveValue('');
  });

  it('renders typing indicator and disables submit button when isLoading is true', () => {
    const handleSend = vi.fn();
    const mockMessages: Message[] = [
      { id: '1', role: 'user', content: 'Hello', timestamp: Date.now() },
    ];

    render(
      <ChatWindow
        messages={mockMessages}
        isLoading={true}
        onSendMessage={handleSend}
        onClear={vi.fn()}
        onFeedback={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText(/Type your medical question here/i);
    fireEvent.change(input, { target: { value: 'Followup' } });

    // Submit button should be disabled when loading
    const buttons = screen.getAllByRole('button');
    const sendBtn = buttons[buttons.length - 1];
    expect(sendBtn).toBeDisabled();
  });

  it('renders clear chat button and triggers onClear callback', () => {
    const handleClear = vi.fn();
    const mockMessages: Message[] = [
      { id: '1', role: 'user', content: 'What is a fever?', timestamp: Date.now() },
      { id: '2', role: 'assistant', content: 'A body temp above 100.4 F.', timestamp: Date.now() },
    ];

    render(
      <ChatWindow
        messages={mockMessages}
        isLoading={false}
        onSendMessage={vi.fn()}
        onClear={handleClear}
        onFeedback={vi.fn()}
      />
    );

    const clearBtn = screen.getByText(/Clear Chat/i);
    expect(clearBtn).toBeInTheDocument();
    fireEvent.click(clearBtn);
    expect(handleClear).toHaveBeenCalledTimes(1);
  });
});
