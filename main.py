import csv
import matplotlib.pyplot as plt

import streamlit as st

class Pupil:

    def __init__(self, surname: str, name: str, patronymic: str, birthyear: int, sex: str, average_mark: float) -> None:
        self.surname = surname
        self.name = name
        self.patronymic = patronymic
        
        self.birthyear = birthyear
        self.sex = sex

        self._average_mark = average_mark

class Classroom:

    def __init__(self, parallel: int, vertical: str) -> None:
        self._parallel = parallel
        self.vertical = vertical
        self._classmates = []

    @property
    def classmates(self) -> list:
        return self_classmates.copy()

    def add_pupil(self, pupil: Pupil) -> None:
        self._classmates.append(pupil)


def main():
    pass

if __name__ == "__main__":
    main()