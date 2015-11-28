import itertools

__author__ = 'akhil'

import json
import csv


def get_reference_set():
    reference_set = set()
    with open('skillset-refined.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            reference_set.add(row['name'])

    return reference_set


def main():
    reference_set = get_reference_set()

    skill_lists = []

    with open('candidate_lists.json') as file:
        candidate_lists = json.loads(file.read())

        for candidate_list in candidate_lists:
            for element in candidate_list:
                if element in reference_set:
                    skill_lists.append(candidate_list)
                break

        extracted_skills = []
        for skill_list in skill_lists:
            for skill in skill_list:
                if skill not in reference_set:
                    extracted_skills.append(skill)

        extracted_skills.sort()
        extracted_skills = list(k for k, _ in itertools.groupby(extracted_skills))
        json.dump(extracted_skills, open('extracted_skills.json', 'w'))


if __name__ == "__main__":
    main()
