import { About, ErrorOcurred, Home, NotFound, ReportError, Summaries } from "../pages";
import { RouteName } from "./routes";


const RouteComponent = {
    [RouteName.About]: About,
    [RouteName.ErrorOcurred]: ErrorOcurred,
    [RouteName.Home]: Home,
    [RouteName.NotFound]: NotFound,
    [RouteName.ReportError]: ReportError,
    [RouteName.Summaries]: Summaries,
};

export { RouteComponent };
