import React, { useState } from "react";
import { useCourseFilters } from "../hooks/use-course-filters";

export const FilterButton = () => {
    const {
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
    } = useCourseFilters();
    const firstResult = getFirstResult();
    return (
        <div className="p-4 space-y-4">
            <div className="space-y-3">
                <div>
                    <label className="block text-sm font-medium mb-1">
                        Filter by Title:
                    </label>
                    <input
                        type="text"
                        value={titleInput}
                        onChange={(e) => handleTitleChange(e.target.value)}
                        placeholder="Enter title..."
                        className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {titleInput && availableTitles.length > 0 && (
                        <div className="text-sm text-gray-600 mt-1">
                            {availableTitles.length} title(s) available
                        </div>
                    )}
                </div>

                {filters.title && availableSubtitles.length > 0 && (
                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Filter by Subtitle:
                        </label>
                        <input
                            type="text"
                            value={subtitleInput}
                            onChange={(e) =>
                                handleSubtitleChange(e.target.value)
                            }
                            placeholder="Enter subtitle..."
                            className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <div className="text-sm text-gray-600 mt-1">
                            {availableSubtitles.length} subtitle(s) available
                        </div>
                    </div>
                )}

                {(filters.title || filters.subtitle) &&
                    availableClasses.length > 0 && (
                        <div>
                            <label className="block text-sm font-medium mb-1">
                                Filter by Class:
                            </label>
                            <input
                                type="number"
                                value={classInput}
                                onChange={(e) =>
                                    handleClassChange(e.target.value)
                                }
                                placeholder="Enter class number..."
                                className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <div className="text-sm text-gray-600 mt-1">
                                Available classes: {availableClasses.join(", ")}
                            </div>
                        </div>
                    )}

                <button
                    onClick={handleClearFilters}
                    className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                    Clear Filters
                </button>
            </div>

            {firstResult.title !== "" && (
                <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-3">
                        First Result:
                    </h3>

                    <div className="p-4 bg-gray-50 rounded-md border">
                        <h4 className="font-medium text-lg">
                            {firstResult.title}
                        </h4>
                        <p className="text-gray-700 mt-1">
                            <strong>Subtitle:</strong>{" "}
                            {firstResult.course.subtitle}
                        </p>
                        <p className="text-gray-700">
                            <strong>Course Key:</strong>{" "}
                            {firstResult.course.courseKey}
                        </p>
                        <p className="text-gray-700">
                            <strong>Classes:</strong>{" "}
                            {firstResult.course.classes.join(", ")}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};
