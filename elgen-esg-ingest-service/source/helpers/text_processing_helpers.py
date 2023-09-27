from typing import List

import nltk

nltk.download('punkt')


def chunk_text_nltk(text: str, chunk_size: int = 250, overlap: int = 50, ignore_token_length: int = 30) -> List[str]:
    """Chunk text in to a list following this strategy:
    - split using double \n as it usually signifies a new paragraph
    - if the paragraph is less than the specified ignore_token_length parameter then we won't consider it
    - if the paragraph is more than the specified chunk_size then truncate it into sub-paragraphs with overlap"""
    chunks = []
    for paragraph in text.split("\n\n"):
        paragraph_tokens = nltk.word_tokenize(paragraph)
        if len(paragraph_tokens) < ignore_token_length:
            continue
        elif len(paragraph_tokens) > chunk_size:
            chunks.extend(
                " ".join(paragraph_tokens[i: i + chunk_size])
                for i in range(0, len(paragraph_tokens), chunk_size - overlap)
            )
        else:
            chunks.append(paragraph)

    return chunks
