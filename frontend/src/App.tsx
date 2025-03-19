import './App.css'
import { Navbar } from './common/navbar'
import { Route, Routes } from 'react-router-dom'
import { About, Home, Summaries, NotFound } from './pages'

function App() {
  return (
    <>
      <Navbar />
      <div className='main-container'>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="summaries" element={<Summaries />} />
          <Route path="/*" element={<NotFound />} />
        </Routes>
      </div>
    </>
  )
}

export default App
