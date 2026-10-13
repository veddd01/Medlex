import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import EmergencyBanner from '../components/EmergencyBanner';

describe('EmergencyBanner', () => {
  it('renders emergency alert heading and critical hotline numbers', () => {
    render(<EmergencyBanner />);
    expect(screen.getByText(/Medical Emergency Alert/i)).toBeInTheDocument();
    expect(screen.getByText(/Please immediately call 911/i)).toBeInTheDocument();
    expect(screen.getByText(/MedLex cannot provide emergency assistance/i)).toBeInTheDocument();
  });
});
