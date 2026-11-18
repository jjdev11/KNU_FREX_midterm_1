import csv
import copy
from pathlib import Path

import streamlit as st
import matplotlib.pyplot as plt

from module import Student, Classroom

CSV_PATH = Path("data/school.csv")
ENCODING = "utf-8"

# Окрема функція для підвантаження даних учнів
# Кешуємо дані (хоч ми це не вчили, але це важливо), щоб не зчитувати та обробляти їх багато разів
@st.cache_data(show_spinner="Завантаження даних...")
def load_school_data() -> (dict[str, Student], dict[str, Classroom]):
    # Якщо дані не завантажились чи шлях невалідний, то явно виведеться помилка
    if not CSV_PATH.exists():
        st.error(f"Файл не знайдено: {CSV_PATH}")
        st.stop()

    # Type hints в словниках, де зберігаються об'єкти Учнів та Класів
    students: dict[str, Student] = {}
    classrooms: dict[str, Classroom] = {}
    class_student_ids: dict[str, list[str]] = {}

    # newline="" важливий для сумісності під час зчитування .csv
    # За умовчанням виставлений режим читання
    with CSV_PATH.open(newline="", encoding=ENCODING) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # При записі атрибутів об'єкту явно перевизначаємо їх тип
                # (Через keyword зручніше)
                student = Student(
                    s_id=int(row["id"]),
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
                st.warning(f"Пропущено {row.get('id')}: помилка - {e}")
                # Переходимо до наступного учня в таблиці
                continue

            students[student.id] = student
            # Створюємо пустий список для ключа, якщо він не існує, а потім додаємо туди id учня
            class_student_ids.setdefault(student.class_name, []).append(student.id)

    # Враховуючи те, що всі помилки покриті перевірками...
    # можемо записати створення Класів з учнями як dict comprehensions
    classrooms = {
        name: Classroom(
            name=name,
            # Завдяки знаку "-" в назві класу його легко поділити на паралель та вертикаль
            parallel=int(name.split("-")[0]), 
            vertical=name.split("-")[1],
            _student_ids=list(ids)
        )
        for name, ids in class_student_ids.items()
    }
    return students, classrooms

# Окрема функція для розрахунків статистичної інформації Учнів та Класів
def get_stats(students: dict[str, Student], classrooms: dict[str, Classroom]) -> dict:
    if not students:
        st.warning("Помилка: Словник Учнів порожній")
        return {}

    # Кіл-ть учнів та рахування кіл-ті хлопчиків та дівчат
    total = len(students)
    boys = sum(1 for student in students.values() if student.sex == "Ч")
    girls = total - boys

    class_sizes = {name: len(classroom.student_ids) for name, classroom in classrooms.items()}
    # max/min перебирають ключі в class_sizes і знаходить ключ з max/min кіл-тю учнів
    max_class = max(class_sizes, key=class_sizes.get)
    min_class = min(class_sizes, key=class_sizes.get)

    # Кіл-ть учнів в паралелях та вертикалях
    parallel_sizes: dict[int, int] = {}
    vertical_sizes: dict[str, int] = {}
    # c як скорочення classroom
    for c in classrooms.values():
        # .get, до речі, дозволяє безпечно добути значення за ключем в словнику
        parallel_sizes[c.parallel] = parallel_sizes.get(c.parallel, 0) + len(c.student_ids)
        vertical_sizes[c.vertical] = vertical_sizes.get(c.vertical, 0) + len(c.student_ids)

    birthyear_sizes: dict[int, int] = {}
    # p як скорочення student
    for p in students.values():
        birthyear_sizes[p.birthyear] = birthyear_sizes.get(p.birthyear, 0) + 1

    student_classes: list[str] = []
    student_average_marks: list[float] = []
    for p in students.values():
        student_classes.append(p.class_name)
        student_average_marks.append(round(p.average_mark, 2))

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
        "vertical_sizes": dict(sorted(vertical_sizes.items())),
        "birthyear_sizes": dict(sorted(birthyear_sizes.items())),
        "class_average_marks": (student_classes, student_average_marks)
    }

