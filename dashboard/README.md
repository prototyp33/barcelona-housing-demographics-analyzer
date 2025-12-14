# Barcelona Housing Dashboard - React Frontend

Modern, production-ready React dashboard for analyzing housing and demographic data in Barcelona.

## 🚀 Quick Start

### Prerequisites

- **Node.js**: v20.19+ or v22.12+ recommended (v18+ will work with warnings)
- **npm**: v10+

### Installation

```bash
cd dashboard
npm install
```

### Development

```bash
# Start development server with hot reload
npm run dev

# Access at http://localhost:5173
```

### Build

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

### Linting

```bash
npm run lint
```

---

## 📁 Project Structure

```
dashboard/
├── public/                 # Static assets
├── src/
│   ├── components/         # React components
│   │   ├── layout/         # Layout components (Sidebar, Header, AppLayout)
│   │   ├── common/         # Reusable UI components (Card, Loading)
│   │   ├── charts/         # Chart components (Recharts wrappers)
│   │   └── maps/           # Map components (Leaflet wrappers)
│   ├── pages/              # Page components
│   │   ├── OverviewPage.tsx
│   │   ├── RentPage.tsx
│   │   ├── PricesPage.tsx
│   │   ├── DemographicsPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── hooks/              # Custom React hooks
│   │   ├── useBarrios.ts
│   │   ├── useDemographics.ts
│   │   └── useHousingPrices.ts
│   ├── services/           # API service layer
│   │   ├── api.ts          # Axios instance
│   │   ├── geography.service.ts
│   │   ├── demographics.service.ts
│   │   └── housing.service.ts
│   ├── stores/             # State management (Zustand)
│   │   ├── filterStore.ts
│   │   └── uiStore.ts
│   ├── types/              # TypeScript type definitions
│   │   ├── api.types.ts
│   │   └── common.types.ts
│   ├── App.tsx             # Main app with routing
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── .env.example            # Environment variables template
├── vite.config.ts          # Vite configuration
└── package.json            # Dependencies and scripts
```

---

## 🛠 Technology Stack

| Category             | Technology              | Version | Purpose                         |
| -------------------- | ----------------------- | ------- | ------------------------------- |
| **Core**             | React                   | 19.2    | UI library                      |
|                      | TypeScript              | 5.9     | Type safety                     |
|                      | Vite                    | 7.2     | Build tool & dev server         |
|                      | SWC                     | 4.2     | Fast TypeScript/JSX compilation |
| **Routing**          | React Router DOM        | 7.x     | Client-side routing             |
| **State Management** | Zustand                 | 5.x     | Lightweight global state        |
|                      | TanStack React Query    | 5.x     | Server state & caching          |
| **HTTP Client**      | Axios                   | 1.x     | API requests with interceptors  |
| **Charts**           | Recharts                | 2.x     | Data visualization              |
| **Maps**             | React Leaflet + Leaflet | ^4 + ^1 | Interactive maps & choropleths  |
| **Linting**          | ESLint                  | 9.x     | Code quality                    |

---

## 🌐 API Integration

The dashboard connects to a backend API (Python ETL pipeline). Configure the API base URL:

### 1. Copy environment template

```bash
cp .env.example .env
```

### 2. Edit `.env` file

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG=true
```

### 3. Backend proxy

Vite is configured to proxy `/api/*` requests to `http://localhost:8000`:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

**Usage in frontend**:

```typescript
// Automatically proxies to http://localhost:8000/barrios
const response = await apiClient.get("/api/barrios");
```

---

## 📄 Pages

| Route         | Component          | Description                                   |
| ------------- | ------------------ | --------------------------------------------- |
| `/`           | `OverviewPage`     | Market cockpit with KPIs                      |
| `/renta`      | `RentPage`         | Household income & affordability analysis     |
| `/precios`    | `PricesPage`       | Housing sale & rental prices (€/m²)           |
| `/demografia` | `DemographicsPage` | Population structure, age groups, nationality |
| `*`           | `NotFoundPage`     | 404 error page                                |

---

## 🎨 Styling

- **CSS Modules**: Component-scoped styles (e.g., `Card.css`, `Sidebar.css`)
- **Global Styles**: Design tokens in `index.css` (CSS variables)
- **Responsive**: Mobile-first approach with breakpoints at 768px

**Color Palette** (defined in `index.css`):

```css
:root {
  --primary: #3b82f6; /* Blue */
  --secondary: #10b981; /* Green */
  --danger: #ef4444; /* Red */
  --gray-50: #f9fafb; /* Background */
  --gray-900: #1a1a1a; /* Text */
}
```

---

## 🔌 Custom Hooks

### `useBarrios()`

Fetch barrio list with React Query caching:

```typescript
import { useBarrios } from "@/hooks/useBarrios";

const { data, isLoading, error } = useBarrios();
```

### `useDemographics(filters)`

Fetch demographic data with optional filters:

```typescript
import { useDemographics } from "@/hooks/useDemographics";

const { data } = useDemographics({
  barrio_id: 42,
  year: 2023,
});
```

### `useHousingPrices(filters)`

Fetch housing prices:

```typescript
import { useHousingPrices } from "@/hooks/useHousingPrices";

const { data } = useHousingPrices({ year: 2024 });
```

---

## 🗄 State Management

### Global Filters (Zustand)

```typescript
import { useFilterStore } from "@/stores/filterStore";

const { filters, setBarrio, setYear } = useFilterStore();

setBarrio(42);
setYear(2023);
```

### UI State

```typescript
import { useUIStore } from "@/stores/uiStore";

const { sidebarOpen, toggleSidebar, theme, toggleTheme } = useUIStore();
```

---

## 🧪 Testing

TODO: Add unit tests with Vitest and component tests with React Testing Library.

```bash
# Future commands
npm run test        # Run tests
npm run test:ui     # Open Vitest UI
npm run coverage    # Generate coverage report
```

---

## 🚢 Deployment

### Build for Production

```bash
npm run build
```

**Output**: `dist/` directory with optimized static files.

### Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

### Deploy to Netlify

Drag and drop `dist/` folder to [Netlify Drop](https://app.netlify.com/drop).

Or use CLI:

```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

---

## 📊 Data Flow

```
User Interaction → React Component
       ↓
Custom Hook (React Query)
       ↓
Service Layer (Axios)
       ↓
Vite Proxy (/api → :8000)
       ↓
Backend API (Python)
       ↓
SQLite Database
```

---

## 🐛 Troubleshooting

### Issue: "Cannot find module '@/...'"

**Solution**: Ensure `tsconfig.app.json` has path mappings:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Issue: API calls failing (CORS or 404)

**Solution**:

1. Verify backend is running on `http://localhost:8000`
2. Check `.env` has correct `VITE_API_BASE_URL`
3. Ensure Vite proxy is configured in `vite.config.ts`

### Issue: Node.js version warning

**Solution**: Upgrade to Node.js 20.19+ or 22.12+:

```bash
# Using nvm
nvm install 20
nvm use 20
```

---

## 🤝 Contributing

1. Create feature branch from `feature/dashboard-react`
2. Follow TypeScript strict mode
3. Run `npm run lint` before committing
4. Keep components small and focused
5. Use custom hooks for data fetching
6. Document complex logic with comments

---

## 📝 License

MIT License - See [LICENSE](../LICENSE) file in root directory.
