import { Link } from "react-router-dom";
import "./navbar.css";
export const Navbar = () => {
    return (
        <div className="flex justify-between p-4 shadow-md" data-testid="navbar">
            <Link to="/" className="">
                <button className="">
                    Home
                </button>
            </Link>
            <Link to="/summaries" >
                <button className="">
                    Resúmenes
                </button>
            </Link>
            <Link to="/about" className="">
                <button className="">
                    Acerca
                </button>
            </Link>
        </div>
    );
};

