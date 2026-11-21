import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ModuleLayout from "../src/components/ModuleLayout";
import * as authApi from "../src/api/auth";
import * as clientApi from "../src/api/client";
import { useRouter } from "next/router";

jest.mock("next/router", () => ({
  useRouter: jest.fn(),
}));

jest.mock("../src/api/auth", () => ({
  getMe: jest.fn(),
}));

jest.mock("../src/api/client", () => ({
  getStoredAuthToken: jest.fn(),
  setAuthToken: jest.fn(),
  clearAuthToken: jest.fn(),
}));

describe("ModuleLayout Component Suite", () => {
  let mockPush;
  let mockReplace;

  beforeEach(() => {
    jest.clearAllMocks();
    mockPush = jest.fn();
    mockReplace = jest.fn();

    useRouter.mockReturnValue({
      pathname: "/",
      push: mockPush,
      replace: mockReplace,
    });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ready" }),
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("redirects unauthenticated users to /login when token is missing", async () => {
    clientApi.getStoredAuthToken.mockReturnValue(null);

    render(
      <ModuleLayout title="Pipeline CRM">
        <div>Pipeline Children</div>
      </ModuleLayout>
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/login");
    });
  });

  it("redirects unauthenticated users to /login when getMe rejects", async () => {
    clientApi.getStoredAuthToken.mockReturnValue("expired-token");
    authApi.getMe.mockRejectedValue(new Error("Invalid token"));

    render(
      <ModuleLayout title="Pipeline CRM">
        <div>Pipeline Children</div>
      </ModuleLayout>
    );

    await waitFor(() => {
      expect(clientApi.clearAuthToken).toHaveBeenCalled();
      expect(mockReplace).toHaveBeenCalledWith("/login");
    });
  });

  it("renders authenticated user layout with header, navigation, and children", async () => {
    clientApi.getStoredAuthToken.mockReturnValue("valid-token");
    authApi.getMe.mockResolvedValue({
      email: "sarah.chen@alum.mit.edu",
      role: "candidate",
    });

    render(
      <ModuleLayout title="Pipeline CRM" subtitle="Candidate interview tracking dashboard">
        <div data-testid="test-child">Active Pipeline Contents</div>
      </ModuleLayout>
    );

    // Verify brand
    await waitFor(() => {
      expect(screen.getByText("clearhire")).toBeInTheDocument();
      expect(screen.getByText(".ai")).toBeInTheDocument();
    });

    // Verify user email in status pill
    expect(screen.getByText("sarah.chen@alum.mit.edu")).toBeInTheDocument();

    // Verify title and subtitle in HUD banner
    expect(screen.getByRole("heading", { name: "Pipeline CRM", level: 1 })).toBeInTheDocument();
    expect(screen.getByText("Candidate interview tracking dashboard")).toBeInTheDocument();

    // Verify children rendered
    expect(screen.getByTestId("test-child")).toBeInTheDocument();

    // Verify navigation links
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Direct Requisitions")).toBeInTheDocument();
    expect(screen.getAllByText("Pipeline CRM")).toHaveLength(2);
    expect(screen.getByText("1-Page Resume")).toBeInTheDocument();
    expect(screen.getByText("JD Matcher")).toBeInTheDocument();
    expect(screen.getByText("Daily Briefing")).toBeInTheDocument();
    expect(screen.getByText("Screener Copilot")).toBeInTheDocument();
  });

  it("handles sign out by clearing auth token and redirecting to /login", async () => {
    clientApi.getStoredAuthToken.mockReturnValue("valid-token");
    authApi.getMe.mockResolvedValue({
      email: "candidate@clearhire.ai",
    });

    render(
      <ModuleLayout title="Overview">
        <div>Overview page</div>
      </ModuleLayout>
    );

    await waitFor(() => {
      expect(screen.getByText("Sign out ↗")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Sign out ↗"));

    expect(clientApi.clearAuthToken).toHaveBeenCalled();
    expect(mockReplace).toHaveBeenCalledWith("/login");
  });

  it("reflects backend health status indicator", async () => {
    clientApi.getStoredAuthToken.mockReturnValue("valid-token");
    authApi.getMe.mockResolvedValue({
      email: "candidate@clearhire.ai",
    });

    // Mock ready check returning ok
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
    });

    const { container } = render(
      <ModuleLayout title="Overview">
        <div>Content</div>
      </ModuleLayout>
    );

    await waitFor(() => {
      // bg-emerald-500 is rendered when dbStatus === 'connected'
      const statusPill = container.querySelector(".bg-emerald-500");
      expect(statusPill).toBeInTheDocument();
    });
  });
});
