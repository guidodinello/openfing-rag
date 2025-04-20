import { FaChevronRight, FaChevronLeft } from "react-icons/fa";
import { useConfig } from "../../hooks";
import { useEffect, useState } from "react";

import "./sidebar.css";
import { Link } from "react-router-dom";

// ...existing imports...

export const Sidebar = () => {
  const [courses, setCourses] = useState<{ key: string; name: string }[]>([]);
  useEffect(() => {
    fetch("/src/demo_data/ScrapInfo/CoursesAcronyms.json")
      .then((res) =>
        res.json().then((data) => {
          const courseList = Object.entries(data).map(([key, name]) => ({
            key: key as string,
            name: name as string,
          }));
          setCourses(courseList);
        })
      )
      .catch((err) => {
        console.error("Failed to load courses:", err);
      });
  }, []);
  const { config, toggleSidebar } = useConfig();
  const { isOpen } = config;
  return (
    <div
      className={`h-screen transition-all duration-300 ease-in-out ${
        isOpen ? "w-64" : "w-12"
      } bg-gray-800 text-white`}
    >
      <div className="flex flex-row-reverse justify-between items-center p-4 ">
        <button onClick={toggleSidebar}>
          {isOpen ? <FaChevronLeft size={24} /> : <FaChevronRight size={24} />}
        </button>
      </div>
      <ul
        className={`p-1 ${
          isOpen ? "" : "hidden"
        } overflow-y-auto max-h-11/12 hide-scrollbar flex flex-col items-start `}
      >
        {courses.map(({ key, name }) => (
          <li key={key} className="flex items-start p-2 flex-col">
            <Link to={`/course/${key}`}>
              <button className="scroll-text text-start w-64 whitespace-nowrap hide-scrollbar text-ellipsis">
                {name}
              </button>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
};
