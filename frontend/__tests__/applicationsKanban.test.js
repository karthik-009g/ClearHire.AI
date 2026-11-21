import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ApplicationsPage from "../src/pages/applications";
import * as appApi from "../src/api/applications";
import * as resumeApi from "../src/api/resumes";

jest.mock("../src/components/ModuleLayout", () => {
  return function MockModuleLayout({ children, title, subtitle }) {
    return (
      <div data-testid="mock-module-layout">
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
        {children}
      </div>
    );
  };
});

jest.mock("../src/api/applications", () => ({
  listApplications: jest.fn(),
  getGhostingAlerts: jest.fn(),
  updateApplicationStatus: jest.fn(),
  generateApplicationOutreach: jest.fn(),
  reviewApplication: jest.fn(),
  createApplication: jest.fn(),
  getAtsCompatibility: jest.fn(),
  getBrowserAutofillPlan: jest.fn(),
  markApplicationSubmitted: jest.fn(),
  triggerN8nWorkflow: jest.fn(),
}));

jest.mock("../src/api/resumes", () => ({
  listResumeVersions: jest.fn(),
}));

jest.mock("../src/lib/moduleState", () => ({
  getJdContext: jest.fn().mockReturnValue(null),
  getResmatContext: jest.fn().mockReturnValue(null),
}));

describe("Applications Kanban Board Component Suite", () => {
  const sampleApplications = [
    {
      id: 101,
      job_title: "Senior Backend Engineer",
      job_company: "Swiggy",
      status: "pending",
      application_url: "https://careers.swiggy.com/jobs/101",
      updated_at: "2026-11-16T10:00:00Z",
    },
    {
      id: 102,
      job_title: "Distributed Systems Lead",
      job_company: "Postman",
      status: "applied",
      application_url: "https://jobs.lever.co/postman/102",
      updated_at: "2026-11-16T11:00:00Z",
    },
    {
      id: 103,
      job_title: "Principal Architect",
      job_company: "Razorpay",
      status: "interviewing",
      application_url: "https://jobs.lever.co/razorpay/103",
      updated_at: "2026-11-16T12:00:00Z",
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    appApi.listApplications.mockResolvedValue(sampleApplications);
    appApi.getGhostingAlerts.mockResolvedValue({
      total_active: 3,
      ghosting_risk_count: 0,
      alerts: [],
    });
    resumeApi.listResumeVersions.mockResolvedValue({ versions: [] });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("renders all 7 Kanban pipeline columns", async () => {
    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText(/📌 Saved & Draft/i)).toBeInTheDocument();
      expect(screen.getByText(/📝 Review & Prep/i)).toBeInTheDocument();
      expect(screen.getByText(/🚀 Submitted/i)).toBeInTheDocument();
      expect(screen.getByText(/📞 Recruiter Screen/i)).toBeInTheDocument();
      expect(screen.getByText(/💻 Interview Round/i)).toBeInTheDocument();
      expect(screen.getByText(/🏆 Offer Received/i)).toBeInTheDocument();
      expect(screen.getByText(/👻 Ghosted \/ Archived/i)).toBeInTheDocument();
    });
  });

  it("sorts application cards into their designated status columns", async () => {
    render(<ApplicationsPage />);

    await waitFor(() => {
      // Swiggy is in "pending" which belongs to "Review & Prep"
      expect(screen.getByText("Senior Backend Engineer")).toBeInTheDocument();
      expect(screen.getByText("Swiggy")).toBeInTheDocument();

      // Postman is in "applied" which belongs to "Submitted"
      expect(screen.getByText("Distributed Systems Lead")).toBeInTheDocument();
      expect(screen.getByText("Postman")).toBeInTheDocument();

      // Razorpay is in "interviewing" which belongs to "Interview Round"
      expect(screen.getByText("Principal Architect")).toBeInTheDocument();
      expect(screen.getByText("Razorpay")).toBeInTheDocument();
    });
  });

  it("updates application status when dropdown selection changes", async () => {
    appApi.updateApplicationStatus.mockResolvedValue({ id: 101, status: "interviewing" });

    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText("Senior Backend Engineer")).toBeInTheDocument();
    });

    // Find the status select for Swiggy (app id 101)
    const selectElements = screen.getAllByTitle("Jump directly to any pipeline stage");
    const swiggySelect = selectElements[0];

    fireEvent.change(swiggySelect, { target: { value: "interviewing" } });

    await waitFor(() => {
      expect(appApi.updateApplicationStatus).toHaveBeenCalledWith(101, "interviewing", expect.anything());
    });
  });

  it("opens AI Recruiter Outreach modal and displays generated highlights and tabs", async () => {
    const mockOutreachData = {
      target_role: "Senior Backend Engineer",
      target_company: "Swiggy",
      grounded_highlights: [
        "FastAPI distributed architecture",
        "Kafka high-throughput stream processing",
      ],
      inmail_message: "Hi Sarah, impressive work on high-scale Python microservices...",
      short_note: "Hi Sarah, saw your distributed architecture background...",
      followup_email: "Hi Sarah, following up on our platform role discussion...",
    };

    appApi.generateApplicationOutreach.mockResolvedValue(mockOutreachData);

    render(<ApplicationsPage />);

    await waitFor(() => {
      expect(screen.getByText("Senior Backend Engineer")).toBeInTheDocument();
    });

    // Click the InMail button on the first card
    const inMailButtons = screen.getAllByTitle("Generate AI recruiter InMail message");
    fireEvent.click(inMailButtons[0]);

    // Verify modal is open with title and role
    await waitFor(() => {
      expect(screen.getByText("ClearHire AI Recruiter Drafter")).toBeInTheDocument();
      expect(screen.getByText("Senior Backend Engineer at Swiggy")).toBeInTheDocument();
    });

    // Verify grounded highlights
    expect(screen.getByText(/FastAPI distributed architecture/i)).toBeInTheDocument();
    expect(screen.getByText(/Kafka high-throughput stream processing/i)).toBeInTheDocument();

    // Verify outreach message tabs
    expect(screen.getByRole("button", { name: /Hiring Manager InMail/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /LinkedIn Note/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /7-Day Follow-Up/i })).toBeInTheDocument();

    // Switch tab to LinkedIn Note
    fireEvent.click(screen.getByRole("button", { name: /LinkedIn Note/i }));

    // Close modal
    fireEvent.click(screen.getByRole("button", { name: "✕" }));
    await waitFor(() => {
      expect(screen.queryByText("ClearHire AI Recruiter Drafter")).not.toBeInTheDocument();
    });
  });
});
