#!/usr/bin/env python3
"""
Automated API Latency & Throughput Benchmark Suite
File: scripts/benchmark_api.py

Standalone executable benchmark suite profiling critical Clear_Hire.AI API endpoints
under phased concurrent loads (5, 15, 25, 50 concurrent requests).
Measures:
  - Minimum, p50 (median), p95, p99, and maximum latency (ms)
  - QPS / RPS throughput
  - HTTP status distribution & 5xx error rate
  - Server process and client process memory RSS deltas (MB)
  - Formatted ASCII table and structured JSON export
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import statistics
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

# ---------------------------------------------------------------------------
# Memory Measurement Helpers (Win32 K32GetProcessMemoryInfo + psutil fallback)
# ---------------------------------------------------------------------------

def get_current_rss_mb() -> float:
    """Retrieve Resident Set Size (RSS) memory in MB for the current process."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024.0 * 1024.0)
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            get_info = ctypes.windll.kernel32.K32GetProcessMemoryInfo
            get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
            get_info.restype = wintypes.BOOL

            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if get_info(handle, ctypes.byref(pmc), pmc.cb):
                return pmc.WorkingSetSize / (1024.0 * 1024.0)
        except Exception:
            pass

    return 0.0


def find_server_pid(port: int = 8000) -> Optional[int]:
    """Auto-detect the process ID listening on the given port."""
    if sys.platform == "win32":
        try:
            output = subprocess.check_output(
                "netstat -ano -p tcp", shell=True, stderr=subprocess.DEVNULL
            ).decode()
            port_pattern = f":{port} "
            for line in output.splitlines():
                if port_pattern in line and "LISTENING" in line:
                    parts = line.strip().split()
                    return int(parts[-1])
        except Exception:
            pass
    else:
        try:
            output = subprocess.check_output(
                ["lsof", "-t", "-i", f":{port}"], stderr=subprocess.DEVNULL
            ).decode()
            for line in output.splitlines():
                if line.strip():
                    return int(line.strip())
        except Exception:
            pass
    return None


def get_pid_rss_mb(pid: Optional[int]) -> Optional[float]:
    """Retrieve RSS memory in MB for a specific process ID."""
    if not pid:
        return None
    try:
        import psutil
        return psutil.Process(pid).memory_info().rss / (1024.0 * 1024.0)
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid
            )
            if not handle:
                return None
            try:
                class PMC(ctypes.Structure):
                    _fields_ = [
                        ("cb", wintypes.DWORD),
                        ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t),
                    ]

                get_info = ctypes.windll.kernel32.K32GetProcessMemoryInfo
                get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
                get_info.restype = wintypes.BOOL

                pmc = PMC()
                pmc.cb = ctypes.sizeof(PMC)
                if get_info(handle, ctypes.byref(pmc), pmc.cb):
                    return pmc.WorkingSetSize / (1024.0 * 1024.0)
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass

    return None


# ---------------------------------------------------------------------------
# Endpoint Definitions and Realistic Test Payloads
# ---------------------------------------------------------------------------

SAMPLE_RESUME_TEXT = """
Jane Doe
Senior Full-Stack & Systems Engineer
Email: jane.doe.bench@clearhire.ai | Phone: +1-555-0144 | Location: Bengaluru / Remote

SUMMARY
Results-oriented software architect with 7+ years of experience designing high-throughput
distributed systems, asyncio microservices, and AI-assisted recruitment platforms.

EXPERIENCE
Staff Backend Engineer | HyperScale Tech (2022 - Present)
- Architected FastAPI microservices handling 35,000 requests/sec with Neon PostgreSQL connection pooling.
- Completely eliminated synchronous event loop blocking using background threadpools.
- Designed Redis multi-tiered caching reducing p95 latency from 1,200ms to 85ms.

Senior Software Engineer | CloudVenture (2018 - 2022)
- Implemented asynchronous web scrapers ingesting 50,000 daily jobs across 22 direct ATS providers.
- Built LangGraph analysis workflows with sentence-transformers for keyword and vector matching.

SKILLS
Python, FastAPI, SQLAlchemy, PostgreSQL, Redis, LangChain, LangGraph, Docker, Kubernetes, AWS.
"""

