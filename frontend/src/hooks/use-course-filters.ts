import { useMemo, useState } from "react";
import type {
    CourseData,
    UseCourseFiltersReturn,
    FilterOptions,
} from "@/types/filter";
import courseJsonRaw from "./courses.json";
const data: CourseData = courseJsonRaw as CourseData;
export const useCourseFilters = (): UseCourseFiltersReturn => {
    const [titleInput, setTitleInput] = useState<string>("");
    const [subtitleInput, setSubtitleInput] = useState<string>("");
    const [classInput, setClassInput] = useState<number>(0);
    const [filters, setFilters] = useState<FilterOptions>({
        title: "",
        subtitle: "",
        classNumber: null,
    });

    const setTitleFilter = (title: string) => {
        setFilters((prev) => ({ ...prev, title, subtitle: "" }));
    };

    const setSubtitleFilter = (subtitle: string) => {
        setFilters((prev) => ({ ...prev, subtitle }));
    };

    const setClassFilter = (classNumber: number | null) => {
        setFilters((prev) => ({ ...prev, classNumber }));
    };

    const clearFilters = () => {
        setFilters({ title: "", subtitle: "", classNumber: null });
    };

    const availableTitles = useMemo(() => {
        return Object.keys(data);
    }, [data]);

    const availableSubtitles = useMemo(() => {
        if (!filters.title) return [];
        return data[filters.title]?.map((course) => course.subtitle) || [];
    }, [data, filters.title]);

    const availableClasses = useMemo(() => {
        const classes = new Set<number>();
        Object.values(data).forEach((courses) => {
            courses.forEach((course) => {
                course.classes.forEach((classNum) => classes.add(classNum));
            });
        });
        return Array.from(classes).sort((a, b) => a - b);
    }, [data]);

    const filteredData = useMemo(() => {
        let result: CourseData = {};

        Object.entries(data).forEach(([title, courses]) => {
            if (
                filters.title &&
                !title.toLowerCase().includes(filters.title.toLowerCase())
            ) {
                return;
            }
            const filteredCourses = courses.filter((course) => {
                if (
                    filters.subtitle &&
                    !course.subtitle
                        .toLowerCase()
                        .includes(filters.subtitle.toLowerCase())
                ) {
                    return false;
                }
                if (
                    filters.classNumber !== null &&
                    !course.classes.includes(filters.classNumber)
                ) {
                    return false;
                }
                return true;
            });

            if (filteredCourses.length > 0) {
                result[title] = filteredCourses;
            }
        });

        return result;
    }, [data, filters]);

    const handleTitleChange = (value: string) => {
        setTitleInput(value);
        setTitleFilter(value);
        // Clear subsequent filters when title changes
        setSubtitleInput("");
        setClassInput(0);
        setSubtitleFilter("");
        setClassFilter(null);
    };

    const handleSubtitleChange = (value: string) => {
        setSubtitleInput(value);
        setSubtitleFilter(value);
        // Clear class filter when subtitle changes
        setClassInput(0);
        setClassFilter(null);
    };

    const handleClassChange = (value: number) => {
        setClassInput(value);
        const classNum = value;
        setClassFilter(classNum);
    };

    const handleClearFilters = () => {
        setTitleInput("");
        setSubtitleInput("");
        setClassInput(0);
        clearFilters();
    };

    // Get first result from filtered data
    const getFirstResult = () => {
        const titles = Object.keys(filteredData);
        if (titles.length === 0) return null;

        const firstTitle = titles[0];
        const firstCourse = filteredData[firstTitle][0];

        return {
            title: firstTitle,
            course: firstCourse,
        };
    };
    return {
        availableClasses,
        availableSubtitles,
        availableTitles,
        classInput,
        filters,
        getFirstResult,
        handleClassChange,
        handleClearFilters,
        handleSubtitleChange,
        handleTitleChange,
        subtitleInput,
        titleInput,
    };
};
