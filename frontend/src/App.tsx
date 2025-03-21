import './App.css'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ConfigProvider } from './contexts'
// import { routes } from './routes'
import { Home } from './pages/home/Home';

export function App() {
  return (
    // <ConfigProvider>
      /* <BrowserRouter> */
      <>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/home" element={<Home />} />
            <Route path="*" element={<Home />} />
          </Routes>
      </>
      // </BrowserRouter>
    // </ConfigProvider>
  )
}
