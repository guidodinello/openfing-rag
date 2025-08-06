import _courses from "../hooks/filters/courses.json";
import _subCourses from "../hooks/filters/subCourses.json";
import _classes from "../hooks/filters/classes.json";
import { useCallback, useState } from "react";
import { DropDownList } from "./ui/dropDownList";

const courses = _courses as string[];
const subCourses = _subCourses as Record<string, string[]>;
const classes = _classes as Record<
    string,
    Record<string, { acronym: string; classes: number[] }>
>;

export const FilterOptions = () => {
    const [course, setCourse] = useState<string>("");
    const [subCourse, setSubCourse] = useState<string>("");
    const [selectedClass, setSelectedClass] = useState<number>(0); // Changed from 'class' to avoid keyword conflict
    const [subCourseOptions, setSubCourseOptions] = useState<string[]>([]);
    const [classOptions, setClassOptions] = useState<number[]>([]);

    const onSelectCourse = useCallback((course: string) => {
        setCourse(course.toString());
        setSubCourse("");
        setSelectedClass(0);
        setSubCourseOptions(subCourses[course] || []);
    }, []);

    const onSelectSubCourse = useCallback((subCourse: string) => {
        setSubCourse(subCourse.toString());
        setSelectedClass(0);
        if (course && subCourse) {
            const classData = classes[course]?.[subCourse];
            setClassOptions(classData?.classes || []);
        }
    }, []);

    const onSelectClass = useCallback((cls: number) => {
        setSelectedClass(parseInt(cls.toString(), 10));
    }, []);

    return (
        <div>
            <DropDownList
                options={courses}
                onSelect={onSelectCourse}
                selectedValue={course}
                disabled={false}
            />
            <DropDownList
                options={subCourseOptions}
                onSelect={onSelectSubCourse}
                selectedValue={subCourse}
                disabled={course !== ""}
            />
            <DropDownList
                options={classOptions}
                onSelect={onSelectClass}
                selectedValue={selectedClass}
                disabled={subCourse !== ""}
            />
        </div>
    );
};
