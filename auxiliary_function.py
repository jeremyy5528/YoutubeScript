from logger import logger
def chunk_string_by_words(string, length):
    # Calculate the percentage of spaces
    space_percentage = string.count(" ") / len(string)

    # Calculate the uniformity of spaces
    space_positions = [i for i, char in enumerate(string) if char == " "]
    space_differences = [
        j - i for i, j in zip(space_positions[:-1], space_positions[1:])
    ]
    uniformity = (
        max(space_differences) - min(space_differences) if space_differences else 0
    )

    # If more than 5% of the characters are spaces and the spaces are relatively uniform, split by words
    if space_percentage > 0.05 and uniformity <= length:
        chunks = [string[i : i + length] for i in range(0, len(string), length)]
        logger.info(f'chunk len 1:{len(chunks)}')
    else:
        words = string.split()
        chunks = [
            " ".join(words[i : i + length]) for i in range(0, len(words), length)
        ]
        logger.info(f'chunk len 2:{len(chunks)}')

    return chunks