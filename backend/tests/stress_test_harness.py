"""
ClearHire Automated Concurrent Stress Testing & Stability Verification Harness
File: backend/tests/stress_test_harness.py

Executes concurrent load testing across 4 phases (5, 15, 25, 50 concurrency)
against FastAPI backend endpoints and Next.js frontend routes.
Measures RPS, p50, p95, p99 latency, status distribution, verifies zero 5xx errors,
detects process crashes, and tracks RSS memory before and after load execution.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

import httpx

TARGET_BACKEND_ENDPOINTS = [
    {
        "name": "Health Check",
        "method": "GET",
        "path": "/health",
        "payload": None,
        "auth": False,
    },
    {
        "name": "Readiness Check",
        "method": "GET",
        "path": "/ready",
        "payload": None,
        "auth": False,
    },
    {
        "name": "API Root",
        "method": "GET",
        "path": "/",
        "payload": None,
        "auth": False,
    },
    {
        "name": "Auth Login",
        "method": "POST",
        "path": "/api/auth/login",
        "payload": {
            "email": "stress_test_worker@clearhire.ai",
            "password": "SecurePassword123!",
        },
        "auth": False,
    },
    {
        "name": "List Applications",
        "method": "GET",
        "path": "/api/applications/",
        "payload": None,
        "auth": True,
    },
    {
        "name": "Funnel Analytics",
        "method": "GET",
        "path": "/api/analytics/funnel",
        "payload": None,
        "auth": True,
    },
    {
        "name": "Job Preferences",
        "method": "GET",
        "path": "/api/jobs/preferences",
        "payload": None,
        "auth": True,
    },
    {
        "name": "Answer Screener",
        "method": "POST",
        "path": "/api/applications/answer-screener",
        "payload": {
            "question": "Describe your experience with FastAPI and PostgreSQL",
            "company": "ClearHire",
            "role": "Senior Backend Engineer",
            "max_words": 100,
        },
        "auth": True,
    },
]

TARGET_FRONTEND_ROUTES = [
    {
        "name": "Frontend Root",
        "method": "GET",
        "path": "/",
        "payload": None,
        "auth": False,
    },
    {
        "name": "Frontend Applications",
        "method": "GET",
        "path": "/applications",
        "payload": None,
        "auth": False,
    },
    {
        "name": "Frontend Job Hunter",
        "method": "GET",
        "path": "/job-hunter",
        "payload": None,
        "auth": False,
    },
    {
        "name": "Frontend Login",
        "method": "GET",
        "path": "/login",
        "payload": None,
        "auth": False,
    },
]

DEFAULT_PHASES = [
    {"phase": 1, "name": "Baseline Warmup", "concurrency": 5, "requests_per_endpoint": 10},
    {"phase": 2, "name": "Normal Load", "concurrency": 15, "requests_per_endpoint": 20},
    {"phase": 3, "name": "High Concurrency", "concurrency": 25, "requests_per_endpoint": 30},
    {"phase": 4, "name": "Peak Saturation", "concurrency": 50, "requests_per_endpoint": 50},
]


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

    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
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


class StressHarness:
    """
    Automated Concurrent Stress Testing Harness for FastAPI Backend & Next.js Frontend.
    """

    def __init__(
        self,
        backend_url: str = "http://127.0.0.1:8000",
        frontend_url: str = "http://127.0.0.1:3000",
        server_pid: Optional[int] = None,
        timeout: float = 30.0,
    ):
        self.backend_url = backend_url.rstrip("/")
        self.frontend_url = frontend_url.rstrip("/")
        self.timeout = timeout
        self.token: Optional[str] = None
        self.server_pid = server_pid or find_server_pid(8000)
        self.user_credentials = {
            "email": "stress_test_worker@clearhire.ai",
            "password": "SecurePassword123!",
            "full_name": "Stress Tester Worker",
        }

    async def authenticate(self, client: httpx.AsyncClient) -> bool:
        """Authenticate or register test user and extract JWT access token."""
        login_url = f"{self.backend_url}/api/auth/login"
        login_payload = {
            "email": self.user_credentials["email"],
            "password": self.user_credentials["password"],
        }
        try:
            res = await client.post(login_url, json=login_payload)
            if res.status_code == 200:
                self.token = res.json().get("access_token")
                return True

            # If user does not exist, register and login
            reg_url = f"{self.backend_url}/api/auth/register"
            reg_res = await client.post(reg_url, json=self.user_credentials)
            if reg_res.status_code in (200, 201):
                login_res = await client.post(login_url, json=login_payload)
                if login_res.status_code == 200:
                    self.token = login_res.json().get("access_token")
                    return True
        except Exception as exc:
            print(f"[StressHarness] Authentication error: {exc}", file=sys.stderr)
        return False

    async def check_backend_health(self, client: Optional[httpx.AsyncClient] = None) -> bool:
        """Verify FastAPI backend is healthy and responding with 200."""
        url = f"{self.backend_url}/health"
        try:
            if client:
                res = await client.get(url, timeout=5.0)
            else:
                async with httpx.AsyncClient(timeout=5.0) as temp_client:
                    res = await temp_client.get(url)
            return res.status_code == 200
        except Exception:
            return False

    async def check_frontend_availability(self, client: Optional[httpx.AsyncClient] = None) -> bool:
        """Verify Next.js frontend dev server is running and reachable."""
        url = f"{self.frontend_url}/login"
        try:
            if client:
                res = await client.get(url, timeout=5.0)
            else:
                async with httpx.AsyncClient(timeout=5.0) as temp_client:
                    res = await temp_client.get(url)
            return res.status_code == 200
        except Exception:
            return False

    async def execute_single_request(
        self,
        client: httpx.AsyncClient,
        endpoint: Dict[str, Any],
        base_url: str,
    ) -> Dict[str, Any]:
        """Execute a single HTTP request with latency timing and error handling."""
        headers = {}
        if endpoint.get("auth") and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"{base_url}{endpoint['path']}"
        method = endpoint.get("method", "GET").upper()
        payload = endpoint.get("payload")

        start = time.perf_counter()
        try:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            elif method == "POST":
                resp = await client.post(url, json=payload, headers=headers)
            elif method == "PUT":
                resp = await client.put(url, json=payload, headers=headers)
            elif method == "PATCH":
                resp = await client.patch(url, json=payload, headers=headers)
            elif method == "DELETE":
                resp = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return {
                "status": resp.status_code,
                "latency_ms": elapsed_ms,
                "error": None if resp.status_code < 500 else f"HTTP {resp.status_code}: {resp.text[:100]}",
            }
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return {
                "status": 0,
                "latency_ms": elapsed_ms,
                "error": f"Exception: {str(exc)}",
            }

    async def run_scenario(
        self,
        endpoint: Dict[str, Any],
        concurrency: int,
        total_requests: int,
        base_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """
        Execute a concurrent load scenario against a single endpoint.
        Uses asyncio.Semaphore to enforce concurrency level.
        """
        target_base_url = base_url or self.backend_url
        semaphore = asyncio.Semaphore(concurrency)
        results: List[Dict[str, Any]] = []

        should_close_client = False
        if client is None:
            limits = httpx.Limits(max_keepalive_connections=concurrency * 2, max_connections=concurrency * 4)
            client = httpx.AsyncClient(timeout=self.timeout, limits=limits)
            should_close_client = True
            if endpoint.get("auth") and not self.token:
                await self.authenticate(client)

        try:
            async def worker():
                async with semaphore:
                    res = await self.execute_single_request(client, endpoint, target_base_url)
                    results.append(res)

            start_time = time.perf_counter()
            tasks = [asyncio.create_task(worker()) for _ in range(total_requests)]
            await asyncio.gather(*tasks)
            duration_sec = time.perf_counter() - start_time
        finally:
            if should_close_client:
                await client.aclose()

        latencies = [r["latency_ms"] for r in results]
        statuses = [r["status"] for r in results]
        latencies.sort()

        errors_5xx = [r for r in results if r["status"] >= 500 or r["status"] == 0]

        p50 = statistics.median(latencies) if latencies else 0.0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0
        rps = (len(results) / duration_sec) if duration_sec > 0 else 0.0

        status_dist = {str(code): statuses.count(code) for code in sorted(set(statuses))}

        return {
            "name": endpoint["name"],
            "method": endpoint.get("method", "GET"),
            "path": endpoint["path"],
            "concurrency": concurrency,
            "total_requests": len(results),
            "duration_seconds": round(duration_sec, 3),
            "rps": round(rps, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "unhandled_5xx_count": len(errors_5xx),
            "errors": [e["error"] for e in errors_5xx[:5]],
            "status_distribution": status_dist,
        }

    async def run_phase(
        self,
        phase_num: int,
        concurrency: int,
        requests_per_endpoint: int,
        include_frontend: bool = True,
        backend_endpoints: Optional[List[Dict[str, Any]]] = None,
        frontend_routes: Optional[List[Dict[str, Any]]] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Execute a full load phase across all backend endpoints and frontend routes."""
        endpoints = backend_endpoints if backend_endpoints is not None else TARGET_BACKEND_ENDPOINTS
        routes = frontend_routes if frontend_routes is not None else TARGET_FRONTEND_ROUTES

        phase_results: List[Dict[str, Any]] = []
        limits = httpx.Limits(max_keepalive_connections=concurrency * 2, max_connections=concurrency * 4)

        async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as client:
            await self.authenticate(client)

            # Test backend endpoints
            for ep in endpoints:
                res = await self.run_scenario(
                    endpoint=ep,
                    concurrency=concurrency,
                    total_requests=requests_per_endpoint,
                    base_url=self.backend_url,
                    client=client,
                )
                phase_results.append(res)
                if verbose:
                    print(f"  [Phase {phase_num}] {ep['name']:<24}: {res['total_requests']} reqs, {res['rps']:.1f} RPS, p95={res['p95_ms']:.1f}ms, 5xx={res['unhandled_5xx_count']}")
                    sys.stdout.flush()

        # Test frontend routes if enabled and available
        frontend_tested = False
        frontend_skipped_reason = None
        if include_frontend:
            frontend_available = await self.check_frontend_availability()
            if frontend_available:
                frontend_tested = True
                async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as f_client:
                    for route in routes:
                        res = await self.run_scenario(
                            endpoint=route,
                            concurrency=concurrency,
                            total_requests=requests_per_endpoint,
                            base_url=self.frontend_url,
                            client=f_client,
                        )
                        phase_results.append(res)
                        if verbose:
                            print(f"  [Phase {phase_num}] {route['name']:<24}: {res['total_requests']} reqs, {res['rps']:.1f} RPS, p95={res['p95_ms']:.1f}ms, 5xx={res['unhandled_5xx_count']}")
                            sys.stdout.flush()
            else:
                frontend_skipped_reason = f"Frontend server at {self.frontend_url} is not responding (gracefully skipped)."

        # Verify backend process stability after phase
        backend_survived = await self.check_backend_health()

        total_reqs = sum(r["total_requests"] for r in phase_results)
        total_5xx = sum(r["unhandled_5xx_count"] for r in phase_results)
        total_time = sum(r["duration_seconds"] for r in phase_results)
        avg_rps = (total_reqs / total_time) if total_time > 0 else 0.0

        return {
            "phase": phase_num,
            "concurrency": concurrency,
            "requests_per_endpoint": requests_per_endpoint,
            "total_requests": total_reqs,
            "unhandled_5xx_count": total_5xx,
            "backend_survived": backend_survived,
            "frontend_tested": frontend_tested,
            "frontend_skipped_reason": frontend_skipped_reason,
            "aggregate_rps": round(avg_rps, 2),
            "scenarios": phase_results,
        }

    async def run_all_phases(
        self,
        phases: Optional[List[Dict[str, Any]]] = None,
        include_frontend: bool = True,
        requests_multiplier: float = 1.0,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute all 4 concurrency stress test phases (5, 15, 25, 50).
        Tracks RSS memory before/after and reports comprehensive telemetry.
        """
        active_phases = phases or DEFAULT_PHASES

        # Record baseline memory
        client_rss_before = get_current_rss_mb()
        server_rss_before = get_pid_rss_mb(self.server_pid)

        if verbose:
            print(f"\n>>> Starting Concurrent Stress Harness across {len(active_phases)} phases...")
            print(f">>> Initial RSS Memory — Client: {client_rss_before:.1f} MB, Server PID {self.server_pid or 'N/A'}: {server_rss_before or 0.0:.1f} MB")
            sys.stdout.flush()

        start_time = time.perf_counter()
        phase_reports = []

        for p_cfg in active_phases:
            p_num = p_cfg.get("phase", 1)
            concurrency = p_cfg["concurrency"]
            reqs = int(p_cfg["requests_per_endpoint"] * requests_multiplier)
            reqs = max(reqs, 5)

            if verbose:
                print(f"\n>>> Executing Phase {p_num}: Concurrency {concurrency} ({reqs} reqs/endpoint)...")
                sys.stdout.flush()

            p_report = await self.run_phase(
                phase_num=p_num,
                concurrency=concurrency,
                requests_per_endpoint=reqs,
                include_frontend=include_frontend,
                verbose=verbose,
            )
            phase_reports.append(p_report)

        total_wall_clock = time.perf_counter() - start_time

        # Record post-load memory
        client_rss_after = get_current_rss_mb()
        server_rss_after = get_pid_rss_mb(self.server_pid)

        # Aggregate metrics
        all_scenarios = [s for p in phase_reports for s in p["scenarios"]]
        total_requests = sum(s["total_requests"] for s in all_scenarios)
        total_5xx = sum(s["unhandled_5xx_count"] for s in all_scenarios)
        all_backends_survived = all(p["backend_survived"] for p in phase_reports)

        overall_rps = (total_requests / total_wall_clock) if total_wall_clock > 0 else 0.0

        server_rss_delta = (
            round(server_rss_after - server_rss_before, 2)
            if (server_rss_before is not None and server_rss_after is not None)
            else None
        )
        client_rss_delta = round(client_rss_after - client_rss_before, 2)

        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "backend_url": self.backend_url,
            "frontend_url": self.frontend_url,
            "server_pid": self.server_pid,
            "total_requests": total_requests,
            "total_wall_clock_seconds": round(total_wall_clock, 2),
            "overall_rps": round(overall_rps, 2),
            "unhandled_5xx_count": total_5xx,
            "unhandled_5xx_rate_pct": round((total_5xx / total_requests * 100.0) if total_requests else 0.0, 4),
            "zero_process_crashes": all_backends_survived,
            "client_rss_mb_before": round(client_rss_before, 2),
            "client_rss_mb_after": round(client_rss_after, 2),
            "client_rss_delta_mb": client_rss_delta,
            "server_rss_mb_before": round(server_rss_before, 2) if server_rss_before is not None else None,
            "server_rss_mb_after": round(server_rss_after, 2) if server_rss_after is not None else None,
            "server_rss_delta_mb": server_rss_delta,
            "phases": phase_reports,
        }

    def run(self, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper to run the full benchmark harness."""
        return asyncio.run(self.run_all_phases(**kwargs))


def print_benchmark_report(report: Dict[str, Any]):
    """Format and print a rich console report for the stress test results."""
    divider = "=" * 95
    sub_divider = "-" * 95

    print(f"\n{divider}")
    print(" CLEARHIRE.AI — AUTOMATED CONCURRENT STRESS & STABILITY BENCHMARK REPORT")
    print(f"{divider}")
    print(f"Timestamp:       {report['timestamp']}")
    print(f"Backend Target:  {report['backend_url']}")
    print(f"Frontend Target: {report['frontend_url']}")
    print(f"Detected Server PID: {report.get('server_pid') or 'N/A'}")
    print(f"Total Requests:  {report['total_requests']:,}")
    print(f"Total Duration:  {report['total_wall_clock_seconds']}s")
    print(f"Overall RPS:     {report['overall_rps']:.1f} req/s")
    print(f"Unhandled 5xx:   {report['unhandled_5xx_count']} ({report['unhandled_5xx_rate_pct']}%)")
    print(f"Server Stability: {'PASSED (Zero Crashes)' if report['zero_process_crashes'] else 'FAILED (Server Crashed)'}")

    if report.get('server_rss_mb_before') is not None:
        print(f"Server Memory:   {report['server_rss_mb_before']:.1f} MB -> {report['server_rss_mb_after']:.1f} MB (Delta: {report['server_rss_delta_mb']:+.1f} MB)")
    print(f"Client Memory:   {report['client_rss_mb_before']:.1f} MB -> {report['client_rss_mb_after']:.1f} MB (Delta: {report['client_rss_delta_mb']:+.1f} MB)")
    print(f"{divider}\n")

    for p in report["phases"]:
        phase_title = f"Phase {p['phase']}: Concurrency {p['concurrency']} ({p['requests_per_endpoint']} reqs/endpoint)"
        print(f"[{phase_title}]")
        if p.get("frontend_skipped_reason"):
            print(f"  Note: {p['frontend_skipped_reason']}")

        header = f"{'Endpoint':<26} | {'Meth':<4} | {'Conc':<4} | {'Reqs':<5} | {'RPS':<7} | {'p50(ms)':<8} | {'p95(ms)':<8} | {'p99(ms)':<8} | {'5xx':<4} | Statuses"
        print(header)
        print(sub_divider)

        for s in p["scenarios"]:
            stat_str = " ".join([f"{k}:{v}" for k, v in s["status_distribution"].items()])
            row = (
                f"{s['name']:<26} | "
                f"{s['method']:<4} | "
                f"{s['concurrency']:<4} | "
                f"{s['total_requests']:<5} | "
                f"{s['rps']:<7.1f} | "
                f"{s['p50_ms']:<8.1f} | "
                f"{s['p95_ms']:<8.1f} | "
                f"{s['p99_ms']:<8.1f} | "
                f"{s['unhandled_5xx_count']:<4} | "
                f"{stat_str}"
            )
            print(row)
        print(sub_divider)
        print(f"Phase Aggregate Throughput: {p['aggregate_rps']:.1f} RPS | 5xx Errors: {p['unhandled_5xx_count']} | Health: {'OK' if p['backend_survived'] else 'CRASHED'}\n")

    print(f"{divider}")
    if report["unhandled_5xx_count"] == 0 and report["zero_process_crashes"]:
        print("VERDICT: PASS — 0% unhandled 5xx exceptions, zero crashes, robust stability under concurrency.")
    else:
        print("VERDICT: FAIL — Violations detected under concurrent load.")
    print(f"{divider}\n")


def parse_args():
    parser = argparse.ArgumentParser(description="ClearHire Automated Concurrent Stress Testing Harness")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000", help="FastAPI backend base URL")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:3000", help="Next.js frontend base URL")
    parser.add_argument("--concurrency", type=int, default=None, help="Run single concurrency phase with specified level")
    parser.add_argument("--requests-per-endpoint", type=int, default=None, help="Override requests per endpoint")
    parser.add_argument("--quick", action="store_true", help="Quick mode for rapid smoke verification (fewer requests)")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend route testing")
    parser.add_argument("--output-json", type=str, default=None, help="File path to save JSON benchmark report")
    return parser.parse_args()


def main():
    args = parse_args()
    harness = StressHarness(
        backend_url=args.backend_url,
        frontend_url=args.frontend_url,
    )

    phases = [dict(p) for p in DEFAULT_PHASES]
    multiplier = 0.5 if args.quick else 1.0

    if args.concurrency:
        reqs = args.requests_per_endpoint or (args.concurrency * 2)
        phases = [{"phase": 1, "name": f"Custom Concurrency {args.concurrency}", "concurrency": args.concurrency, "requests_per_endpoint": reqs}]
    elif args.requests_per_endpoint:
        for p in phases:
            p["requests_per_endpoint"] = args.requests_per_endpoint

    report = harness.run(
        phases=phases,
        include_frontend=not args.skip_frontend,
        requests_multiplier=multiplier,
        verbose=True,
    )

    print_benchmark_report(report)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {args.output_json}")

    # Return exit code: 0 if success, 1 if failures
    if report["unhandled_5xx_count"] > 0 or not report["zero_process_crashes"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
