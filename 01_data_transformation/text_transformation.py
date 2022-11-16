import re

# REMOVING CARRIAGE RETURN FROM THE TEXT
def remove_carriage_return(text, add_empty_space=True):
    if add_empty_space:
        return re.sub(pattern = '\r', repl = ' ', string = text)
    return re.sub(pattern = '\r', repl = '', string = text)


# REMOVING LINE BREAK FROM THE TEXT
def remove_line_break(text, add_empty_space=True):
    if add_empty_space:
        return re.sub(pattern = '\n', repl = ' ', string = text)
    return re.sub(pattern = '\n', repl = '', string = text)


# REMOVING HTML TAGS FROM THE TEXT
def remove_html_tags(text):
    return re.sub(re.compile('<.*?>'), '', text)


# STANDARDIZING QUOTES
def standardize_quotes(text):
    modified_text = text
    modified_text = modified_text.replace('“', '"')
    modified_text = modified_text.replace('”', '"')
    return modified_text


# REMOVING SOME SEQUENCES OF EMPTY SPACES FROM THE TEXT
def remove_empty_space_sequence(text):
    modified_text = text
    while "        " in modified_text:
        modified_text = modified_text.replace("        ", "    ")
    return modified_text


# COMBINING THE OTHER FUNCTIONS
def clear_text_data(body):
    modified_text = body
    modified_text = remove_carriage_return(modified_text)
    modified_text = remove_line_break(modified_text)
    modified_text = remove_html_tags(modified_text)
    modified_text = standardize_quotes(modified_text)
    modified_text = remove_empty_space_sequence(modified_text)

    return modified_text