SAMPLE_JD_TEXT = """
ClearHire AI is hiring a Senior Backend Engineer to lead latency optimization and high-concurrency
infrastructure. You will optimize database connection pools, eliminate synchronous blocking I/O
on the asyncio event loop, harden caching services, and build pre-compiled LangGraph workflows.
Requirements: Strong proficiency with Python 3.11+, FastAPI, PostgreSQL, Redis, and LangGraph.
"""


def build_endpoint_registry(resume_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Construct the list of critical and auxiliary target endpoints."""
    effective_resume_id = resume_id or "demo-seed-resume-uuid-001"
    return [
        {
            "id": "health",
            "name": "Health Check",
            "method": "GET",
            "path": "/health",
            "payload_type": "none",
            "payload": None,
            "auth": False,
            "is_critical": False,
        },
        {
            "id": "ready",
            "name": "Readiness Probe",
            "method": "GET",
            "path": "/ready",
            "payload_type": "none",
            "payload": None,
            "auth": False,
            "is_critical": False,
        },
        {
            "id": "parse",
            "name": "Resume Parse & Ingest",
            "method": "POST",
            "path": "/api/resumes/upload",
            "payload_type": "multipart",
            "payload": {
                "filename": "jane_doe_bench_resume.txt",
                "content": SAMPLE_RESUME_TEXT.encode("utf-8"),
                "content_type": "text/plain",
            },
            "auth": True,
            "is_critical": True,
        },
        {
            "id": "match",
            "name": "Resume Match Analysis",
            "method": "POST",
            "path": "/api/resumes/match",
            "payload_type": "json",
            "payload": {
                "resume_id": effective_resume_id,
                "jd_text": SAMPLE_JD_TEXT,
                "title": "Senior Backend Engineer",
                "company": "ClearHire AI",
                "source": "bench_harness",
            },
            "auth": True,
            "is_critical": True,
        },
        {
            "id": "search",
            "name": "Job Scrape & Search",
            "method": "POST",
            "path": "/api/jobs/scrape",
            "payload_type": "json",
            "payload": {
                "keywords": ["backend", "python", "fastapi"],
                "locations": ["Remote", "Bengaluru"],
                "sources": ["direct_ats"],
                "direct_portals_only": True,
                "exclude_staffing_agencies": True,
                "posted_within_hours": 72,
            },
            "auth": True,
            "is_critical": True,
        },
        {
            "id": "digest",
            "name": "Matched Jobs Digest",
            "method": "POST",
            "path": "/api/jobs/digest",
            "payload_type": "json",
            "payload": {
                "resume_id": effective_resume_id,
                "target_email": "jane.doe.bench@clearhire.ai",
                "top_n": 10,
            },
            "auth": True,
            "is_critical": True,
        },
        {
            "id": "applications",
            "name": "List Applications CRM",
            "method": "GET",
            "path": "/api/applications/",
            "payload_type": "none",
            "payload": None,
            "auth": True,
            "is_critical": True,
        },
    ]


# ---------------------------------------------------------------------------
# Benchmark Engine
# ---------------------------------------------------------------------------

class ApiBenchmarkHarness:
    """
    High-throughput asynchronous benchmark harness for FastAPI backend.
    """

    def __init__(
        self,
        backend_url: str = "http://127.0.0.1:8000",
        timeout: float = 30.0,
        server_pid: Optional[int] = None,
        dry_run: bool = False,
    ):
        self.backend_url = backend_url.rstrip("/")
        self.timeout = timeout
        self.server_pid = server_pid or find_server_pid(8000)
        self.dry_run = dry_run
        self.token: Optional[str] = None
        self.active_resume_id: Optional[str] = None
        self.test_user = {
            "email": f"bench_{int(time.time())}@clearhire.ai",
            "password": "BenchmarkPassword123!",
            "full_name": "API Benchmark Runner",
        }

    async def authenticate(self, client: httpx.AsyncClient) -> bool:
        """Authenticate or register benchmark user to acquire JWT token."""
        if self.dry_run:
            self.token = "mock-dry-run-jwt-token"
            self.active_resume_id = "mock-dry-run-resume-id"
            return True

        login_url = f"{self.backend_url}/api/auth/login"
        reg_url = f"{self.backend_url}/api/auth/register"
        login_payload = {
            "email": self.test_user["email"],
            "password": self.test_user["password"],
        }

        try:
            # First attempt login
            resp = await client.post(login_url, json=login_payload)
            if resp.status_code == 200:
                self.token = resp.json().get("access_token")
                return True

            # Register if not exists
            reg_resp = await client.post(reg_url, json=self.test_user)
            if reg_resp.status_code in (200, 201):
                login_resp = await client.post(login_url, json=login_payload)
                if login_resp.status_code == 200:
                    self.token = login_resp.json().get("access_token")
                    return True
        except Exception as exc:
            print(f"[WARN] Live auth connection failed: {exc}", file=sys.stderr)
        return False

    async def seed_resume_if_needed(self, client: httpx.AsyncClient) -> None:
        """Upload a seed resume on setup so that /match and /digest endpoints succeed."""
        if self.dry_run or not self.token:
            return

        upload_url = f"{self.backend_url}/api/resumes/upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        files = {
            "file": ("seed_resume.txt", SAMPLE_RESUME_TEXT.encode("utf-8"), "text/plain")
        }
        try:
            resp = await client.post(upload_url, headers=headers, files=files, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                self.active_resume_id = data.get("resume_id")
        except Exception:
            pass

    async def _execute_dry_run_request(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate realistic network and compute latency in dry-run mode."""
        eid = endpoint.get("id", "")
        # Baseline latency profiles based on empirical measurements (in ms)
        profiles = {
            "health": (0.8, 2.5),
            "ready": (2.0, 8.0),
            "parse": (45.0, 95.0),
            "match": (55.0, 140.0),
            "search": (85.0, 220.0),
            "digest": (40.0, 110.0),
            "applications": (12.0, 35.0),
        }
        low, high = profiles.get(eid, (10.0, 50.0))
        simulated_ms = random.uniform(low, high)
        await asyncio.sleep(simulated_ms / 1000.0)
        return {
            "status": 200,
            "latency_ms": simulated_ms,
            "error": None,
        }

    async def execute_single_request(
        self,
        client: httpx.AsyncClient,
        endpoint: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single HTTP request with microsecond timing and error handling."""
        if self.dry_run:
            return await self._execute_dry_run_request(endpoint)

        headers: Dict[str, str] = {}
        if endpoint.get("auth") and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"{self.backend_url}{endpoint['path']}"
        method = endpoint.get("method", "GET").upper()
        payload_type = endpoint.get("payload_type", "none")
        payload = endpoint.get("payload")

        # Dynamically inject active resume_id if available
        if payload_type == "json" and isinstance(payload, dict) and self.active_resume_id:
            if "resume_id" in payload:
                payload = dict(payload)
                payload["resume_id"] = self.active_resume_id

        start = time.perf_counter()
        try:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            elif method == "POST":
                if payload_type == "multipart" and isinstance(payload, dict):
                    files = {
                        "file": (
                            payload["filename"],
                            payload["content"],
                            payload.get("content_type", "application/octet-stream"),
                        )
                    }
                    resp = await client.post(url, headers=headers, files=files)
                elif payload_type == "json":
                    resp = await client.post(url, headers=headers, json=payload)
                else:
                    resp = await client.post(url, headers=headers)
            else:
                resp = await client.request(method, url, headers=headers, json=payload)

            elapsed_ms = (time.perf_counter() - start) * 1000.0
            is_err = resp.status_code >= 500
            return {
                "status": resp.status_code,
                "latency_ms": elapsed_ms,
                "error": None if not is_err else f"HTTP {resp.status_code}: {resp.text[:120]}",
            }
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return {
                "status": 0,
                "latency_ms": elapsed_ms,
                "error": f"Exception: {type(exc).__name__}: {str(exc)}",
            }

    async def benchmark_endpoint(
        self,
        endpoint: Dict[str, Any],
        concurrency: int,
        total_requests: int,
    ) -> Dict[str, Any]:
        """
        Execute concurrent benchmark runs against a single endpoint using asyncio.Semaphore.
        """
        semaphore = asyncio.Semaphore(concurrency)
        results: List[Dict[str, Any]] = []

        limits = httpx.Limits(
            max_keepalive_connections=concurrency * 2,
            max_connections=concurrency * 4,
        )
        async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as client:
            if endpoint.get("auth") and not self.token:
                await self.authenticate(client)
                await self.seed_resume_if_needed(client)

            async def worker():
                async with semaphore:
                    res = await self.execute_single_request(client, endpoint)
                    results.append(res)

            start_time = time.perf_counter()
            tasks = [asyncio.create_task(worker()) for _ in range(total_requests)]
            await asyncio.gather(*tasks)
            duration_sec = time.perf_counter() - start_time

        latencies = [r["latency_ms"] for r in results]
        statuses = [r["status"] for r in results]
        latencies.sort()

        min_ms = min(latencies) if latencies else 0.0
        max_ms = max(latencies) if latencies else 0.0
        p50 = statistics.median(latencies) if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0
        rps = (len(results) / duration_sec) if duration_sec > 0 else 0.0

        errors_5xx = [r for r in results if r["status"] >= 500 or r["status"] == 0]
        status_dist = {str(code): statuses.count(code) for code in sorted(set(statuses))}
        error_rate = (len(errors_5xx) / len(results) * 100.0) if results else 0.0

        return {
            "id": endpoint["id"],
            "name": endpoint["name"],
            "method": endpoint["method"],
            "path": endpoint["path"],
            "is_critical": endpoint.get("is_critical", False),
            "concurrency": concurrency,
            "total_requests": len(results),
            "duration_sec": round(duration_sec, 3),
            "qps": round(rps, 2),
            "min_ms": round(min_ms, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "max_ms": round(max_ms, 2),
            "status_distribution": status_dist,
            "5xx_count": len(errors_5xx),
            "5xx_error_rate_pct": round(error_rate, 2),
        }

    async def run_benchmark(
        self,
        concurrency_tiers: List[int],
        requests_per_endpoint: int,
    ) -> Dict[str, Any]:
        """
        Execute full benchmark across specified concurrency tiers and endpoints.
        """
        init_client_rss = get_current_rss_mb()
        init_server_rss = get_pid_rss_mb(self.server_pid)

        # Setup auth & seed resume if possible
        if not self.dry_run:
            async with httpx.AsyncClient(timeout=10.0) as setup_client:
                await self.authenticate(setup_client)
                await self.seed_resume_if_needed(setup_client)

        endpoints = build_endpoint_registry(self.active_resume_id)
        tier_results: List[Dict[str, Any]] = []

        for tier in concurrency_tiers:
            endpoint_metrics: List[Dict[str, Any]] = []
            for ep in endpoints:
                metric = await self.benchmark_endpoint(
                    endpoint=ep,
                    concurrency=tier,
                    total_requests=requests_per_endpoint,
                )
                endpoint_metrics.append(metric)

            tier_results.append({
                "concurrency": tier,
                "requests_per_endpoint": requests_per_endpoint,
                "endpoints": endpoint_metrics,
            })

        final_client_rss = get_current_rss_mb()
        final_server_rss = get_pid_rss_mb(self.server_pid)

        summary = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "backend_url": self.backend_url,
            "dry_run": self.dry_run,
            "server_pid": self.server_pid,
            "memory_telemetry": {
                "client_initial_rss_mb": round(init_client_rss, 2),
                "client_final_rss_mb": round(final_client_rss, 2),
                "client_delta_rss_mb": round(final_client_rss - init_client_rss, 2),
                "server_initial_rss_mb": round(init_server_rss, 2) if init_server_rss else None,
                "server_final_rss_mb": round(final_server_rss, 2) if final_server_rss else None,
                "server_delta_rss_mb": round(final_server_rss - init_server_rss, 2) if (init_server_rss and final_server_rss) else None,
            },
            "tiers": tier_results,
        }
        return summary


# ---------------------------------------------------------------------------
# Terminal Output Formatting (ASCII Table)
# ---------------------------------------------------------------------------

def print_ascii_summary(report: Dict[str, Any]) -> None:
    """Print clean formatted ASCII summary tables to stdout."""
    print("\n" + "=" * 115)
    print(" CLEAR_HIRE.AI — AUTOMATED API LATENCY & CONCURRENT THROUGHPUT BENCHMARK REPORT")
    print("=" * 115)
    print(f" Timestamp    : {report['timestamp']}")
    print(f" Backend URL  : {report['backend_url']} {'[DRY RUN / SIMULATION]' if report['dry_run'] else '[LIVE TARGET]'}")
    mem = report["memory_telemetry"]
    print(f" Memory RSS   : Client Delta: {mem['client_delta_rss_mb']:+.2f} MB | "
          f"Server Delta: {mem['server_delta_rss_mb'] if mem['server_delta_rss_mb'] is not None else 'N/A'}")
    print("-" * 115)

    headers = [
        "Endpoint", "Method", "Path", "Conc", "Reqs", "QPS",
        "Min (ms)", "p50 (ms)", "p95 (ms)", "p99 (ms)", "Max (ms)", "5xx %"
    ]
    col_widths = [22, 6, 23, 5, 5, 8, 8, 8, 8, 8, 8, 6]

    def fmt_row(vals: List[Any]) -> str:
        parts = [f"{str(v):<{w}}" for v, w in zip(vals, col_widths)]
        return " | ".join(parts)

    divider = "-+-".join("-" * w for w in col_widths)

    for tier in report["tiers"]:
        print(f"\n[PHASE / CONCURRENCY TIER: {tier['concurrency']} concurrent clients]")
        print(fmt_row(headers))
        print(divider)
        for ep in tier["endpoints"]:
            crit_badge = "*" if ep["is_critical"] else " "
            row = [
                f"{crit_badge}{ep['name'][:21]}",
                ep["method"],
                ep["path"][:23],
                ep["concurrency"],
                ep["total_requests"],
                f"{ep['qps']:.1f}",
                f"{ep['min_ms']:.1f}",
                f"{ep['p50_ms']:.1f}",
                f"{ep['p95_ms']:.1f}",
                f"{ep['p99_ms']:.1f}",
                f"{ep['max_ms']:.1f}",
                f"{ep['5xx_error_rate_pct']:.1f}%",
            ]
            print(fmt_row(row))
        print("-" * 115)

    print(" [*] denotes critical endpoints required by R1 specification.")
    print("=" * 115 + "\n")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clear_Hire.AI Automated API Latency & Concurrency Benchmark Suite"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="FastAPI backend base URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=25,
        help="Concurrency level when --phases is not specified (default: 25)",
    )
    parser.add_argument(
        "--requests-per-endpoint",
        type=int,
        default=20,
        help="Number of requests dispatched per endpoint per tier (default: 20)",
    )
    parser.add_argument(
        "--phases",
        action="store_true",
        help="Execute across all 4 standard concurrency tiers (5, 15, 25, 50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate load offline with realistic latency distributions (self-test mode)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional path to output structured JSON benchmark report",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds (default: 30.0)",
    )
    return parser.parse_args()


async def async_main() -> int:
    args = parse_args()

    if args.phases:
        tiers = [5, 15, 25, 50]
    else:
        tiers = [args.concurrency]

    harness = ApiBenchmarkHarness(
        backend_url=args.backend_url,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )

    report = await harness.run_benchmark(
        concurrency_tiers=tiers,
        requests_per_endpoint=args.requests_per_endpoint,
    )

    print_ascii_summary(report)

    if args.output_json:
        os.makedirs(os.path.dirname(os.path.abspath(args.output_json)), exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"[SUCCESS] JSON report saved to: {args.output_json}")

    # Check for hard gate failures (any 5xx errors across critical endpoints)
    has_critical_failure = False
    for tier in report["tiers"]:
        for ep in tier["endpoints"]:
            if ep["is_critical"] and ep["5xx_count"] > 0:
                has_critical_failure = True
                print(f"[FAIL GATE] 5xx errors detected in {ep['name']} ({ep['path']}): {ep['5xx_count']} errors", file=sys.stderr)

    return 1 if has_critical_failure else 0


def main() -> None:
    exit_code = asyncio.run(async_main())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
