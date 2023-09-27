from nostril import nonsense


def divide_into_batches(lst, batch_size):
    return [lst[i:i + batch_size] for i in range(0, len(lst), batch_size)]


def clean_non_sense_text(text):
    clean_text_list = []
    for sub_text in text.split('.'):
        try:
            if not nonsense(sub_text):
                clean_text_list.append(sub_text)
        except ValueError:
            pass

    return '. '.join(clean_text_list).replace('\n', ' ').replace('  ', ' ')
