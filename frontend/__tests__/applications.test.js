jest.mock('../src/api/client', () => ({
  request: jest.fn(),
}));

import { request } from '../src/api/client';
import {
  answerScreenerQuestion,
  prepareApplicationAutofill,
  updateApplicationAutofill,
} from '../src/api/applications';

describe('application preparation API helpers', () => {
  beforeEach(() => jest.clearAllMocks());

  it('submits a screener answer to the expected endpoint', async () => {
    const payload = { application_id: 7, question: 'Work authorization?', answer: 'Yes' };
    await answerScreenerQuestion(payload);
    expect(request).toHaveBeenCalledWith('/api/applications/answer-screener', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  });

  it('requests autofill preparation with the supplied application data', async () => {
    const payload = { job_id: 11, resume_id: 3 };
    await prepareApplicationAutofill(payload);
    expect(request).toHaveBeenCalledWith('/api/applications/autofill', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  });

  it('updates autofill data and includes notes only when provided', async () => {
    await updateApplicationAutofill(9, { fields: [] }, 'Reviewed');
    expect(request).toHaveBeenLastCalledWith('/api/applications/9/autofill', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ autofill_payload: { fields: [] }, notes: 'Reviewed' }),
    });

    await updateApplicationAutofill(9, { fields: [] });
    expect(request).toHaveBeenLastCalledWith('/api/applications/9/autofill', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ autofill_payload: { fields: [] } }),
    });
  });
});
