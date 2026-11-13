import csv
from dataclasses import dataclass
from pathlib import Path
from warnings import warn


# Константи подібні до першого сценарію
CSV_DATA_PATH = Path("data/employees.csv")
CSV_OUTPUT_PATH = Path("data/employees_updated.csv")
ENCODING = "utf-8"

# Константи базової ставки робітників
DIRECTOR_BASE_SALARY = 15000
TEACHER_BASE_SALARY = 12000
GUARDIAN_BASE_SALARY = 11000


# Один загальний клас для всіх робітників
# Код не буде масштабуватись, тому клас один
@dataclass(frozen=True, slots=True)
class Employee:
    id:str
    full_name:str
    job_title:str
    work_experience:int
    management_experience:int

    # Коефіцієнт впливу стажу роботи працівника на його зарплатню переписано за логікою...
    # (1 + стаж / кіл-ть років стажу до подвоєння зарплати без урахування досвіду управління)
    def get_salary(self):
        match self.job_title:
            case "Директор":
                return (
                    DIRECTOR_BASE_SALARY*(1 + self.work_experience / 50)
                    + self.management_experience*500
                )
            case "Вчитель":
                return (TEACHER_BASE_SALARY*(1 + self.work_experience / 30))
            case "Охоронець":
                return (GUARDIAN_BASE_SALARY + self.work_experience*250)
            case _:
                raise ValueError(f"Непередбачена посада: {self.job_title}")


# Завантаження даних з таблиці, в котрій треба оновити стовпчик з зарплатами
def load_employees_data() -> dict[str, Employee]:
    if not CSV_DATA_PATH.exists():
        raise FileNotFoundError(f"Файл не знайдено: {CSV_DATA_PATH}")

    employees: dict[str, Employee] = {}
    
    with CSV_DATA_PATH.open(newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                employee = Employee(
                    id=row["id"],
                    full_name=row["ПІБ"],
                    job_title=row["Посада"],
                    work_experience=int(row["Стаж роботи"]),
                    management_experience=int(row["Стаж управління"])
                )
                    
            except (KeyError, ValueError) as e:
                warn(f"Пропущено {row.get('id')}: помилка - {e}")
                continue

            employees[employee.id] = employee

    return employees

def main():
    # Завантажуємо дані з таблиці
    employees = load_employees_data()

    # Список в  форматі для таблиці
    updated_employees = []
    for employee in employees.values():
        # Перетворюємо атрибути та методи з об'єкту кожного робітника в його дані
        employee_csv_data = {
            "id":employee.id,
            "ПІБ":employee.full_name,
            "Посада":employee.job_title,
            "Стаж роботи":employee.work_experience,
            "Стаж управління":employee.management_experience,
            "Зарплата":round(employee.get_salary(), 2)
        }
        updated_employees.append(employee_csv_data)

    if not updated_employees:
        raise ValueError("Дані відсутні")
    # Назви стовпців в таблиці
    fieldnames = updated_employees[0].keys()
    with CSV_OUTPUT_PATH.open("w", newline="", encoding=ENCODING) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_employees)

    print(f"Таблицю з оновленими зарплатами записано в: \n{CSV_OUTPUT_PATH.absolute()}")

if __name__ == "__main__":
    main()
