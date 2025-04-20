import dotenv from "dotenv";
dotenv.config();

const API_URL: string | undefined = process.env.REACT_APP_API_URL;
const PORT_API_TRANSCRIPTIONS: string | undefined =
  process.env.REACT_APP_PORT_API_TRANSCRIPTIONS;
const PORT_API_GENERATIVE: string | undefined =
  process.env.REACT_APP_PORT_API_GENERATIVE;
const PORT_API_SCRAPING: string | undefined =
  process.env.REACT_APP_PORT_API_SCRAPING;

export const API_ROUTES = {
  EXAMPLE: "/example",
  HEALTHCHECK: "/health-check",
  USER: {
    CONVERSATIONS: "/user/conversation/:id",
  },
  ABOUT: {
    ABOUT: "/about",
    TEAM: "/about/team",
    FAQ: "/about/faq",
  },
  SUMMARIES: {
    SUMMARY_COURSEACRONYM_CLASS: "/summaries/:course_acronym/:class_number",
  },
  API_SCRAPING: {
    SCRAPING: `${PORT_API_SCRAPING}/scraping`,
    SCRAPING_COURSEACRONYM_CLASS: `${PORT_API_SCRAPING}/scraping/:course_acronym/:class_number`,
    SCRAPING_COURSEACRONYM_CLASS_ID: `${PORT_API_SCRAPING}/scraping/:course_acronym/:class_number/:id`,
  },
  API_TRANSCRIPTION: {
    TRANSCRIPTION_COURSEACRONYM_CLASS: `${PORT_API_TRANSCRIPTIONS}/transcription/:course_acronym/:class_number`,
  },
  API_GENERATIVE: {
    GENERATIVE: `${PORT_API_GENERATIVE}/generative`,
    GENERATIVE_COURSEACRONYM_CLASS: `${PORT_API_GENERATIVE}/generative/:course_acronym/:class_number`,
  },
};
