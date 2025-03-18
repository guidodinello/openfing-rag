import { Link } from "react-router-dom";
import "./navbar.module.scss";
export const Navbar = () => {
    return (
        <div className="flex justify-between p-4 shadow-md" data-testid="navbar">
            <Link to="/" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Home
                </button>
            </Link>
            <Link to="/summaries" >
                <button className="bg-blue-500 hover:bg-blue-700 text-black font-bold py-2 px-4 rounded">
                    Resúmenes
                </button>
            </Link>
            <Link to="/about" className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Acerca
                </button>
            </Link>
        </div>
    );
};

