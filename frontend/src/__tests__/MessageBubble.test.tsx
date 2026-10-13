import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import MessageBubble from '../components/MessageBubble';
import { Message } from '../types/api';

describe('MessageBubble', () => {
  it('renders user message content correctly', () => {
    const msg: Message = {
      id: '1',
      role: 'user',
      content: 'How much water should I drink?',
      timestamp: Date.now(),
    };

    render(<MessageBubble message={msg} />);
    expect(screen.getByText('How much water should I drink?')).toBeInTheDocument();
  });

  it('renders assistant message with sources and feedback buttons', () => {
    const handleFeedback = vi.fn();
    const msg: Message = {
      id: '2',
      role: 'assistant',
      content: 'You should drink enough water that your urine is pale yellow.',
      sources: [
        { page: 2, source: 'sample.pdf', score: 0.95, excerpt: 'pale yellow urine' }
      ],
      timestamp: Date.now(),
    };

    render(<MessageBubble message={msg} onFeedback={handleFeedback} />);
    expect(screen.getByText(/You should drink enough water/i)).toBeInTheDocument();
    expect(screen.getByText(/Sources/i)).toBeInTheDocument();
    expect(screen.getByText(/Page 2/i)).toBeInTheDocument();

    const thumbsUp = screen.getByTitle('Helpful');
    fireEvent.click(thumbsUp);
    expect(handleFeedback).toHaveBeenCalledWith('2', 'up');

    const thumbsDown = screen.getByTitle('Not helpful');
    fireEvent.click(thumbsDown);
    expect(handleFeedback).toHaveBeenCalledWith('2', 'down');
  });

  it('displays EmergencyBanner when message.emergency is true on assistant response', () => {
    const msg: Message = {
      id: '3',
      role: 'assistant',
      content: 'Emergency guidance provided.',
      emergency: true,
      timestamp: Date.now(),
    };

    render(<MessageBubble message={msg} />);
    expect(screen.getByText(/Medical Emergency Alert/i)).toBeInTheDocument();
  });
});
