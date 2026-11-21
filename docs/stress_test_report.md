# ClearHire.AI High-Concurrency Stress Test & Reliability Report

**Date:** 2026-11-16 18:00:22 UTC  
**Concurrency Tiers Evaluated:** 5, 15, 25, 50 concurrent requests  
**Backend Endpoint:** `http://127.0.0.1:8000`  
**Frontend Endpoint:** `http://localhost:3000`  

---

## Executive Summary

| Category | Endpoint / Route | Max Concurrency | RPS @ 50c | p50 Latency (ms) | p95 Latency (ms) | 5xx Error Rate |
|---|---|---|---|---|---|---|
| Backend System | `Health Check` | 50 | 728.8 | 36.0ms | 61.2ms | 0% (0 errors) |
| Backend System | `Readiness Check` | 50 | 20.1 | 1539.15ms | 2433.06ms | 0% (0 errors) |
| Backend Auth/DB | `Auth Me (User Profile)` | 50 | 16.7 | 930.24ms | 2908.12ms | 0% (0 errors) |
| Backend Auth/DB | `Applications List` | 50 | 15.4 | 1239.65ms | 3156.63ms | 0% (0 errors) |
| Backend Compute | `Job Portal Search/Scrape` | 50 | 3.5 | 7999.04ms | 13785.24ms | 0% (0 errors) |
| Frontend SSR | `Login Page (Public SSR)` | 50 | 36.3 | 1226.44ms | 1351.0ms | 0% (0 errors) |
| Frontend SSR | `Story Landing Page (3D Engine SSR)` | 50 | 50.7 | 843.35ms | 948.38ms | 0% (0 errors) |
| Frontend SSR | `Applications Kanban Workspace SSR` | 50 | 55.5 | 851.42ms | 871.29ms | 0% (0 errors) |
| Frontend SSR | `Job Hunter Portal SSR` | 50 | 47.0 | 1013.29ms | 1033.23ms | 0% (0 errors) |
| Frontend SSR | `JD Analyzer Workspace SSR` | 50 | 57.6 | 631.04ms | 842.39ms | 0% (0 errors) |
| Frontend SSR | `Resmat AI Resume Tailor SSR` | 50 | 50.5 | 942.78ms | 957.17ms | 0% (0 errors) |
| Frontend SSR | `Student Lab & Prep Portal SSR` | 50 | 56.0 | 837.03ms | 863.72ms | 0% (0 errors) |
| Frontend SSR | `Funnel Analytics Executive Dashboard SSR` | 50 | 55.9 | 584.67ms | 863.19ms | 0% (0 errors) |

**Overall 5xx Error Rate Across All 1235 Stress Requests:** `0.00%`

---

## Detailed Latency Profiles by Concurrency Tier

### Backend System: Health Check
`GET http://127.0.0.1:8000/health`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.01s | 518.3 | 6.98ms | 8.12ms | 8.75ms | 8.75ms | 8.75ms | `200:5` |
| 15 | 0.02s | 750.1 | 6.17ms | 13.3ms | 19.21ms | 19.21ms | 19.21ms | `200:15` |
| 25 | 0.037s | 684.4 | 10.24ms | 20.49ms | 31.85ms | 34.68ms | 34.68ms | `200:25` |
| 50 | 0.069s | 728.8 | 16.12ms | 36.0ms | 61.2ms | 62.15ms | 62.15ms | `200:50` |

### Backend System: Readiness Check
`GET http://127.0.0.1:8000/ready`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 2.428s | 2.1 | 986.34ms | 2223.1ms | 2427.43ms | 2427.43ms | 2427.43ms | `200:5` |
| 15 | 2.453s | 6.1 | 986.01ms | 2304.75ms | 2447.48ms | 2447.48ms | 2447.48ms | `200:15` |
| 25 | 2.455s | 10.2 | 1007.88ms | 1064.38ms | 2409.41ms | 2447.37ms | 2447.37ms | `200:25` |
| 50 | 2.488s | 20.1 | 1010.17ms | 1539.15ms | 2433.06ms | 2468.44ms | 2468.44ms | `200:50` |

