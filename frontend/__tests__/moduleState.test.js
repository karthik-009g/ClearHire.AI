import {
  formatPercent,
  parseCsv,
  getResmatContext,
  setResmatContext,
  clearResmatContext,
  getJdContext,
  setJdContext,
  clearJdContext,
} from '../src/lib/moduleState';

describe('moduleState utility functions', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  describe('formatPercent', () => {
    it('returns -- for invalid or non-numeric inputs', () => {
      expect(formatPercent(undefined)).toBe('--');
      expect(formatPercent(null)).toBe('--');
      expect(formatPercent(NaN)).toBe('--');
      expect(formatPercent('not-a-number')).toBe('--');
    });

    it('formats fractional decimal scores into rounded percentage', () => {
      expect(formatPercent(0.854)).toBe('85%');
      expect(formatPercent(1.0)).toBe('100%');
      expect(formatPercent(0.0)).toBe('0%');
    });

    it('formats 0-100 scale scores directly', () => {
      expect(formatPercent(92.4)).toBe('92%');
      expect(formatPercent(75)).toBe('75%');
    });
  });

  describe('parseCsv', () => {
    it('splits and trims comma separated keywords', () => {
      expect(parseCsv('Python, FastAPI, Docker, ')).toEqual(['Python', 'FastAPI', 'Docker']);
      expect(parseCsv('')).toEqual([]);
      expect(parseCsv(null)).toEqual([]);
    });
  });

  describe('ResMat Context state storage', () => {
    it('saves, reads, and clears resume context from localStorage', () => {
      expect(getResmatContext()).toBeNull();
      const mockContext = { resumeId: 'res-123', originalFilename: 'cv.pdf' };
      setResmatContext(mockContext);
      expect(getResmatContext()).toEqual(mockContext);
      clearResmatContext();
      expect(getResmatContext()).toBeNull();
    });
  });

  describe('JD Context state storage', () => {
    it('saves, reads, and clears JD context from localStorage', () => {
      expect(getJdContext()).toBeNull();
      const mockJd = { title: 'Backend Lead', company: 'Google', jdText: 'PyTorch and Kubernetes' };
      setJdContext(mockJd);
      expect(getJdContext()).toEqual(mockJd);
      clearJdContext();
      expect(getJdContext()).toBeNull();
    });
  });
});
