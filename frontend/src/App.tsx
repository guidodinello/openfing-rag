import './App.css'
import { /*BrowserRouter,*/ Route, Routes } from 'react-router-dom'
// import { ConfigProvider } from './contexts'
// import { routes } from './routes'
import { Home,Summaries } from './pages';
import { ConfigProvider } from './contexts';


export function App() {
  return (
    // <ConfigProvider>
      /* <BrowserRouter> */
      <ConfigProvider>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/summaries" element={<Summaries />} />
            <Route path="/summaries/:id" element={<Summaries />} />
            <Route path="*" element={<Home />} />
          </Routes>
      </ConfigProvider>
      // </BrowserRouter>
    // </ConfigProvider>
  )
}