### Backend Auth/DB: Auth Me (User Profile)
`GET http://127.0.0.1:8000/api/auth/me`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.78s | 6.4 | 767.82ms | 773.13ms | 776.62ms | 776.62ms | 776.62ms | `200:5` |
| 15 | 0.941s | 15.9 | 799.65ms | 837.37ms | 936.21ms | 936.21ms | 936.21ms | `200:15` |
| 25 | 0.945s | 26.5 | 812.31ms | 850.99ms | 913.76ms | 924.48ms | 924.48ms | `200:25` |
| 50 | 3.002s | 16.7 | 869.74ms | 930.24ms | 2908.12ms | 2969.26ms | 2969.26ms | `200:50` |

### Backend Auth/DB: Applications List
`GET http://127.0.0.1:8000/api/applications/`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 1.023s | 4.9 | 1016.85ms | 1017.82ms | 1022.95ms | 1022.95ms | 1022.95ms | `200:5` |
| 15 | 1.155s | 13.0 | 1006.63ms | 1052.36ms | 1155.25ms | 1155.25ms | 1155.25ms | `200:15` |
| 25 | 1.142s | 21.9 | 1049.63ms | 1081.92ms | 1136.55ms | 1142.02ms | 1142.02ms | `200:25` |
| 50 | 3.24s | 15.4 | 1061.42ms | 1239.65ms | 3156.63ms | 3196.6ms | 3196.6ms | `200:50` |

### Backend Compute: Job Portal Search/Scrape
`POST http://127.0.0.1:8000/api/jobs/scrape`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 9.61s | 0.5 | 6823.89ms | 8356.13ms | 9607.55ms | 9607.55ms | 9607.55ms | `200:5` |
| 15 | 5.396s | 2.8 | 1746.48ms | 3564.18ms | 5391.98ms | 5391.98ms | 5391.98ms | `200:15` |
| 25 | 7.984s | 3.1 | 1833.98ms | 4899.74ms | 7714.97ms | 7975.32ms | 7975.32ms | `200:25` |
| 50 | 14.301s | 3.5 | 2207.18ms | 7999.04ms | 13785.24ms | 14287.48ms | 14287.48ms | `200:50` |

### Frontend SSR: Login Page (Public SSR)
`GET http://localhost:3000/login`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.118s | 42.3 | 114.66ms | 115.66ms | 118.01ms | 118.01ms | 118.01ms | `200:5` |
| 15 | 0.354s | 42.4 | 91.04ms | 345.31ms | 348.45ms | 348.45ms | 348.45ms | `200:15` |
| 25 | 0.564s | 44.3 | 44.39ms | 503.29ms | 554.65ms | 557.73ms | 557.73ms | `200:25` |
| 50 | 1.376s | 36.3 | 89.59ms | 1226.44ms | 1351.0ms | 1373.5ms | 1373.5ms | `200:50` |

### Frontend SSR: Story Landing Page (3D Engine SSR)
`GET http://localhost:3000/`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.11s | 45.6 | 29.53ms | 104.57ms | 105.8ms | 105.8ms | 105.8ms | `200:5` |
| 15 | 0.315s | 47.6 | 51.49ms | 203.02ms | 304.63ms | 304.63ms | 304.63ms | `200:15` |
| 25 | 0.517s | 48.4 | 56.24ms | 486.56ms | 501.63ms | 506.58ms | 506.58ms | `200:25` |
| 50 | 0.986s | 50.7 | 80.37ms | 843.35ms | 948.38ms | 982.28ms | 982.28ms | `200:50` |

