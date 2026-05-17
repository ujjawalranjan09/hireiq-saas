import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Welcome } from './pages/Welcome';
import { Interview } from './pages/Interview';
import { Completed } from './pages/Completed';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/interview/:token" element={<Welcome />} />
        <Route path="/interview/:token/session" element={<Interview />} />
        <Route path="/interview/:token/completed" element={<Completed />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
