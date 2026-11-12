import csv
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
import matplotlib.pyplot as plt


CSV_PATH = Path("data/school.csv")
ENCODING = "utf-8"

# Параметри frozen та slots забезпечують те, що дані завантажились лише раз і компактно в оперативну пам'ять
@dataclass(frozen=True, slots=True)
class Pupil:
    id: str
    surname: str
    name: str
    patronymic: str
    birthyear: int
    sex: str
    average_mark: float
    class_name: str

@dataclass(frozen=True, slots=True)
class Classroom:
    name: str          # Назва класу
    parallel: int      # Паралель (наприклад, 11)
    vertical: str      # Вертикаль (наприклад, "А")
    pupil_ids: tuple[str, ...]  # ID учнів в Класі

# Окрема функція для підвантаження даних учнів
# Кешуємо дані (хоч ми це не вчили, але це важливо), щоб не зчитувати та обробляти їх багато разів
@st.cache_data(show_spinner="Завантаження даних...")
def load_school_data() -> (dict[str, Pupil], dict[str, Classroom]):
    # Якщо дані не завантажились чи шлях невалідний, то явно виведеться помилка
    if not CSV_PATH.exists():
        st.error("Файл не знайдено: {CSV_PATH}")
        st.stop()

    # Type hints в словниках, де зберігаються об'єкти Учнів та Класів
    pupils: dict[str, Pupil] = {}
    classrooms: dict[str, Classroom] = {}
    class_pupil_ids: dict[str, list[str]] = {}

    # newline="" важливий для сумісності під час зчитування .csv
    with CSV_PATH.open(newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # При записі атрибутів об'єкту явно перевизначаємо їх тип
                # (Через keyword зручніше)
                pupil = Pupil(
                    id=row["id"],
                    surname=row["Прізвище"],
                    name=row["Ім'я"],
                    patronymic=row["По-батькові"],
                    birthyear=int(row["Рік народження"]),
                    sex=row["Стать"],
                    average_mark=float(row["Середній бал"]),
                    class_name=row["Клас"]
                )
            # Щоб довго не возитись з помилками через записи в таблиці
            # ...передбачаємо їх явно і відображаємо в Streamlit
            except (KeyError, ValueError) as e:
                st.warning(f"Пропущено {row.get("id")}: помилка - {e}")
                # Переходимо до наступного учня в таблиці
                continue

            pupils[pupil.id] = pupil
            # Створюємо пустий список для ключа, якщо він не існує, а потім додаємо туди id учня
            class_pupil_ids.setdefault(pupil.class_name, []).append(pupil.id)

    # Враховуючи те, що всі помилки покриті перевірками...
    # можемо записати створення Класів з учнями як dict comprehensions
    classrooms = {
        name: Classroom(
            name=name,
            # Завдяки знаку "-" в назві класу його легко поділити на паралель та вертикаль
            parallel=int(name.split("-")[0]), 
            vertical=name.split("-")[1],
            pupil_ids=tuple(ids)
        )
        for name, ids in class_pupil_ids.items()
    }
    return pupils, classrooms

# Окрема функція для розрахунків статистичної інформації Учнів та Класів
def get_stats(pupils: dict[str, Pupil], classrooms: dict[str, Classroom]) -> dict:
    if not pupils:
        st.warning("Помилка: Отримано порожні дані з таблиці")
        return {}

    # Кіл-ть учнів та рахування кіл-ті хлопчиків та дівчат
    total = len(pupils)
    boys = sum(1 for pupil in pupils.values() if pupil.sex == "Ч")
    girls = total - boys

    class_sizes = {name: len(classroom.pupil_ids) for name, classroom in classrooms.items()}
    # max/min перебирають ключі в class_sizes і знаходить ключ з max/min кіл-тю учнів
    max_class = max(class_sizes, key=class_sizes.get)
    min_class = min(class_sizes, key=class_sizes.get)

    # Кіл-ть учнів в паралелях та вертикалях
    parallel_sizes: dict[int, int] = {}
    vertical_sizes: dict[str, int] = {}
    # c як скорочення classroom
    for c in classrooms.values():
        # .get, до речі, дозволяє безпечно добути значення за ключем в словнику
        parallel_sizes[c.parallel] = parallel_sizes.get(c.parallel, 0) + len(c.pupil_ids)
        vertical_sizes[c.vertical] = vertical_sizes.get(c.vertical, 0) + len(c.pupil_ids)

    # Повертаємо зручний словник значень в статистиці
    return {
        "total": total,
        "boys_pct": round(boys / total * 100, 1),
        "girls_pct": round(girls / total * 100, 1),
        "avg_class_size": round(total / len(classrooms), 1),
        "class_sizes": class_sizes,
        "max_class": (class_sizes[max_class], max_class),
        "min_class": (class_sizes[min_class], min_class),
        # Сортуємо ключі для правильного порядку відображення на графіку
        "parallel_sizes": dict(sorted(parallel_sizes.items())),
        "vertical_sizes": dict(sorted(vertical_sizes.items()))
    }

def main():
    # WIP Кнопка головної сторінки для перемикання між сценаріями 
    if st.button("Головна сторінка", type="tertiary", icon="🏠", width="content"):
        st.warning("🚧 WIP")

    # Тут також буде розділення на Сценарії завдяки кнопкам

    pupils, classrooms = load_school_data()
    stats = get_stats(pupils, classrooms)

    # Створюємо розділи статистики учнів та списку учнів для зручності
    tab_statistics, tab_table_pupils = st.tabs(["Статистика учнів","Таблиця учнів"])

    # Розділ статистики учнів
    with tab_statistics:
        st.header("Статистика учнів")
        st.divider()

        # Відображення кіл-ті учнів та їх відсоткового співвідношення за статю в дві колонки
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Загальна кількість учнів у школі: {stats["total"]}")
        with col2:
            st.write(f"Cпіввідношення хлопців/дівчат: {stats["boys_pct"]}% / {stats["girls_pct"]}%")
        
        st.write(f"Середня кіл-ть учнів в класах: {stats["avg_class_size"]}")

        max_size, max_class_name = stats["max_class"]
        st.write(f"Максимальна кількість учнів: {max_size} (в класі {max_class_name})")

        min_size, min_class_name = stats["min_class"]
        st.write(f"Мінімальна кількість учнів: {min_size} (в класі {min_class_name})")

        # Переходимо до графіків
        st.divider()

        # Графік вертикальних стовпчиків розподілу кіл-ті учнів в паралелях
        ## Створення Графіку
        fig, ax = plt.subplots()
        parallel_names = stats["parallel_sizes"].keys()
        parallel_sizes = stats["parallel_sizes"].values()
        ax.bar(parallel_names, parallel_sizes)
        ### Атрибути нашого графіку
        ax.set_title("Розподіл кількості учнів по паралелях")
        ax.set_xlabel("Паралелі")
        ax.set_ylabel("Кіл-ть учнів")
        ## Відображення графіку
        st.pyplot(fig)
        plt.close(fig)



        # Графік вертикальних стовпчиків розподілу кіл-ті учнів в вертикалях
        ## Створення Графіку
        fig, ax = plt.subplots()
        vertical_names = stats["vertical_sizes"].keys()
        vertical_sizes = stats["vertical_sizes"].values()
        ax.bar(vertical_names, vertical_sizes)
        ### Атрибути нашого графіку
        ax.set_title("Розподіл кількості учнів по вертикалях")
        ax.set_xlabel("Вертикалі")
        ax.set_ylabel("Кіл-ть учнів")
        ## Відображення графіку
        st.pyplot(fig)
        plt.close(fig)


    # Розділ списку учнів (відображення CSV-файлу)
    with tab_table_pupils:
        st.header("Список учнів")
        st.write("(усі дані вигадано)")
        st.divider()

        with CSV_PATH.open(newline="", encoding=ENCODING) as f:
            pupils_data = list(csv.DictReader(f))
        st.table(pupils_data)

if __name__ == "__main__":
    main()