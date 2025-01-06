def create_button(key, text):
    if len(key) > 30:
        key = key[:30]
        text = text[:30]
    return {'key': key, 'text': text}
