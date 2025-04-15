const domain = "localhost";
const protocol = "http";
const transcriberPort = 8001;
const generativePort = 8002;
const transcriberUrl = `${protocol}://${domain}:${transcriberPort}`;
const generativeUrl = `${protocol}://${domain}:${generativePort}`;

export const generativeRoutes = {
  generate: `${generativeUrl}/generate`,
};

export const transcriberRoutes = {
  getTranscription: (
    course_url: string,
    class_number: number,
    model_size: string
  ) =>
    `${transcriberUrl}/transcribe/${course_url}/${class_number}?${model_size}`,
  getTranscriptionStatus: (course_url: string, class_number: number) =>
    `${transcriberUrl}/transcribe/${course_url}/${class_number}`,
};
