export type FilteringType = "none" | "byCourse" | "bySubCourse" | "byClass";

export interface Course {
    subtitle: string;
    courseKey: string;
    classes: number[];
}

export interface CourseData {
    [title: string]: Course[];
}

export interface Filters {
    byCourse: string?;
    bySubCourse: string?;
    byClass: number?;
}
