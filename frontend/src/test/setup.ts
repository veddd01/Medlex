import '@testing-library/jest-dom';

// Polyfill scrollIntoView for jsdom
window.HTMLElement.prototype.scrollIntoView = function() {};
