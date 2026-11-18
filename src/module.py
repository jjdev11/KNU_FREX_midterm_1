from dataclasses import dataclass, replace
from abc import ABC, abstractmethod

DIRECTOR_BASE_SALARY = 15000
TEACHER_BASE_SALARY = 12000
GUARDIAN_BASE_SALARY = 11000

# Учні та Класи

# Параметр slots забезпечує збереження даних класу компактно в оперативну пам'ять
@dataclass(slots=True)
class Student:
    s_id: str
    surname: str
    name: str
    patronymic: str
    birthyear: int
    sex: str
    average_mark: float
    class_name: str

    def promote(self) -> None:
        parallel, vertical = self.class_name.split("-")
        next_parallel = int(parallel) + 1
        self.class_name = f"{next_parallel}-{vertical}"

@dataclass(slots=True)
class Classroom:
    name: str          # Назва класу
    parallel: int      # Паралель (наприклад, 11)
    vertical: str      # Вертикаль (наприклад, "А")
    _student_ids: list[str]  # ID учнів в Класі

    @property
    def student_ids(self):
        return self._student_ids

    def promote_class(self, students: dict[str, Student]) -> dict[str, Student]:
        self.parallel += 1
        self.name = f"{self.parallel}-{self.vertical}"
        for s_id in self._student_ids:
            if self.parallel == 12:
                students.pop(s_id, None)
            else:
                students[s_id].promote()

        return students


# Працівники школи

## Коефіцієнт впливу стажу роботи працівника на його зарплатню переписано за логікою...
## (1 + стаж / кіл-ть років стажу до подвоєння зарплати без урахування досвіду управління)
@dataclass(slots=True)
class BaseEmployee(ABC):
    e_id:str
    full_name:str
    job_title:str
    work_experience:int
    management_experience:int = 0
    _salary_bonus:int = 0

    @property
    def salary_bonus(self):
        return self._salary_bonus

    # Підвищення гнучкості в подальшому, якщо буде потреба в підвищенні зарплати окремому працівнику
    @salary_bonus.setter
    def salary_bonus(self, value):
        if value < 0:
            raise ValueError("Надбавка не може бути від'ємною")
        self._salary_bonus = value

    @abstractmethod
    def get_salary(self): ...

@dataclass(slots=True)
class Director(BaseEmployee):
    def get_salary(self):
        return (
            DIRECTOR_BASE_SALARY*(1 + self.work_experience / 50)
            + self.management_experience*500 + self.salary_bonus
        )

@dataclass(slots=True)
class Teacher(BaseEmployee):
    def get_salary(self):
        return (TEACHER_BASE_SALARY*(1 + self.work_experience / 30)+ self.salary_bonus) 

@dataclass(slots=True)
class Guardian(BaseEmployee):
    def get_salary(self):
        return (GUARDIAN_BASE_SALARY + self.work_experience*250 + self.salary_bonus)

def create_employee(e_id, full_name, job_title, work_experience, management_experience) -> Director | Teacher | Guardian:
    if job_title == "Директор":
        return Director(e_id, full_name, work_experience, management_experience)
    if job_title == "Вчитель":
        return Teacher(e_id, full_name, work_experience, management_experience)
    if job_title == "Охоронець":
        return Guardian(e_id, full_name, work_experience, management_experience)
    raise ValueError(f"Невідома посада: {job_title}")