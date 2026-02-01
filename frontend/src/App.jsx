import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Configurator from './pages/Configurator';
import Search from './pages/Search';
import PartBuilder from './pages/PartBuilder';
import GuidedSelector from './pages/GuidedSelector';
import Settings from './pages/Settings';

function App() {
    return (
        <BrowserRouter>
            <div className="app-layout">
                <Sidebar />
                <main className="main-content">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/upload" element={<Upload />} />
                        <Route path="/guided" element={<GuidedSelector />} />
                        <Route path="/configure/:datasheetId" element={<Configurator />} />
                        <Route path="/build/:datasheetId" element={<PartBuilder />} />
                        <Route path="/search" element={<Search />} />
                        <Route path="/settings" element={<Settings />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}

export default App;

