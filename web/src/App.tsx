import { BrowserRouter, Route, Routes } from 'react-router'

import { Sidebar } from './components/Sidebar'
import { WorkspaceSearch } from './components/WorkspaceSearch'
import { NewRequestPage } from './features/new-request/NewRequestPage'
import { ObservabilityPage } from './features/observability/ObservabilityPage'
import { RequestPage } from './features/request-detail/RequestPage'
import { RequestsPage } from './features/requests/RequestsPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-dvh p-2.5 sm:p-5 lg:p-6 2xl:px-12 2xl:py-8">
        <div className="glass-frame noise-texture mx-auto grid max-w-[2200px] min-h-[calc(100dvh-1.25rem)] grid-cols-[minmax(0,1fr)] overflow-hidden lg:h-[calc(100dvh-3rem)] 2xl:h-[calc(100dvh-4rem)] lg:min-h-[620px] lg:grid-cols-[272px_minmax(0,1fr)] 2xl:grid-cols-[300px_minmax(0,1fr)]">
          <Sidebar />
          <div className="dashboard-workspace flex min-h-0 min-w-0 flex-col">
            <div className="workspace-toolbar flex flex-wrap items-center justify-between gap-3 px-5 py-4 sm:px-7 lg:px-9">
              <p className="text-[10px] font-semibold tracking-[0.18em] text-muted">
                PRICE SCOUT <span className="px-1.5 text-peach">/</span> SHOPPING WORKSPACE
              </p>
              <WorkspaceSearch />
            </div>
            <main className="scroll-area min-h-0 flex-1 px-5 pb-6 sm:px-7 sm:pb-8 lg:px-9 lg:pb-9">
              <Routes>
                <Route path="/" element={<NewRequestPage />} />
                <Route path="/requests" element={<RequestsPage />} />
                <Route path="/requests/:requestId" element={<RequestPage />} />
                <Route path="/observability" element={<ObservabilityPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </BrowserRouter>
  )
}
