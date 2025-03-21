import { Link } from "react-router-dom";
import "./navbar.css";
export const Navbar = () => {
    return (
        <div className="navbar" data-testid="navbar">
            <div>
                <Link to="/" className="">
                    <button className="pl-2 pr-2 text-center hover:text-yellow-500">
                        Home
                    </button>
                </Link>
            </div>
            <div>
                <Link to="/summaries" >
                    <button className="pl-2 pr-2  text-center hover:text-yellow-500">
                        Resúmenes
                    </button>
                </Link>
                <Link to="/about">
                    <button className="pl-2 pr-2 text-center hover:text-yellow-500">
                        Acerca
                    </button>
                </Link>
            </div>
        </div>
    );
};

