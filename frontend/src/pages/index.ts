import { About } from "./about/about";
import { Course } from "./course/course";
import { ErrorOcurred } from "./errorOccured/errorOcurred";
import { Home } from "./home/home";
import { LayoutType, withLayout } from "../hocs/with-layout";
import { NotFound } from "./notFound/notFound";
import { ReportError } from "./reportError/reportError";
import { Summaries } from "./summaries/summaries";

const WrappedAbout = withLayout(LayoutType.NavAndSidebar, About);
const WrappedCourse = withLayout(LayoutType.NavAndSidebar, Course);
const WrappedErrorOcurred = withLayout(LayoutType.NavAndSidebar, ErrorOcurred);
const WrappedHome = withLayout(LayoutType.NavAndSidebar, Home);
const WrappedNotFound = withLayout(LayoutType.NavAndSidebar, NotFound);
const WrappedReportError = withLayout(LayoutType.NavAndSidebar, ReportError);
const WrappedSummaries = withLayout(LayoutType.NavAndSidebar, Summaries);

export { WrappedAbout as About };
export { WrappedCourse as Course };
export { WrappedErrorOcurred as ErrorOcurred };
export { WrappedHome as Home };
export { WrappedNotFound as NotFound };
export { WrappedReportError as ReportError };
export { WrappedSummaries as Summaries };
