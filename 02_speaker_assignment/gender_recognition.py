import json

def load_names(filename):
    file = open(filename, "r")
    file_json = json.loads(file.read())
    file.close()
    return file_json


def assign_gender_to_speakers(speaker_assignment, name_list):
    for assignment in speaker_assignment:
        speaker = assignment["speaker"]
        if "undefined" not in speaker:
            first_letter = speaker["entity_first_name"][0]
            if first_letter in name_list:    
                for name_and_gender in name_list[first_letter]:
                    name, gender = name_and_gender
                    # IF THE ENTITY NAME IS FOUND
                    # IN THE LIST OF COMMON BRAZILIAN NAMES
                    if speaker["entity_first_name"] == name:
                        speaker["gender"] = gender
                # IF THE ENTITY NAME IS NOT FOUND IN THE LIST
                if "gender" not in speaker:
                    speaker["gender"] = "undefined"
            else:
                speaker["gender"] = "undefined"

    return speaker_assignment