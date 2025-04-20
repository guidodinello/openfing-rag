import { ReactElement, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

export const Course = (): ReactElement => {
  const { acronym } = useParams<{ acronym: string }>();
  // You can fetch the course name based on the acronym if needed
  // For now, just use acronym
  const [indexes, setIndexes] = useState<number[]>([]);

  useEffect(() => {
    if (!acronym) return;
    fetch(`/src/demo_data/ScrapInfo/${acronym}.json`)
      .then((response) => response.json())
      .then((data) => setIndexes(data))
      .catch((error) => {
        console.error("Error fetching data:", error);
      });
  }, [acronym]);

  return (
    <div>
      <h1>Course Page</h1>
      <p>This is the course page for {acronym}.</p>
      {indexes.map((index) => (
        <div key={index}>
          <h2>Index {index}</h2>
          <p>Details about index {index}...</p>
        </div>
      ))}
    </div>
  );
};
