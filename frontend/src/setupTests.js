// Loaded by CRA before every test file: adds the jest-dom matchers (toHaveAttribute, toBeInTheDocument, ...).
import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';

// findBy*/waitFor default to 1000 ms. Role queries over the chat/admin trees take hundreds of ms
// when the CI box is busy, so a correct test could time out. The limit only bounds failures:
// passing tests are not slowed down.
configure({ asyncUtilTimeout: 5000 });
