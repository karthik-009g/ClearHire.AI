import React from "react";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import LoginPage from "../src/pages/login";
import * as authApi from "../src/api/auth";
import * as clientApi from "../src/api/client";
import { useRouter } from "next/router";

jest.mock("next/router", () => ({
  useRouter: jest.fn(),
}));

jest.mock("../src/api/auth", () => ({
  loginUser: jest.fn(),
  registerUser: jest.fn(),
  getMe: jest.fn(),
}));

jest.mock("../src/api/client", () => ({
  getStoredAuthToken: jest.fn(),
  setAuthToken: jest.fn(),
  clearAuthToken: jest.fn(),
}));

jest.mock("../src/components/ClearHireStoryEngine", () => {
  const stages = [
    { index: 0, num: "01", shortLabel: "INTAKE", title: "Candidate Dossier Dispatched", scannerStatus: "READY", coordinates: "X:0 Y:0 Z:0" },
    { index: 1, num: "02", shortLabel: "LIFT", title: "Aerodynamic Flutter Lift", scannerStatus: "LIFT", coordinates: "X:0 Y:0 Z:0" },
    { index: 2, num: "03", shortLabel: "OCR SCAN", title: "Precision Optical ATS Ingest", scannerStatus: "SCAN", coordinates: "X:0 Y:0 Z:0" },
    { index: 3, num: "04", shortLabel: "AST PARSE", title: "The Heuristic Divergence", scannerStatus: "PARSE", coordinates: "X:0 Y:0 Z:0" },
    { index: 4, num: "05", shortLabel: "FORK", title: "The Discarded Incinerator", scannerStatus: "FORK", coordinates: "X:0 Y:0 Z:0" },
    { index: 5, num: "06", shortLabel: "PNEUMATIC", title: "Pressurized Pipeline Velocity", scannerStatus: "SPEED", coordinates: "X:0 Y:0 Z:0" },
    { index: 6, num: "07", shortLabel: "DIRECT ATS", title: "Enterprise Direct Pipeline Entry", scannerStatus: "DIRECT", coordinates: "X:0 Y:0 Z:0" },
    { index: 7, num: "08", shortLabel: "ANTI-GHOST", title: "The 48-Hour SLA Covenant", scannerStatus: "SLA", coordinates: "X:0 Y:0 Z:0" },
    { index: 8, num: "09", shortLabel: "PORTAL", title: "ClearHire Candidate Workspace Entry", scannerStatus: "PORTAL", coordinates: "X:0 Y:0 Z:0" },
  ];
  return {
    __esModule: true,
    default: function MockStoryEngine() {
      return <div data-testid="mock-story-engine" />;
    },
    STORY_STAGES: stages,
  };
});

let sectorListener = null;

jest.mock("../src/lib/VirtualScroll", () => ({
  VirtualScroll: jest.fn().mockImplementation(() => ({
    bindEvents: jest.fn(),
    unbindEvents: jest.fn(),
    onUpdate: jest.fn(),
    update: jest.fn(),
    onSectorChange: jest.fn((cb) => {
      sectorListener = cb;
    }),
    scrollToSector: jest.fn((idx) => {
      if (sectorListener) {
        sectorListener(idx);
      }
    }),
    nextSector: jest.fn(),
    prevSector: jest.fn(),
    destroy: jest.fn(),
  })),
}));

