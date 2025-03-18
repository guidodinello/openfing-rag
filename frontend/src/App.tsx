import './App.css'
import { Navbar } from './common/navbar'
import { Route, Routes } from 'react-router-dom'
import { About, Home, Summaries } from './pages'

function App() {

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="about" element={<About />} />
        <Route path="summaries" element={<Summaries />} />
        <Route path="*" element={<Home />} />
      </Routes>
    </>
  )
}

export default App