# Функція відображення статистики
def view_stats(stats: dict) -> None:
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

    # Лінійний графік розподілу кіл-ті учнів по року народження
    ## Створення Графіку
    fig, ax = plt.subplots()
    birthyears = stats["birthyear_sizes"].keys()
    birthyear_sizes = stats["birthyear_sizes"].values()
    ax.plot(birthyears, birthyear_sizes)
    ### Атрибути нашого графіку
    ax.set_title("Розподіл кількості учнів по року народження")
    ax.set_xlabel("Роки народження")
    ax.set_ylabel("Кіл-ть учнів")
    ## Відображення графіку
    st.pyplot(fig)
    plt.close(fig)

    # Графік залежності Scatter середньої оцінки учнів від класу
    ## Створення Графіку
    fig, ax = plt.subplots()
    classes = stats["class_average_marks"][0]
    class_average_marks = stats["class_average_marks"][1]
    # Додатково додано градієнт Червоний-Жовтий-Зелений для точок в залежності від значення середньої оцінки
    ax.scatter(classes, class_average_marks, c=class_average_marks, cmap="Greens", vmin=0, vmax=12)
    ### Атрибути нашого графіку
    ax.set_title("Розподіл кількості учнів по року народження")
    ax.set_xlabel("Клас")
    ax.set_ylabel("Середні оцінки")
    ## Написи на осі x під кутом та зменшені
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ## Відображення графіку
    st.pyplot(fig)
    plt.close(fig)
    

def main():
    if st.button("Головна сторінка", type="tertiary", icon="🏠"):
        st.session_state.page = "homepage"

    match st.session_state.page:
        # Головна сторінка
        case "homepage":
            if st.button("Статистика школи", width="stretch"):
                st.session_state.page = "statistics"
                st.rerun()
        # Сторінка Статистики школи (Сценарій №1)
        case "statistics":
            students, classrooms = load_school_data()
            

            # Створюємо розділи статистики учнів та списку учнів для зручності
            tab_statistics, tab_table_students = st.tabs(["Статистика учнів","Таблиця учнів"])

            # Розділ статистики учнів
            with tab_statistics:
                st.header("Статистика учнів")
                st.divider()

                # Отримуємо поточну статистику
                stats = get_stats(students, classrooms)
                # Відображаємо її
                view_stats(stats)

                # Здійснюємо переход кожного учня і класу на наступну паралель та зберігаємо в нові словники
                promoted_students: dict[str, Student] = copy.deepcopy(students)
                promoted_classrooms: dict[str, Classroom] = copy.deepcopy(classrooms)
                for c in promoted_classrooms.values():
                    promoted_students = c.promote_class(promoted_students)
                
                promoted_classrooms = {
                    c.name: c for c in promoted_classrooms.values()
                    if c.parallel != 12
                }
                
                if promoted_students:
                    st.divider()
                    st.header("Прогноз на наступний рік")
                    # Отримуємо статистику для наступного року
                    new_stats = get_stats(promoted_students, promoted_classrooms)
                    # Відображення нової статистики
                    view_stats(new_stats)

            # Розділ списку учнів (відображення CSV-файлу)
            with tab_table_students:
                st.header("Список учнів")
                st.write("(усі дані вигадано)")
                st.divider()

                with CSV_PATH.open(newline="", encoding=ENCODING) as f:
                    students_data = list(csv.DictReader(f))
                st.dataframe(students_data)
        # У непередбаченому випадку здійснюється перехід до Головної сторінки
        case _:
            st.session_state.page = "homepage"
            st.rerun()

if __name__ == "__main__":
    if "page" not in st.session_state:
        st.session_state.page = "homepage"
    main()