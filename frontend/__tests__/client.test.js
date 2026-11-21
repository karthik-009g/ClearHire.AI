import {
  request,
  setAuthToken,
  getStoredAuthToken,
  clearAuthToken,
} from '../src/api/client';

describe('client API utility', () => {
  beforeEach(() => {
    window.localStorage.clear();
    clearAuthToken();
    jest.restoreAllMocks();
  });

  describe('auth token management', () => {
    it('stores, retrieves, and clears token in cache and localStorage', () => {
      expect(getStoredAuthToken()).toBeNull();
      setAuthToken('test-bearer-token');
      expect(getStoredAuthToken()).toBe('test-bearer-token');
      clearAuthToken();
      expect(getStoredAuthToken()).toBeNull();
    });
  });

  describe('request handler', () => {
    it('attaches Authorization header if token is present', async () => {
      setAuthToken('my-jwt-token');
      const mockFetch = jest.fn().mockResolvedValue({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ status: 'healthy' }),
      });
      global.fetch = mockFetch;

      const res = await request('/health');
      expect(res).toEqual({ status: 'healthy' });
      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch.mock.calls[0][0]).toMatch(/\/health$/);

      const callArgs = mockFetch.mock.calls[0];
      expect(callArgs[1].headers.Authorization).toBe('Bearer my-jwt-token');
    });

    it('throws formatted error on API failure', async () => {
      const mockFetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 400,
        headers: { get: () => 'application/json' },
        json: async () => ({ detail: 'Custom validation error' }),
      });
      global.fetch = mockFetch;

      await expect(request('/api/bad-endpoint')).rejects.toThrow('Custom validation error');
    });
  });
});
