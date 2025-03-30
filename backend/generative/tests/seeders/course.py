# app/database/seeders/course.py
from app.models import Course
from tests.factories import CourseFactory
from tests.seeders import BaseSeeder


class CourseSeeder(BaseSeeder):
    async def run(self):
        courses = [
            {
                "code": "actint",
                "name": "Actividad Introductoria",
                "course_metadata": {
                    "semester": 1,
                    "credits": 5,
                    "department": "General Engineering",
                    "description": "Curso introductorio para estudiantes de ingeniería que proporciona una visión general de la carrera y desarrolla habilidades básicas necesarias para el éxito académico.",
                },
            },
            {
                "code": "agpi",
                "name": "Administración General para Ingenieros",
                "course_metadata": {
                    "semester": 8,
                    "credits": 8,
                    "department": "Management",
                    "description": "Fundamentos de administración y gestión empresarial orientados a la práctica ingenieril, incluyendo planificación, organización, dirección y control de proyectos.",
                },
            },
            {
                "code": "comp1",
                "name": "Computación 1",
                "course_metadata": {
                    "semester": 2,
                    "credits": 12,
                    "department": "Computer Science",
                    "description": "Conceptos fundamentales de la computación, arquitectura de computadoras, sistemas operativos y programación básica.",
                },
            },
            {
                "code": "metn-2023",
                "name": "Métodos Numéricos",
                "course_metadata": {
                    "semester": 4,
                    "credits": 12,
                    "department": "Mathematics",
                    "description": "Estudio de métodos numéricos para resolución de problemas matemáticos, incluyendo análisis de error, solución de ecuaciones, interpolación y métodos numéricos para ecuaciones diferenciales.",
                },
            },
            {
                "code": "pln",
                "name": "Procesamiento de Lenguaje Natural",
                "course_metadata": {
                    "semester": 7,
                    "credits": 10,
                    "department": "Computer Science",
                    "description": "Fundamentos y aplicaciones del procesamiento del lenguaje natural, incluyendo análisis sintáctico, semántico, modelos de lenguaje y aplicaciones prácticas.",
                },
            },
        ]

        for course_data in courses:
            course = Course(**course_data)
            self.db.add(course)

        await self.db.flush()
        return courses

    async def run_random(self):
        factory = CourseFactory(db=self.db)
        await factory.create_batch(50)
