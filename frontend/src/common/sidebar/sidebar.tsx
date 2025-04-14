import { FaChevronRight, FaChevronLeft } from "react-icons/fa";
import { useConfig } from "../../hooks";

export const Sidebar = () => {
  const { config, toggleSidebar } = useConfig();
  const { isOpen } = config;
  return (
    // <div className="flex h-screen">
    <div
      className={`h-screen transition-all duration-300 ease-in-out ${
        isOpen ? "w-64" : "w-12"
      } bg-gray-800 text-white`}
    >
      <div className="flex flex-row-reverse justify-between items-center p-4">
        <button
          onClick={toggleSidebar}
          // className="relative right-4 text-white"
        >
          {isOpen ? <FaChevronLeft size={24} /> : <FaChevronRight size={24} />}
        </button>
      </div>
      <ul className={`p-4 ${isOpen ? "" : "hidden"}`}>
        <li className="mb-2">
          <a href="#" className="text-blue-400 hover:text-blue-300">
            Home
          </a>
        </li>
        <li className="mb-2">
          <a href="#" className="text-blue-400 hover:text-blue-300">
            About
          </a>
        </li>
        <li className="mb-2">
          <a href="#" className="text-blue-400 hover:text-blue-300">
            Contact
          </a>
        </li>
      </ul>
    </div>
  );
};
