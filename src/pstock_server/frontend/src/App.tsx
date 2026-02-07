/**
 * App Component
 *
 * Main application component with routing.
 */
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Marketplace } from './pages/Marketplace';
import { Chat } from './pages/Chat';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Marketplace />} />
        <Route path="/chat/:agentId" element={<Chat />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
