import "./App.css";
import { /*BrowserRouter,*/ Route, Routes } from "react-router-dom";
// import { ConfigProvider } from './contexts'
// import { routes } from './routes'
import { Home, Summaries } from "./pages";
import { ConfigProvider } from "./contexts";
import { Course } from "./pages/course/course";
import "./index.css";

export function App() {
  return (
    <>
      <ConfigProvider>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/summaries" element={<Summaries />} />
          <Route path="/course/*" element={<Course />} />
          <Route path="/summaries/:id" element={<Summaries />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </ConfigProvider>
    </>
  );
}
