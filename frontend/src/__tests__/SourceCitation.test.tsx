import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SourceCitation from '../components/SourceCitation';
import { Source } from '../types/api';

describe('SourceCitation', () => {
  const mockSource: Source = {
    page: 4,
    source: 'sample_medical_book.pdf',
    score: 0.88,
    excerpt: 'Adults require at least 150 minutes of moderate activity per week.',
  };

  it('renders page pill and truncated filename in collapsed state', () => {
    render(<SourceCitation source={mockSource} />);

    expect(screen.getByText(/Page 4/i)).toBeInTheDocument();
    expect(screen.getByText(/sample_medical_book\.pdf/i)).toBeInTheDocument();
    expect(screen.queryByText(new RegExp(mockSource.excerpt, 'i'))).not.toBeInTheDocument();
  });

  it('toggles expansion to show excerpt on click', () => {
    render(<SourceCitation source={mockSource} />);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(screen.getByText(new RegExp(mockSource.excerpt, 'i'))).toBeInTheDocument();

    // Click again to collapse
    fireEvent.click(button);
    expect(screen.queryByText(new RegExp(mockSource.excerpt, 'i'))).not.toBeInTheDocument();
  });
});
