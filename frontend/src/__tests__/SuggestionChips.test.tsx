import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SuggestionChips from '../components/SuggestionChips';

describe('SuggestionChips', () => {
  it('renders default medical suggestion questions', () => {
    const handleSelect = vi.fn();
    render(<SuggestionChips onSelect={handleSelect} />);

    expect(screen.getByText(/What are the symptoms of type 2 diabetes\?/i)).toBeInTheDocument();
    expect(screen.getByText(/How is hypertension usually treated\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Explain the side effects of ibuprofen/i)).toBeInTheDocument();
  });

  it('calls onSelect callback when a chip is clicked', () => {
    const handleSelect = vi.fn();
    render(<SuggestionChips onSelect={handleSelect} />);

    const chip = screen.getByText(/What are early signs of a heart attack\?/i);
    fireEvent.click(chip);

    expect(handleSelect).toHaveBeenCalledTimes(1);
    expect(handleSelect).toHaveBeenCalledWith('What are early signs of a heart attack?');
  });
});
