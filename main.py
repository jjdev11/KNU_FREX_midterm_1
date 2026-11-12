import csv
import matplotlib.pyplot as plt

import streamlit as st

class Pupil:
    total_pupils = 0
    total_boys = 0
    total_girls = 0

    def __init__(self, surname: str, name: str, patronymic: str, birthyear: int, sex: str, average_mark: float):
        Pupil.total_pupils += 1
        
        self.surname = surname
        self.name = name
        self.patronymic = patronymic
        
        self.birthyear = birthyear
        self.sex = sex
        if sex == "Ч":
            Pupil.total_boys += 1
        else:
            Pupil.total_girls += 1

        # Інкапсулюємо значення середньої оцінки, щоб буцімто не можна було "підправити" оцінку
        self._average_mark = average_mark

class Classroom:
    num_of_classrooms = 0
    # Список наявних паралелей та вертикалей для подальшої ітерації в розрахунках
    parallels = []
    verticals = []

    def __init__(self, parallel: int, vertical: str):
        Classroom.num_of_classrooms += 1

        # Інкапсулюємо значення паралелі, бо переходом між класами займається окремий метод
        self._parallel = parallel
        self.vertical = vertical
        # Додаємо паралель та вертикаль до списку існуючих
        if parallel not in Classroom.parallels:
            Classroom.parallels.append(parallel)
        if vertical not in Classroom.verticals:
            Classroom.verticals.append(vertical)
        # Інкапсулюємо список однокласників, бо він mutable
        self._classmates = []

    @property
    def parallel(self):
        return self._parallel

    @property
    def classmates(self) -> list:
        return self.classmates.copy()

    def add_pupil(self, pupil: Pupil) -> None:
        self._classmates.append(pupil)

    def get_num_of_pupils(self):
        return len(self._classmates)

def main():
    # Кнопка головної сторінки для перемикання між сценаріями
    if st.button("Головна сторінка", type="tertiary", icon="🏠", width="content"):
        st.write("Перехід до головної сторінки")

    # Зчитуємо дані та зберігаємо у вигляді списку з словниками
    with open("data/school.csv", "r", encoding="utf-8") as f:
        pupils_data = list(csv.DictReader(f))

    # Завдяки отриманим даним створюємо об'єкти учнів та їх класів
    pupils = {}
    classrooms = {}
    for data in pupils_data:
        pupil_id = data["id"]
        class_name = data["Клас"]

        # Створюємо об'єкт учня...
        pupil = Pupil(
            surname=data["Прізвище"],
            name=data["Ім'я"],
            patronymic=data["По-батькові"],
            birthyear=data["Рік народження"],
            sex=data["Стать"],
            average_mark=data["Середній бал"]
        )
        # та додаємо його до списку учнів
        pupils[pupil_id] = pupil
        
        # Якщо клас вже існує, то його створення не продублюється
        if class_name not in classrooms:
            parallel, vertical = class_name.split("-")
            classrooms[class_name] = Classroom(parallel, vertical)

        # Додаємо учня до списку однокласників
        classrooms[class_name].add_pupil(pupil)

    # Створюємо розділи статистики учнів та списку учнів для зручності
    tab_statistics, tab_table_pupils = st.tabs(["Статистика учнів","Таблиця учнів"])

    # Розділ статистики учнів
    with tab_statistics:
        st.header("Статистика учнів")
        st.divider()

        st.write(f"Загальна кількість учнів у школі: {Pupil.total_pupils}")

        # Завдяки атрибутам класу Pupil рахуємо відсоткове співвідношення хлопців та дівчат
        boy_percentage = round(Pupil.total_boys / Pupil.total_pupils, 1) * 100
        girl_percentage = 100-boy_percentage
        st.write(f"Відсоткове співвідношення хлопців/дівчат в класах: {boy_percentage}% / {girl_percentage}%")

        # Завдяки атрибутам класів рахуємо середню кіл-ть учнів в класах
        average_num_of_pupils = round(Pupil.total_pupils / Classroom.num_of_classrooms, 1)
        st.write(f"Середня кількість учнів в класі: {average_num_of_pupils}")

        # Завдяки dict comprehension отримуємо словник, де ключ це клас, а його елемент це його кіл-ть учнів
        classes_num_of_pupils = {name: classroom.get_num_of_pupils() for name, classroom in classrooms.items()}
        # Шукаємо максимальну кількість учнів в класі, знаючи, що кількість учнів є другим елементом кортежу
        class_name_max, max_num_of_pupils = max(classes_num_of_pupils.items(), key=lambda x: x[1])
        st.write(f"Максимальна кількість учнів: {max_num_of_pupils} (в класі {class_name_max})")

        # Аналогічно шукаємо мінімальну кількість учнів...
        class_name_min, min_num_of_pupils = min(classes_num_of_pupils.items(), key=lambda x: x[1])
        st.write(f"Мінімальна кількість учнів: {min_num_of_pupils} (в класі {class_name_min})")

        # Переходимо до графіків
        st.divider()

        # Графік вертикальних стовпчиків розподілу кіл-ті учнів в паралелях
        ## Підготовка даних
        parallels_num_of_pupils = []
        for curr_parallel in Classroom.parallels:
            # list comprehensions для фільтрування кіл-ті учнів визначеної паралелі
            curr_num_of_pupils = sum([
                classroom.get_num_of_pupils() for classroom in classrooms.values()
                if classroom.parallel == curr_parallel
            ])
            parallels_num_of_pupils.append(curr_num_of_pupils)
        ## Створення Графіку
        fig, ax = plt.subplots()
        ax.bar(Classroom.parallels, parallels_num_of_pupils)
        ### Атрибути нашого графіку
        ax.set_title("Розподіл кількості учнів по паралелях")
        ax.set_xlabel("Паралелі")
        ax.set_ylabel("Кіл-ть учнів")
        ## Відображення графіку
        st.pyplot(fig)

        # Графік вертикальних стовпчиків розподілу кіл-ті учнів в вертикалях
        ## Підготовка даних (аналогічно)
        verticals_num_of_pupils = []
        for curr_vertical in Classroom.verticals:
            # list comprehensions для фільтрування кіл-ті учнів визначеної паралелі
            curr_num_of_pupils = sum([
                classroom.get_num_of_pupils() for classroom in classrooms.values()
                if classroom.vertical == curr_vertical
            ])
            verticals_num_of_pupils.append(curr_num_of_pupils)
        ## Створення Графіку
        fig, ax = plt.subplots()
        ax.bar(Classroom.verticals, verticals_num_of_pupils)
        ### Атрибути нашого графіку
        ax.set_title("Розподіл кількості учнів по вертикалях")
        ax.set_xlabel("Вертикалі")
        ax.set_ylabel("Кіл-ть учнів")
        ## Відображення графіку
        st.pyplot(fig)

    # Розділ списку учнів
    with tab_table_pupils:
        st.header("Список учнів")
        st.write("(усі дані вигадано)")
        st.divider()

        st.table(pupils_data)

if __name__ == "__main__":
    main()