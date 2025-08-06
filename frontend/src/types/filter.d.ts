export interface Course {
    subtitle: string;
    courseKey: string;
    classes: number[];
}

export interface CourseData {
    [title: string]: Course[];
}

export interface FilterOptions {
    title: string;
    subtitle: string;
    classNumber: number | null;
}

export interface UseCourseFiltersReturn {
    availableClasses: number[];
    availableSubtitles: string[];
    availableTitles: string[];
    classInput: number;
    filters: FilterOptions;
    getFirstResult;
    handleClassChange;
    handleClearFilters;
    handleSubtitleChange;
    handleTitleChange;
    subtitleInput: string;
    titleInput: string;
}