### Frontend SSR: Applications Kanban Workspace SSR
`GET http://localhost:3000/applications`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.091s | 55.1 | 25.88ms | 85.36ms | 87.55ms | 87.55ms | 87.55ms | `200:5` |
| 15 | 0.299s | 50.1 | 40.42ms | 278.96ms | 291.59ms | 291.59ms | 291.59ms | `200:15` |
| 25 | 0.464s | 53.9 | 56.26ms | 437.48ms | 451.02ms | 457.25ms | 457.25ms | `200:25` |
| 50 | 0.902s | 55.5 | 76.93ms | 851.42ms | 871.29ms | 885.72ms | 885.72ms | `200:50` |

### Frontend SSR: Job Hunter Portal SSR
`GET http://localhost:3000/job-hunter`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.11s | 45.4 | 29.68ms | 103.65ms | 106.1ms | 106.1ms | 106.1ms | `200:5` |
| 15 | 0.306s | 49.1 | 41.36ms | 187.61ms | 298.57ms | 298.57ms | 298.57ms | `200:15` |
| 25 | 0.506s | 49.4 | 50.78ms | 480.03ms | 493.17ms | 497.34ms | 497.34ms | `200:25` |
| 50 | 1.065s | 47.0 | 97.4ms | 1013.29ms | 1033.23ms | 1044.22ms | 1044.22ms | `200:50` |

### Frontend SSR: JD Analyzer Workspace SSR
`GET http://localhost:3000/jd-analyzer`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.086s | 57.9 | 24.81ms | 80.96ms | 83.14ms | 83.14ms | 83.14ms | `200:5` |
| 15 | 0.246s | 60.9 | 41.23ms | 224.25ms | 237.54ms | 237.54ms | 237.54ms | `200:15` |
| 25 | 0.423s | 59.1 | 51.46ms | 396.3ms | 408.19ms | 415.05ms | 415.05ms | `200:25` |
| 50 | 0.869s | 57.6 | 80.22ms | 631.04ms | 842.39ms | 857.89ms | 857.89ms | `200:50` |

### Frontend SSR: Resmat AI Resume Tailor SSR
`GET http://localhost:3000/resmat-ai`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.089s | 56.5 | 24.59ms | 82.89ms | 85.23ms | 85.23ms | 85.23ms | `200:5` |
| 15 | 0.336s | 44.6 | 74.22ms | 236.13ms | 324.02ms | 324.02ms | 324.02ms | `200:15` |
| 25 | 0.459s | 54.5 | 58.58ms | 429.46ms | 444.3ms | 444.75ms | 444.75ms | `200:25` |
| 50 | 0.99s | 50.5 | 81.76ms | 942.78ms | 957.17ms | 961.7ms | 961.7ms | `200:50` |

### Frontend SSR: Student Lab & Prep Portal SSR
`GET http://localhost:3000/student-lab`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.096s | 52.3 | 29.05ms | 88.14ms | 90.59ms | 90.59ms | 90.59ms | `200:5` |
| 15 | 0.267s | 56.2 | 39.93ms | 241.85ms | 255.9ms | 255.9ms | 255.9ms | `200:15` |
| 25 | 0.532s | 47.0 | 46.54ms | 504.1ms | 522.14ms | 528.23ms | 528.23ms | `200:25` |
| 50 | 0.893s | 56.0 | 82.89ms | 837.03ms | 863.72ms | 882.74ms | 882.74ms | `200:50` |

### Frontend SSR: Funnel Analytics Executive Dashboard SSR
`GET http://localhost:3000/funnel-analytics`

| Concurrency | Duration (s) | RPS | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Status Codes |
|---|---|---|---|---|---|---|---|---|
| 5 | 0.091s | 54.7 | 26.93ms | 85.14ms | 87.68ms | 87.68ms | 87.68ms | `200:5` |
| 15 | 0.262s | 57.2 | 40.68ms | 243.46ms | 255.19ms | 255.19ms | 255.19ms | `200:15` |
| 25 | 0.424s | 58.9 | 47.6ms | 399.06ms | 411.09ms | 417.44ms | 417.44ms | `200:25` |
| 50 | 0.894s | 55.9 | 85.65ms | 584.67ms | 863.19ms | 881.55ms | 881.55ms | `200:50` |
