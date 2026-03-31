# Frontend Segment

## Overview
Modern React/Next.js web dashboard for users to manage job preferences, track applications, and view automation results.

## Architecture

```
src/
├── pages/
│   ├── _app.tsx             # App wrapper
│   ├── _document.tsx        # HTML document
│   ├── index.tsx            # Dashboard home
│   ├── jobs.tsx             # Job listings page
│   ├── applications.tsx      # Application tracking
│   ├── resumes.tsx          # Resume management
│   ├── preferences.tsx      # User preferences
│   ├── settings.tsx         # App settings
│   └── auth/
│       ├── login.tsx
│       └── signup.tsx
│
├── components/
│   ├── Layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Layout.tsx
│   ├── Cards/
│   │   ├── JobCard.tsx
│   │   ├── ApplicationCard.tsx
│   │   └── StatCard.tsx
│   ├── Forms/
│   │   ├── JobFilterForm.tsx
│   │   ├── PreferenceForm.tsx
│   │   └── ResumeUploadForm.tsx
│   ├── Tables/
│   │   ├── JobsTable.tsx
│   │   └── ApplicationsTable.tsx
│   └── Modals/
│       ├── JobDetailModal.tsx
│       └── ApplyConfirmModal.tsx
│
├── api/
│   ├── client.ts            # Axios instance
│   ├── endpoints.ts         # API URL definitions
│   ├── jobs.ts              # Job API calls
│   ├── applications.ts      # Application API calls
│   ├── resumes.ts           # Resume API calls
│   └── auth.ts              # Auth API calls
│
├── hooks/
│   ├── useAuth.ts           # Auth context hook
│   ├── useJobs.ts           # Job data hook
│   ├── useApplications.ts   # Application data hook
│   └── useFetch.ts          # Generic fetch hook
│
├── context/
│   ├── AuthContext.tsx      # Authentication state
│   └── PreferencesContext.tsx # User preferences
│
├── types/
│   ├── index.ts             # Shared types
│   ├── api.ts               # API response types
│   └── models.ts            # Domain models
│
├── utils/
│   ├── formatters.ts        # Format utilities
│   ├── validators.ts        # Input validation
│   └── helpers.ts           # Helper functions
│
├── styles/
│   ├── globals.css
│   ├── variables.css
│   └── components/
│
└── config.ts                # App configuration

public/
├── favicon.ico
├── icons/
└── images/

tests/
├── components/
├── pages/
└── utils/

.env.example
next.config.js
tsconfig.json
tailwind.config.js
```

## Pages & Features

### Dashboard (`/`)
- Welcome message
- Quick stats (total jobs, applications, success rate)
- Recent applications
- Upcoming job matches
- Quick action buttons

### Jobs Page (`/jobs`)
- List all scraped jobs
- Filter by: company, location, salary, skills
- Sort options
- Job details modal
- Manual apply option

### Applications Page (`/applications`)
- Track all submitted applications
- Status: Applied, Reviewing, Interview, Offer, Rejected
- Filter by status, date, company
- View custom resume used
- Response tracking

### Resumes Page (`/resumes`)
- Upload new resumes
- Manage resume templates
- Preview resumes
- Mark as primary
- Delete old resumes

### Preferences Page (`/preferences`)
- Target companies (Infosys, TCS, etc.)
- Job titles (Senior Developer, etc.)
- Skills required/preferred
- Location preferences
- Salary expectations
- Experience level
- Employment type

### Settings Page (`/settings`)
- Account settings
- Automation schedule
- Email notifications
- API key management
- Data export/import

## Environment Variables

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Job Automation Tool
NEXT_PUBLIC_ENV=development

# Auth
NEXT_PUBLIC_JWT_STORAGE_KEY=auth_token
```

## Key Components

### JobCard
Displays individual job with:
- Company logo
- Job title & company
- Location & salary
- Match percentage
- Quick apply button

### ApplicationTracker
Shows application status with timeline:
- Application date
- Status updates
- Interview dates
- Offer details

### JobFilter
Advanced filtering with:
- Company multi-select
- Salary range slider
- Location autocomplete
- Skills checkboxes
- Experience level dropdown

### ResumeUploader
Drag-and-drop resume upload:
- PDF/DOCX support
- File preview
- Parsing feedback
- Template naming

## State Management

Using **Zustand** for simple state:
```typescript
- jobsStore (jobs list, filters)
- applicationsStore (applications data)
- authStore (user auth state)
- preferencesStore (user preferences)
```

## API Integration

All API calls through `api/` directory:
```typescript
// Usage example
const { data: jobs } = await getJobs({ 
  skip: 0, 
  limit: 20,
  filters: { location: 'Bangalore' }
})
```

## Styling

- **Framework:** Tailwind CSS
- **UI Library:** Headless UI / Radix UI
- **Icons:** Lucide React or Tabler Icons
- **Theme:** Light/Dark mode support

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint & format
npm run lint
npm run format
```

## Production Build

```bash
npm run build
npm run start
```

## Performance Optimizations

- Image optimization with Next.js Image
- Code splitting with dynamic imports
- API request caching with SWR/React Query
- Lazy loading pagination
- Service worker for offline support

## Security

- JWT token in httpOnly cookies
- CSRF protection
- Input validation & sanitization
- XSS prevention
- Rate limiting on API calls