describe("Login and Authentication Route Suite", () => {
  let mockPush;
  let mockReplace;

  beforeEach(() => {
    jest.clearAllMocks();
    mockPush = jest.fn();
    mockReplace = jest.fn();
    sectorListener = null;

    useRouter.mockReturnValue({
      pathname: "/login",
      push: mockPush,
      replace: mockReplace,
    });

    clientApi.getStoredAuthToken.mockReturnValue(null);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const goToLoginPortal = () => {
    const skipBtn = screen.getByRole("button", { name: /SKIP TO LOGIN/i });
    act(() => {
      fireEvent.click(skipBtn);
    });
  };

  it("renders story world header and skip to login portal button", () => {
    render(<LoginPage />);

    expect(screen.getByText("clearhire")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /SKIP TO LOGIN/i })).toBeInTheDocument();
  });

  it("opens candidate portal and renders credentials form fields", () => {
    render(<LoginPage />);
    goToLoginPortal();

    expect(screen.getByText("Enter the Candidate Workspace")).toBeInTheDocument();
    expect(screen.getByText("Sign In")).toBeInTheDocument();
    expect(screen.getByText("Provision Account")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("sarah.chen@alum.mit.edu")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Enter Workspace/i })).toBeInTheDocument();
  });

  it("switches modes between Sign In and Provision Account (Create Access Key)", () => {
    render(<LoginPage />);
    goToLoginPortal();

    // Initially in Sign In mode - confirm password field not present
    expect(screen.queryByText("Confirm Password")).not.toBeInTheDocument();

    // Switch to Provision Account mode
    const provisionBtn = screen.getByText("Provision Account");
    fireEvent.click(provisionBtn);

    // Confirm Password field and new submit button label appear
    expect(screen.getByText("Confirm Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Provision Candidate Account/i })).toBeInTheDocument();

    // Switch back to Sign In
    const signInBtn = screen.getByText("Sign In");
    fireEvent.click(signInBtn);
    expect(screen.queryByText("Confirm Password")).not.toBeInTheDocument();
  });

  it("validates password matching on registration mode", async () => {
    render(<LoginPage />);
    goToLoginPortal();

    // Switch to Provision Account mode
    fireEvent.click(screen.getByText("Provision Account"));

    // Fill mismatched passwords
    const emailInput = screen.getByPlaceholderText("sarah.chen@alum.mit.edu");
    const passwordInputs = screen.getAllByPlaceholderText("••••••••••••");
    const passwordInput = passwordInputs[0];
    const confirmInput = passwordInputs[1];

    fireEvent.change(emailInput, { target: { value: "new.candidate@clearhire.ai" } });
    fireEvent.change(passwordInput, { target: { value: "SecretPass123!" } });
    fireEvent.change(confirmInput, { target: { value: "DifferentPass456!" } });

    const submitBtn = screen.getByRole("button", { name: /Provision Candidate Account/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    });
    expect(authApi.registerUser).not.toHaveBeenCalled();
  });

  it("submits valid sign in credentials and navigates to workspace dashboard", async () => {
    authApi.loginUser.mockResolvedValue({ access_token: "test-valid-jwt" });
    authApi.getMe.mockResolvedValue({ email: "sarah.chen@alum.mit.edu", role: "candidate" });

    render(<LoginPage />);
    goToLoginPortal();

    const emailInput = screen.getByPlaceholderText("sarah.chen@alum.mit.edu");
    const passwordInput = screen.getByPlaceholderText("••••••••••••");

    fireEvent.change(emailInput, { target: { value: "sarah.chen@alum.mit.edu" } });
    fireEvent.change(passwordInput, { target: { value: "Password123!" } });

    const submitBtn = screen.getByRole("button", { name: /Enter Workspace/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(authApi.loginUser).toHaveBeenCalledWith("sarah.chen@alum.mit.edu", "Password123!");
      expect(clientApi.setAuthToken).toHaveBeenCalledWith("test-valid-jwt");
      expect(mockPush).toHaveBeenCalledWith("/");
    });
  });

  it("displays error message on authentication failure", async () => {
    authApi.loginUser.mockRejectedValue(new Error("Invalid credentials or unregistered candidate"));

    render(<LoginPage />);
    goToLoginPortal();

    const emailInput = screen.getByPlaceholderText("sarah.chen@alum.mit.edu");
    const passwordInput = screen.getByPlaceholderText("••••••••••••");

    fireEvent.change(emailInput, { target: { value: "wrong@clearhire.ai" } });
    fireEvent.change(passwordInput, { target: { value: "WrongPass" } });

    fireEvent.click(screen.getByRole("button", { name: /Enter Workspace/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid credentials or unregistered candidate/i)).toBeInTheDocument();
    });
  });
});
